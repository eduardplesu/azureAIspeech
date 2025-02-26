import streamlit as st
import os, time
from datetime import datetime
from modules.speech_to_text import transcribe_with_diarization, detect_language_from_audio
from modules.docx_export import export_transcription_to_docx
from modules.azure_storage import upload_file_to_azure_storage
from modules.openai_analysis import analyze_transcription
from modules.text_cleaning import clean_segments_with_openai

# ---------------------------
# Helper: Clear Session State for New Upload
# ---------------------------
def clear_previous_session():
    keys_to_clear = [
        "temp_file_path",
        "detected_language",
        "transcription_results",
        "uploaded_filename",
        "analysis_result",
        "cleaned_transcription"
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

# ---------------------------
# Tab 1: Upload & Transcribe
# ---------------------------
def upload_and_transcribe():
    st.header("1. Upload & Transcribe")
    
    uploaded_file = st.file_uploader("Upload an audio file (MP3/WAV)", type=["mp3", "wav"], key="upload")
    
    if uploaded_file is not None:
        # If a different file is uploaded, clear previous state.
        if st.session_state.get("uploaded_filename") != uploaded_file.name:
            clear_previous_session()
            st.session_state.uploaded_filename = uploaded_file.name

        # Save the file temporarily if not already saved.
        if not st.session_state.get("temp_file_path"):
            temp_file_path = f"temp_{uploaded_file.name}"
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            st.session_state.temp_file_path = temp_file_path
        
        st.success(f"File '{uploaded_file.name}' uploaded successfully!")
        
        # Detect language if not done yet.
        if not st.session_state.get("detected_language"):
            with st.spinner("Detecting language..."):
                try:
                    # Prioritize Romanian first.
                    detected_language = detect_language_from_audio(
                        st.session_state.temp_file_path, possible_languages=["ro-RO", "en-US"]
                    )
                    st.session_state.detected_language = detected_language
                except Exception as e:
                    st.error(f"Language detection failed: {e}")
                    st.session_state.detected_language = "en-US"  # Fallback.
        st.success(f"Detected language: {st.session_state.detected_language}")
        
        # Allow user to override detected language.
        language_options = ["ro-RO", "en-US"]
        default_index = 0 if st.session_state.detected_language == "ro-RO" else 1
        language_override = st.selectbox(
            "Override detected language (if needed):",
            options=language_options,
            index=default_index,
            key="lang_override"
        )
        
        if st.button("Start Transcription", key="transcribe_button"):
            if not st.session_state.get("temp_file_path"):
                st.error("No file available for transcription. Please upload an audio file.")
                return
            with st.spinner("Transcribing..."):
                try:
                    transcription_results = transcribe_with_diarization(
                        st.session_state.temp_file_path, language=language_override
                    )
                    st.session_state.transcription_results = transcription_results
                    st.success("Transcription completed!")
                except Exception as e:
                    st.error(f"Transcription failed: {e}")
    else:
        st.info("Please upload an audio file.")

# ---------------------------
# Tab 2: Review & Edit
# ---------------------------
def review_and_edit():
    st.header("2. Review & Edit")
    
    if not st.session_state.get("temp_file_path"):
        st.warning("No audio file uploaded yet. Please complete step 1.")
        return

    # Audio playback
    st.audio(st.session_state.temp_file_path, format="audio/wav")
    
    if not st.session_state.get("transcription_results"):
        st.warning("No transcription results available. Please complete transcription first.")
        return

    st.subheader("Edit Transcription Segments")
    with st.form("edit_transcription_form"):
        edited_transcriptions = []
        
        # Create a text area for each diarized segment.
        for i, segment in enumerate(st.session_state.transcription_results):
            speaker = segment.get("speaker_id", "Unknown")
            text = segment.get("text", "")
            new_text = st.text_area(
                label=f"Segment {i+1} - Speaker {speaker}",
                value=text,
                key=f"segment_{i}"
            )
            edited_transcriptions.append({**segment, "text": new_text})

        # Two buttons side by side: Save Edits and Clean All Segments.
        col1, col2 = st.columns(2)
        with col1:
            save_edits = st.form_submit_button("Save Edits")
        with col2:
            clean_segments = st.form_submit_button("Clean All Segments")

        if save_edits:
            st.session_state.transcription_results = edited_transcriptions
            st.success("Transcription edits saved!")

        if clean_segments:
            try:
                cleaned_transcriptions = clean_segments_with_openai(edited_transcriptions)
                st.session_state.transcription_results = cleaned_transcriptions
                # Optionally, also store a combined version.
                st.session_state.cleaned_transcription = "\n".join([seg["text"] for seg in cleaned_transcriptions])
                st.success("All segments cleaned!")
            except Exception as e:
                st.error(f"Text cleaning failed: {e}")

    st.subheader("Assign Speaker Names")
    with st.form("assign_names_form"):
        speaker_names = {}
        unique_speakers = {seg.get("speaker_id", "Unknown") for seg in st.session_state.transcription_results}
        
        for speaker in unique_speakers:
            name = st.text_input(
                label=f"Name for Speaker {speaker}",
                value=f"Speaker {speaker}",
                key=f"name_{speaker}"
            )
            speaker_names[speaker] = name
        
        if st.form_submit_button("Save Speaker Names"):
            for seg in st.session_state.transcription_results:
                seg["speaker_name"] = speaker_names.get(seg.get("speaker_id", "Unknown"), "Unknown")
            st.success("Speaker names saved!")

# ---------------------------
# Tab 3: Analysis
# ---------------------------
def analysis_tab():
    st.header("3. Analysis")
    
    if not st.session_state.get("transcription_results"):
        st.warning("No transcription available for analysis. Please complete transcription and editing first.")
        return
    
    # Combine all transcription segments into one text.
    transcription_text = "\n".join([seg.get("text", "") for seg in st.session_state.transcription_results])
    
    if st.button("Analyze Transcription", key="analyze_button"):
        with st.spinner("Analyzing transcription using Azure OpenAI..."):
            try:
                analysis_result = analyze_transcription(transcription_text)
                st.session_state.analysis_result = analysis_result
                st.success("Analysis completed!")
            except Exception as e:
                st.error(f"Analysis failed: {e}")
    
    if st.session_state.get("analysis_result"):
        st.subheader("Analysis Output")
        st.text_area("Analysis", st.session_state.analysis_result, height=300)
        if st.button("Save Analysis", key="save_analysis"):
            st.success("Analysis saved!")
    else:
        st.info("Run analysis to see results.")

# ---------------------------
# Tab 4: Export & Save
# ---------------------------
def export_and_save():
    st.header("4. Export & Save")
    
    if not st.session_state.get("transcription_results"):
        st.warning("No transcription available. Please complete transcription and editing first.")
        return

    analysis_text = st.session_state.get("analysis_result", None)
    # Use the updated transcription segments (with cleaned text if available)
    final_transcription = st.session_state.transcription_results
    
    if st.button("Generate DOCX and Download", key="download_button"):
        with st.spinner("Generating DOCX..."):
            try:
                unique_suffix = datetime.now().strftime("%Y%m%d%H%M%S")
                output_filename = f"transcription_{unique_suffix}.docx"
                docx_file = export_transcription_to_docx(
                    final_transcription,
                    analysis_text=analysis_text,
                    output_filename=output_filename,
                    cleaned_transcription=st.session_state.get("cleaned_transcription")
                )
                with open(docx_file, "rb") as f:
                    st.download_button("Download DOCX", data=f.read(), file_name=docx_file)
                st.success("DOCX generated!")
            except Exception as e:
                st.error(f"Error generating DOCX: {e}")
    
    st.markdown("---")
    st.subheader("Upload Files to Azure Blob Storage")
    if st.button("Upload Audio & DOCX to Azure", key="upload_blob_button"):
        messages = []
        unique_suffix = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # Upload the audio file with a unique blob name.
        if st.session_state.get("temp_file_path"):
            try:
                audio_blob_name = f"{unique_suffix}_{os.path.basename(st.session_state.temp_file_path)}"
                audio_url = upload_file_to_azure_storage(
                    st.session_state.temp_file_path,
                    container_name="transcription",
                    blob_name=audio_blob_name
                )
                messages.append(f"Audio file uploaded to: [Link]({audio_url})")
            except Exception as e:
                messages.append(f"Audio upload failed: {e}")
        else:
            messages.append("No audio file available to upload.")
        
        # Generate DOCX file and upload it with a unique blob name.
        try:
            output_docx = export_transcription_to_docx(
                st.session_state.transcription_results,
                analysis_text=analysis_text,
                output_filename=f"{unique_suffix}_transcription.docx",
                cleaned_transcription=st.session_state.get("cleaned_transcription")
            )
            docx_blob_name = f"{unique_suffix}_transcription.docx"
            docx_url = upload_file_to_azure_storage(
                output_docx,
                container_name="transcription",
                blob_name=docx_blob_name
            )
            messages.append(f"DOCX transcription uploaded to: [Link]({docx_url})")
        except Exception as e:
            messages.append(f"DOCX upload failed: {e}")
        
        for msg in messages:
            st.write(msg)
    
    st.markdown("**Note:** In this demo, files are not automatically deleted. In a production Azure deployment, you might implement a cleanup strategy.")

# ---------------------------
# Main App with Tabs
# ---------------------------
def main():
    st.title("Azure AI Speech Transcription Demo")
    st.markdown(
        "This demo showcases Azure Speech Service with diarization, automatic language detection, cloud-based analysis using Azure OpenAI GPT-4o, "
        "and post-processing of transcriptions with OpenAI for cleaning and correction. Use the tabs below to progress through each step."
    )
    
    tabs = st.tabs(["Upload & Transcribe", "Review & Edit", "Analysis", "Export & Save"])
    with tabs[0]:
        upload_and_transcribe()
    with tabs[1]:
        review_and_edit()
    with tabs[2]:
        analysis_tab()
    with tabs[3]:
        export_and_save()

if __name__ == "__main__":
    if "transcription_results" not in st.session_state:
        st.session_state.transcription_results = None
    if "temp_file_path" not in st.session_state:
        st.session_state.temp_file_path = None
    if "detected_language" not in st.session_state:
        st.session_state.detected_language = None
    if "uploaded_filename" not in st.session_state:
        st.session_state.uploaded_filename = None
    if "analysis_result" not in st.session_state:
        st.session_state.analysis_result = None
    if "cleaned_transcription" not in st.session_state:
        st.session_state.cleaned_transcription = None
    
    main()

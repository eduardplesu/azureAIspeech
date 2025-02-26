# modules/speech_to_text.py
import os
import time
import threading
import json
import azure.cognitiveservices.speech as speechsdk
from modules.audio_utils import convert_audio_to_wav
from dotenv import load_dotenv

load_dotenv()

SPEECH_KEY = os.getenv("SPEECH_KEY")
SPEECH_REGION = os.getenv("SPEECH_REGION")
SPEECH_ENDPOINT = os.getenv("SPEECH_ENDPOINT")  # Optional custom endpoint

def create_speech_config(language: str, auto_detection: bool = False):
    """
    Creates and returns a configured SpeechConfig.
    If auto_detection is True, then the custom endpoint is not set
    because custom endpoints are unsupported in auto language detection scenarios.
    Additionally, sets the profanity option to Raw so that all words (including profanity) are returned.
    """
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    speech_config.speech_recognition_language = language
    # Set profanity to Raw (i.e., do not mask or remove profane words)
    speech_config.set_profanity(speechsdk.ProfanityOption.Raw)
    if not auto_detection and SPEECH_ENDPOINT:
        # Only set the endpoint when not using auto language detection.
        speech_config.endpoint_id = SPEECH_ENDPOINT
    return speech_config

def detect_language_from_audio(file_path: str, possible_languages=["en-US", "ro-RO"]) -> str:
    """
    Detects the language of the audio file using Azure Speech Service's auto language detection feature.
    Returns the detected language code (e.g., "en-US" or "ro-RO").
    """
    file_path = convert_audio_to_wav(file_path)

    # For auto detection, disable custom endpoint configuration.
    speech_config = create_speech_config("en-US", auto_detection=True)
    
    auto_detect_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(possible_languages)
    audio_config = speechsdk.audio.AudioConfig(filename=file_path)
    
    recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config,
        auto_detect_source_language_config=auto_detect_config
    )
    
    result = recognizer.recognize_once()
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        detected_lang_str = result.properties.get(
            speechsdk.PropertyId.SpeechServiceConnection_AutoDetectSourceLanguageResult
        )
        # Return the raw string, e.g., "en-US", "ro-RO", etc.
        if detected_lang_str:
            return detected_lang_str

    # Fallback if detection fails
    return "en-US"

def transcribe_with_diarization(file_path: str, language: str = "auto"):
    """
    Transcribes an audio file using Azure Speech Service with diarization enabled.
    If language is set to "auto", it first detects the language.
    Returns a list of dictionaries with transcription results.
    """
    file_path = convert_audio_to_wav(file_path)
    
    if language == "auto":
        detected_language = detect_language_from_audio(file_path)
        print(f"Detected language: {detected_language}")
        language = detected_language
        
    # Use full configuration (custom endpoint allowed).
    speech_config = create_speech_config(language, auto_detection=False)
    # Enable diarization intermediate results.
    speech_config.set_property(property_id=speechsdk.PropertyId.SpeechServiceResponse_DiarizeIntermediateResults, value='true')
    
    audio_config = speechsdk.audio.AudioConfig(filename=file_path)
    conversation_transcriber = speechsdk.transcription.ConversationTranscriber(speech_config=speech_config, audio_config=audio_config)
    
    transcription_results = []
    transcription_complete = threading.Event()
    
    def transcribed_callback(evt: speechsdk.SpeechRecognitionEventArgs):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            result = {
                "speaker_id": evt.result.speaker_id,
                "text": evt.result.text,
                "offset": evt.result.offset,
                "duration": evt.result.duration
            }
            transcription_results.append(result)
        elif evt.result.reason == speechsdk.ResultReason.NoMatch:
            print("No match:", evt.result.no_match_details)
    
    def transcribing_callback(evt: speechsdk.SpeechRecognitionEventArgs):
        print("Intermediate transcription:", evt.result.text)
    
    def session_stopped_callback(evt: speechsdk.SessionEventArgs):
        print("Transcription session stopped.")
        transcription_complete.set()
    
    def canceled_callback(evt: speechsdk.SessionEventArgs):
        print("Transcription canceled.")
        transcription_complete.set()
    
    conversation_transcriber.transcribed.connect(transcribed_callback)
    conversation_transcriber.transcribing.connect(transcribing_callback)
    conversation_transcriber.session_stopped.connect(session_stopped_callback)
    conversation_transcriber.canceled.connect(canceled_callback)
    
    conversation_transcriber.start_transcribing_async()
    transcription_complete.wait()  # Wait until transcription completes.
    conversation_transcriber.stop_transcribing_async()
    
    return transcription_results

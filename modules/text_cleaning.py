import os
import openai
import json
from dotenv import load_dotenv

load_dotenv()

def clean_segments_with_openai(segments: list[dict]) -> list[dict]:
    """
    Cleans multiple transcribed segments in a single API call using Azure OpenAI.
    
    Each segment should have a 'text' field. This function builds a single prompt
    that contains all segments (separated by clear delimiters) and instructs the model to return
    a JSON array of objects with a 'text' key. The cleaned text for each segment is then merged
    back into the original segments.
    
    Args:
        segments (list[dict]): List of transcription segments.
    
    Returns:
        list[dict]: The updated list of segments with cleaned text.
    """
    deployment = os.getenv("DEPLOYMENT_NAME", "gpt-4o")
    
    # Configure OpenAI for Azure OpenAI.
    openai.api_type = "azure"
    openai.api_base = os.getenv("OPENAI_ENDPOINT")
    openai.api_version = "2023-07-01-preview"
    openai.api_key = os.getenv("OPENAI_API_KEY")
    
    # Build a prompt with instructions and segments.
    user_content = (
        "Please clean the following transcribed segments. For each segment, remove extraneous characters, "
        "and correct grammatical, punctuation, and spelling errors, while preserving the original meaning. "
        "Do NOT censor or mask any words. Return the result as a JSON array of objects in the same order, "
        "with each object containing a single key 'text' for the cleaned segment. "
        "Separate each segment with '---'.\n\n"
    )
    for i, seg in enumerate(segments, start=1):
        user_content += f"Segment {i}: {seg.get('text', '')}\n---\n"
    
    prompt = [
        {
            "role": "system",
            "content": (
                "You are an AI assistant that cleans and formats transcribed text. "
                "For each segment provided, remove extraneous characters and fix grammatical, punctuation, "
                "and spelling errors while preserving the original context and meaning. "
                "Return the cleaned results as a JSON array of objects, each with a 'text' field corresponding to each segment."
            )
        },
        {
            "role": "user",
            "content": user_content
        }
    ]
    
    response = openai.ChatCompletion.create(
        engine=deployment,
        messages=prompt,
        max_tokens=3000,
        temperature=0.5,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0
    )
    
    cleaned_text_json = response.choices[0].message["content"]
    # Debug print: log the raw response from OpenAI
    print("Raw cleaning API response:", cleaned_text_json)
    
    # Strip markdown code block formatting if present.
    if cleaned_text_json.startswith("```"):
        lines = cleaned_text_json.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        cleaned_text_json = "\n".join(lines)
        print("Stripped markdown, now:", cleaned_text_json)
    
    try:
        cleaned_array = json.loads(cleaned_text_json)
        if isinstance(cleaned_array, list) and len(cleaned_array) == len(segments):
            for i, seg in enumerate(segments):
                seg["text"] = cleaned_array[i].get("text", seg.get("text", ""))
        else:
            print("Warning: Returned JSON does not match expected format or segment count.")
    except Exception as e:
        print("Error parsing JSON from cleaning API:", e)
        print("Raw response for debugging:", cleaned_text_json)
        # Fallback: do not update segments if parsing fails.
    
    return segments

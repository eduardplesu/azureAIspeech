import os
import openai
from dotenv import load_dotenv

load_dotenv()

def analyze_transcription(transcription_text: str) -> str:
    """
    Uses Azure OpenAI (e.g., GPT-4o) to analyze the transcription text.
    The analysis includes:
      - A comprehensive summary,
      - Entity extraction,
      - Sentiment analysis.
    The complete response is provided in Romanian.
    
    Parameters:
      - transcription_text: the transcription text to analyze.
      
    Returns:
      - A string with the analysis.
    """
    endpoint = os.getenv("OPENAI_ENDPOINT")
    api_key = os.getenv("OPENAI_API_KEY")
    deployment = os.getenv("DEPLOYMENT_NAME", "gpt-4o")  # e.g., "gpt-4o"
    
    # Configure OpenAI for Azure OpenAI.
    openai.api_type = "azure"
    openai.api_base = endpoint
    openai.api_version = "2025-01-01-preview"
    openai.api_key = api_key

    chat_prompt = [
        {
            "role": "system",
            "content": (
                "You are ChatGPT, a highly capable language model. You will receive as input a transcription of an audio recording "
                "which may contain text in various languages. Your task is to perform the following steps:\n\n"
                "1. Comprehensive Summary: Generate a detailed summary of the conversation.\n"
                "2. Entity Extraction: List the main entities (names, organizations, locations, etc.).\n"
                "3. Sentiment Analysis: Analyze the overall sentiment (positive, negative, or neutral).\n"
                "4. Language Requirement: Provide your complete response in Romanian.\n"
            )
        },
        {
            "role": "user",
            "content": f"The transcription is:\n\n{transcription_text}\n\nPlease provide the analysis as specified."
        }
    ]
    
    # For openai==0.28, use the 'engine' parameter:
    response = openai.ChatCompletion.create(
        engine=deployment,
        messages=chat_prompt,
        max_tokens=2000,
        temperature=0.7,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0
    )
    
    analysis_text = response.choices[0].message["content"]
    return analysis_text

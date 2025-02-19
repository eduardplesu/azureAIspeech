# Azure AI Speech Transcription Demo

This project demonstrates an end-to-end solution for speech transcription, analysis using Azure OpenAI, and exporting the results to a DOCX file. The application is built with Python and Streamlit and uses several Azure services including:

- **Azure Speech Service** for transcription and language detection.
- **Azure OpenAI** (GPT-4o) for analyzing transcriptions (providing summary, entity extraction, and sentiment analysis).
- **Azure Blob Storage** (optional) for storing audio or DOCX files.

## Features

- **File Upload & Transcription:**  
  Upload an MP3 or WAV file, automatically detect the language (with override option), and transcribe the audio using diarization.

- **Review & Edit:**  
  Review the transcription, edit the text if necessary, and assign friendly speaker names.

- **Analysis:**  
  Run Azure OpenAI analysis on the transcription to generate a detailed summary, extract key entities, and analyze sentiment (output in Romanian).

- **Export & Save:**  
  Export the transcription (and analysis, if available) to a DOCX file and optionally upload files to Azure Blob Storage.

## Requirements

- Python 3.12
- Required Python libraries (see `requirements.txt`)
- FFmpeg installed (for MP3 to WAV conversion via pydub)

## Setup

1. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   source .venv/bin/activate        # Linux/macOS
   .\.venv\Scripts\activate         # Windows
   pip install --upgrade pip
   pip install -r requirements.txt
Create a .env file at the root of the project with your configuration variables. For example:

dotenv
Copy
# Azure Speech Service credentials
SPEECH_KEY=your_speech_key
SPEECH_REGION=your_speech_region
SPEECH_ENDPOINT=https://your_speech_endpoint

# Azure OpenAI credentials
OPENAI_ENDPOINT=https://empowergovswcent.openai.azure.com/
OPENAI_API_KEY=your_openai_api_key
DEPLOYMENT_NAME=gpt-4o
DEPLOYMENT_TTS_MODEL=gpt-4o-realtime-preview

# (Optional) Azure Storage Blob
AZURE_STORAGE_CONNECTION_STRING=your_storage_connection_string
Ensure FFmpeg is installed and available in your PATH (required by pydub).

Running the App Locally
Run the Streamlit app using:

bash

streamlit run app.py
Docker Deployment
A Dockerfile is provided to build a container for the app. Build and run the container using:

bash

docker build -t my-streamlit-app .
docker run -p 8501:8501 my-streamlit-app


# modules/azure_storage.py
import os
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv

load_dotenv()

AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")

def upload_file_to_azure_storage(file_path: str, container_name: str, blob_name: str) -> str:
    """
    Uploads a file to Azure Blob Storage and returns the URL of the uploaded blob.
    """
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
    container_client = blob_service_client.get_container_client(container_name)
    
    # Create container if it doesn't exist.
    try:
        container_client.create_container()
    except Exception:
        pass  # Container likely exists.
    
    blob_client = container_client.get_blob_client(blob_name)
    with open(file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
    
    return blob_client.url

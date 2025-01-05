import urllib.parse
from azure.identity import ClientSecretCredential
from azure.storage.blob import (
    BlobServiceClient, 
    BlobClient,
    BlobProperties,
    ContainerClient
)
from azure.storage.blob import generate_blob_sas, BlobSasPermissions
from datetime import datetime, timedelta
import urllib

import os
from azure.core.paging import ItemPaged


class StorageAccount:
    def __init__(self, 
                 name: str, 
                 container_name: str) -> None:
        """_summary_

        Args:
            name (str): _description_
            container_name (str): _description_
        """
        self._name = name
        self._container_name = container_name
        self._credential = ClientSecretCredential(
            tenant_id = os.getenv("AZURE_TENANT_ID"),
            client_id = os.getenv("AZURE_CLIENT_ID"),
            client_secret= os.getenv("AZURE_CLIENT_SECRET")
        )
        self._blob_service_client = self._get_blob_service_client()
        self._container_client = self._get_container_client()
    
    def _get_blob_service_client(self) -> BlobServiceClient:
        return BlobServiceClient(
            account_url=f"https://{self._name}.blob.core.windows.net", 
            credential=self._credential
        )
        
    def _get_container_client(self) -> ContainerClient:
        return self._blob_service_client.get_container_client(self._container_name)
    
    def get_list_of_blobs(self) -> ItemPaged[BlobProperties]:
        return self._container_client.list_blobs()
    
    def get_download_blob(self, blob: BlobProperties) -> bytes:
        if blob.name.lower().endswith(".pdf"):
            print(f"PDF name: {blob.name}")
    
            blob_client = self._container_client.get_blob_client(blob.name)
            
            # Download Blob
            blob_data = blob_client.download_blob()
            # Read Blob
            return blob_data.readall()
        
    def get_file_downloadable_link(self, file_name:str):
        sas_token = generate_blob_sas(
            account_name = self._name,
            container_name = self._container_name,
            blob_name = file_name,
            permission = BlobSasPermissions(read=True),
            expiry = datetime.utcnow() + timedelta(hours=1),
            account_key = os.getenv("STORAGE_ACCOUNT_KEY")
        )
        
        file_url = f"https://{self._name}.blob.core.windows.net/{self._container_name}/{file_name}?{sas_token}"
        
        return file_url
    
    def get_file_metadata(self, metadata_name: str, blob: BlobProperties):
        blob_client = self._blob_service_client.get_blob_client(container=self._container_name, blob=blob.name)
        
        blob_properties = blob_client.get_blob_properties()
        
        metadata_value = blob_properties.metadata.get(metadata_name)
        
        return metadata_value
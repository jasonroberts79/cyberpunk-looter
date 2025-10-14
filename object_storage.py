import os
import json
import requests
from google.cloud import storage
from typing import Optional

REPLIT_SIDECAR_ENDPOINT = "http://127.0.0.1:1106"

class ReplitObjectStorage:
    """Wrapper for Replit's object storage using Google Cloud Storage"""
    
    def __init__(self):
        self.client = self._create_storage_client()
        self.bucket_name = os.getenv("STORAGE_BUCKET_NAME", "appdata")
    
    def _create_storage_client(self) -> storage.Client:
        """Create Google Cloud Storage client with Replit credentials"""
        credentials = {
            "type": "external_account",
            "audience": "replit",
            "subject_token_type": "access_token",
            "token_url": f"{REPLIT_SIDECAR_ENDPOINT}/token",
            "credential_source": {
                "url": f"{REPLIT_SIDECAR_ENDPOINT}/credential",
                "format": {
                    "type": "json",
                    "subject_token_field_name": "access_token"
                }
            },
            "universe_domain": "googleapis.com"
        }
        
        return storage.Client(
            credentials=storage.Credentials.from_dict(credentials),
            project=""
        )
    
    def save_json(self, key: str, data: dict) -> bool:
        """Save JSON data to object storage"""
        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(key)
            blob.upload_from_string(
                json.dumps(data, indent=2),
                content_type="application/json"
            )
            return True
        except Exception as e:
            print(f"Error saving to object storage: {e}")
            return False
    
    def load_json(self, key: str) -> Optional[dict]:
        """Load JSON data from object storage"""
        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(key)
            
            if not blob.exists():
                return None
            
            content = blob.download_as_text()
            return json.loads(content)
        except Exception as e:
            print(f"Error loading from object storage: {e}")
            return None
    
    def exists(self, key: str) -> bool:
        """Check if a file exists in object storage"""
        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(key)
            return blob.exists()
        except Exception as e:
            print(f"Error checking object storage: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a file from object storage"""
        try:
            bucket = self.client.bucket(self.bucket_name)
            blob = bucket.blob(key)
            blob.delete()
            return True
        except Exception as e:
            print(f"Error deleting from object storage: {e}")
            return False

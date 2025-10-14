import os
import json
import tempfile
from pathlib import Path
from replit.object_storage import Client
from typing import Optional

REPLIT_SIDECAR_ENDPOINT = "http://127.0.0.1:1106"

class ReplitObjectStorage:
    """Wrapper for Replit's object storage with fallback to local files"""
    
    def __init__(self):
        self.use_object_storage = False
        self.client = None
        self.bucket_name = os.getenv("STORAGE_BUCKET_NAME", "appdata")
        self.local_storage_dir = Path(".storage")
        self.local_storage_dir.mkdir(exist_ok=True)
        
        try:
            self.client = self._create_storage_client()
            if self.client:
                bucket = self.client.bucket(self.bucket_name)
                if bucket.exists():
                    self.use_object_storage = True
                    print(f"Using Replit Object Storage (bucket: {self.bucket_name})")
                else:
                    print(f"Object storage bucket '{self.bucket_name}' not found. Using local file storage.")
        except Exception as e:
            print(f"Object storage not available: {e}")
            print("Falling back to local file storage")
    
    def _create_storage_client(self) -> Optional[storage.Client]:
        """Create Google Cloud Storage client with Replit credentials"""
        try:
            credentials_config = {
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
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(credentials_config, f)
                config_file = f.name
            
            try:
                credentials = identity_pool.Credentials.from_file(config_file)
                return storage.Client(credentials=credentials, project="")
            finally:
                os.unlink(config_file)
        except Exception:
            return None
    
    def save_json(self, key: str, data: dict) -> bool:
        """Save JSON data to storage (object storage or local fallback)"""
        try:
            if self.use_object_storage:
                bucket = self.client.bucket(self.bucket_name)
                blob = bucket.blob(key)
                blob.upload_from_string(
                    json.dumps(data, indent=2),
                    content_type="application/json"
                )
            else:
                file_path = self.local_storage_dir / key
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with open(file_path, 'w') as f:
                    json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving to storage: {e}")
            return False
    
    def load_json(self, key: str) -> Optional[dict]:
        """Load JSON data from storage (object storage or local fallback)"""
        try:
            if self.use_object_storage:
                bucket = self.client.bucket(self.bucket_name)
                blob = bucket.blob(key)
                
                if not blob.exists():
                    return None
                
                content = blob.download_as_text()
                return json.loads(content)
            else:
                file_path = self.local_storage_dir / key
                legacy_path = Path(key)
                
                if file_path.exists():
                    with open(file_path, 'r') as f:
                        return json.load(f)
                elif legacy_path.exists():
                    print(f"Migrating legacy file {key} to .storage/ directory")
                    with open(legacy_path, 'r') as f:
                        data = json.load(f)
                    self.save_json(key, data)
                    return data
                else:
                    return None
        except Exception as e:
            print(f"Error loading from storage: {e}")
            return None
    
    def exists(self, key: str) -> bool:
        """Check if a file exists in storage (object storage or local fallback)"""
        try:
            if self.use_object_storage:
                bucket = self.client.bucket(self.bucket_name)
                blob = bucket.blob(key)
                return blob.exists()
            else:
                file_path = self.local_storage_dir / key
                return file_path.exists()
        except Exception as e:
            print(f"Error checking storage: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete a file from storage (object storage or local fallback)"""
        try:
            if self.use_object_storage:
                bucket = self.client.bucket(self.bucket_name)
                blob = bucket.blob(key)
                blob.delete()
            else:
                file_path = self.local_storage_dir / key
                if file_path.exists():
                    file_path.unlink()
            return True
        except Exception as e:
            print(f"Error deleting from storage: {e}")
            return False

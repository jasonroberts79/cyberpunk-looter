import os
from google.cloud import storage


class AppStorage:
    def __init__(self):
        """Initialize Google Cloud Storage client"""
        self.client = storage.Client()
        self.bucket_name = os.getenv("GCS_BUCKET_NAME")

        if not self.bucket_name:
            raise ValueError("GCS_BUCKET_NAME environment variable is not set")

        self.bucket = self.client.bucket(self.bucket_name)

    def writedata(self, filename, data):
        """Write data to a blob in the GCS bucket"""
        blob = self.bucket.blob(filename)
        blob.upload_from_string(data)

    def readdata(self, filename):
        """Read data from a blob in the GCS bucket"""
        blob = self.bucket.blob(filename)

        if not blob.exists():
            return None

        return blob.download_as_text()

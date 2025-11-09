"""
Google Cloud Storage implementation for application persistence.

This module provides a Storage implementation using Google Cloud Storage,
with proper error handling and type safety.
"""

from typing import Optional
from google.cloud import storage
from google.api_core import exceptions as gcp_exceptions
from exceptions import StorageError, ConfigurationError


class AppStorage:
    """
    Google Cloud Storage implementation of the Storage protocol.

    This class handles all persistence operations using GCS,
    with proper error handling and validation.
    """

    def __init__(self, bucket_name: str, client: Optional[storage.Client] = None) -> None:
        """
        Initialize Google Cloud Storage client.

        Args:
            bucket_name: The GCS bucket name to use for storage
            client: Optional GCS client (for testing/dependency injection)

        Raises:
            ConfigurationError: If bucket_name is empty or invalid
            StorageError: If unable to connect to GCS
        """
        if not bucket_name or not bucket_name.strip():
            raise ConfigurationError("Bucket name cannot be empty")

        self.bucket_name = bucket_name.strip()
        self.client = client or storage.Client()

        try:
            self.bucket = self.client.bucket(self.bucket_name)
        except Exception as e:
            raise StorageError(
                f"Failed to initialize GCS bucket '{self.bucket_name}': {e}"
            ) from e

    def write_data(self, filename: str, data: str) -> None:
        """
        Write data to a blob in the GCS bucket.

        Args:
            filename: The name of the file to write
            data: The string data to write

        Raises:
            StorageError: If write operation fails
        """
        if not filename or not filename.strip():
            raise StorageError("Filename cannot be empty")

        try:
            blob = self.bucket.blob(filename)
            blob.upload_from_string(data)
        except gcp_exceptions.GoogleAPIError as e:
            raise StorageError(
                f"Failed to write file '{filename}' to GCS: {e}"
            ) from e
        except Exception as e:
            raise StorageError(
                f"Unexpected error writing file '{filename}': {e}"
            ) from e

    def read_data(self, filename: str) -> Optional[str]:
        """
        Read data from a blob in the GCS bucket.

        Args:
            filename: The name of the file to read

        Returns:
            The file contents as a string, or None if file doesn't exist

        Raises:
            StorageError: If read operation fails (other than file not existing)
        """
        if not filename or not filename.strip():
            raise StorageError("Filename cannot be empty")

        try:
            blob = self.bucket.blob(filename)

            if not blob.exists():
                return None

            return blob.download_as_text()
        except gcp_exceptions.NotFound:
            # File not found is expected, return None
            return None
        except gcp_exceptions.GoogleAPIError as e:
            raise StorageError(
                f"Failed to read file '{filename}' from GCS: {e}"
            ) from e
        except Exception as e:
            raise StorageError(
                f"Unexpected error reading file '{filename}': {e}"
            ) from e

    # Legacy method names for backward compatibility
    def writedata(self, filename: str, data: str) -> None:
        """
        Legacy method name for write_data.

        Deprecated: Use write_data instead.
        """
        return self.write_data(filename, data)

    def readdata(self, filename: str) -> Optional[str]:
        """
        Legacy method name for read_data.

        Deprecated: Use read_data instead.
        """
        return self.read_data(filename)

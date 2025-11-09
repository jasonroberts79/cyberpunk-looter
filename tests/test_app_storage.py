"""Unit tests for AppStorage."""

from unittest.mock import Mock, patch
from src.app_storage import AppStorage


class TestAppStorageInit:
    """Test AppStorage initialization."""

    @patch("src.app_storage.storage.Client")
    def test_init_success(self, mock_client):
        """Test successful initialization with bucket name."""
        mock_bucket = Mock()
        mock_client_instance = Mock()
        mock_client_instance.bucket.return_value = mock_bucket
        mock_client.return_value = mock_client_instance

        storage = AppStorage(bucket_name="test-bucket")

        assert storage.bucket_name == "test-bucket"
        assert storage.client is not None
        assert storage.bucket is not None
        mock_client_instance.bucket.assert_called_once_with("test-bucket")

class TestAppStorageWriteData:
    """Test AppStorage writedata method."""

    @patch("src.app_storage.storage.Client")
    def test_writedata_success(self, mock_client):
        """Test successful data write."""
        mock_blob = Mock()
        mock_bucket = Mock()
        mock_bucket.blob.return_value = mock_blob
        mock_client_instance = Mock()
        mock_client_instance.bucket.return_value = mock_bucket
        mock_client.return_value = mock_client_instance

        storage = AppStorage(bucket_name="test-bucket")
        test_data = "test data content"
        storage.writedata("test_file.json", test_data)

        mock_bucket.blob.assert_called_once_with("test_file.json")
        mock_blob.upload_from_string.assert_called_once_with(test_data)

    @patch("src.app_storage.storage.Client")
    def test_writedata_with_json(self, mock_client):
        """Test writing JSON data."""
        mock_blob = Mock()
        mock_bucket = Mock()
        mock_bucket.blob.return_value = mock_blob
        mock_client_instance = Mock()
        mock_client_instance.bucket.return_value = mock_bucket
        mock_client.return_value = mock_client_instance

        storage = AppStorage(bucket_name="test-bucket")
        test_data = '{"key": "value", "number": 42}'
        storage.writedata("data.json", test_data)

        mock_bucket.blob.assert_called_once_with("data.json")
        mock_blob.upload_from_string.assert_called_once_with(test_data)


class TestAppStorageReadData:
    """Test AppStorage readdata method."""

    @patch("src.app_storage.storage.Client")    
    def test_readdata_success(self, mock_client):
        """Test successful data read."""
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        mock_blob.download_as_text.return_value = "test data content"
        mock_bucket = Mock()
        mock_bucket.blob.return_value = mock_blob
        mock_client_instance = Mock()
        mock_client_instance.bucket.return_value = mock_bucket
        mock_client.return_value = mock_client_instance

        storage = AppStorage(bucket_name="test-bucket")
        result = storage.readdata("test_file.json")

        assert result == "test data content"
        mock_bucket.blob.assert_called_once_with("test_file.json")
        mock_blob.exists.assert_called_once()
        mock_blob.download_as_text.assert_called_once()

    @patch("src.app_storage.storage.Client")
    def test_readdata_file_not_exists(self, mock_client):
        """Test reading non-existent file returns None."""
        mock_blob = Mock()
        mock_blob.exists.return_value = False
        mock_bucket = Mock()
        mock_bucket.blob.return_value = mock_blob
        mock_client_instance = Mock()
        mock_client_instance.bucket.return_value = mock_bucket
        mock_client.return_value = mock_client_instance

        storage = AppStorage(bucket_name="test-bucket")
        result = storage.readdata("nonexistent.json")

        assert result is None
        mock_bucket.blob.assert_called_once_with("nonexistent.json")
        mock_blob.exists.assert_called_once()
        mock_blob.download_as_text.assert_not_called()

    @patch("src.app_storage.storage.Client")    
    def test_readdata_json_content(self, mock_client):
        """Test reading JSON data."""
        mock_blob = Mock()
        mock_blob.exists.return_value = True
        json_data = '{"key": "value", "number": 42}'
        mock_blob.download_as_text.return_value = json_data
        mock_bucket = Mock()
        mock_bucket.blob.return_value = mock_blob
        mock_client_instance = Mock()
        mock_client_instance.bucket.return_value = mock_bucket
        mock_client.return_value = mock_client_instance

        storage = AppStorage(bucket_name="test-bucket")
        result = storage.readdata("data.json")

        assert result == json_data
        mock_bucket.blob.assert_called_once_with("data.json")
        mock_blob.download_as_text.assert_called_once()

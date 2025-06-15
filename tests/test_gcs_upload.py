#!/usr/bin/env python
#!/usr/bin/env python
#!/usr/bin/env python

"""
Unit tests for the GCSRedirectionHandler class
"""

import os
import tempfile
import unittest
from unittest import mock

from pypiserver_redirection.cdn_config_examples.gcs_upload import GCSRedirectionHandler


class TestGCSRedirectionHandler(unittest.TestCase):
    """Test the GCSRedirectionHandler class"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for packages
        self.temp_dir = tempfile.TemporaryDirectory()
        self.packages_dir = self.temp_dir.name

        # Create some test package files
        self.package_files = [
            "test-package-1.0.0.tar.gz",
            "test-package-1.0.0-py3-none-any.whl",
        ]
        for filename in self.package_files:
            with open(os.path.join(self.packages_dir, filename), "w") as f:
                f.write("dummy content")

        # Create a test cache file
        self.cache_file = os.path.join(self.temp_dir.name, "test_gcs_cache.json")

        # Mock the storage client
        self.mock_bucket = mock.MagicMock()
        self.mock_storage_client = mock.MagicMock()
        self.mock_storage_client.bucket.return_value = self.mock_bucket
        self.storage_patcher = mock.patch('google.cloud.storage.Client', return_value=self.mock_storage_client)
        self.mock_storage = self.storage_patcher.start()

        # Create the handler
        self.pypiserver_url = "http://localhost:8080"
        self.bucket_name = "test-bucket"
        self.object_prefix = "packages/"

        # The handler's initialization will call storage.Client
        self.handler = GCSRedirectionHandler(
            pypiserver_url=self.pypiserver_url,
            packages_dir=self.packages_dir,
            bucket_name=self.bucket_name,
            object_prefix=self.object_prefix,
            cache_file=self.cache_file,
            public=True
        )

    def tearDown(self):
        """Clean up test fixtures"""
        self.storage_patcher.stop()
        self.temp_dir.cleanup()

    def test_init(self):
        """Test initialization of GCSRedirectionHandler"""
        # Verify GCS-specific attributes
        self.assertEqual(self.handler.bucket_name, self.bucket_name)
        self.assertEqual(self.handler.object_prefix, self.object_prefix)
        self.assertTrue(self.handler.public)

        # Verify storage client was created correctly
        self.mock_storage.assert_called_once()
        self.mock_storage_client.bucket.assert_called_once_with(self.bucket_name)

        # Verify the CDN base URL
        expected_cdn_url = f"https://storage.googleapis.com/{self.bucket_name}/{self.object_prefix}"
        self.assertEqual(self.handler.cdn_base_url, expected_cdn_url)

    def test_upload_to_cdn(self):
        """Test uploading a package to GCS"""
        # Set up mock blob
        mock_blob = mock.MagicMock()
        self.mock_bucket.blob.return_value = mock_blob

        # Get a test package path
        filename = self.package_files[0]
        package_path = os.path.join(self.packages_dir, filename)

        # Call the method
        url = self.handler.upload_to_cdn(package_path)

        # Verify blob was created correctly
        self.mock_bucket.blob.assert_called_once_with(f"{self.object_prefix}{filename}")

        # Verify blob methods were called
        mock_blob.upload_from_filename.assert_called_once_with(package_path)
        mock_blob.make_public.assert_called_once()

        # Verify the returned URL
        expected_url = f"https://storage.googleapis.com/{self.bucket_name}/{self.object_prefix}{filename}"
        self.assertEqual(url, expected_url)

    def test_upload_to_cdn_no_public(self):
        """Test uploading a package to GCS without public access"""
        # Create a handler with public=False
        handler = GCSRedirectionHandler(
            pypiserver_url=self.pypiserver_url,
            packages_dir=self.packages_dir,
            bucket_name=self.bucket_name,
            object_prefix=self.object_prefix,
            cache_file=self.cache_file,
            public=False
        )

        # Set up mock blob
        mock_blob = mock.MagicMock()
        self.mock_bucket.blob.return_value = mock_blob

        # Get a test package path
        filename = self.package_files[0]
        package_path = os.path.join(self.packages_dir, filename)

        # Call the method
        url = handler.upload_to_cdn(package_path)

        # Verify blob was created correctly
        self.mock_bucket.blob.assert_called_once_with(f"{self.object_prefix}{filename}")

        # Verify upload was called but make_public was not
        mock_blob.upload_from_filename.assert_called_once_with(package_path)
        mock_blob.make_public.assert_not_called()

    def test_upload_to_cdn_error_handling(self):
        """Test error handling during GCS upload"""
        # Set up mock blob with error
        mock_blob = mock.MagicMock()
        mock_blob.upload_from_filename.side_effect = Exception("Upload failed")
        self.mock_bucket.blob.return_value = mock_blob

        # Get a test package path
        filename = self.package_files[0]
        package_path = os.path.join(self.packages_dir, filename)

        # Call the method and expect an exception
        with self.assertRaises(Exception):
            self.handler.upload_to_cdn(package_path)


if __name__ == "__main__":
    unittest.main()
"""
Unit tests for the GCSRedirectionHandler class
"""

import os
import tempfile
import unittest
from unittest import mock

# Set up mocks for google.cloud.storage before importing the module
import sys
sys.modules['google.cloud'] = mock.MagicMock()
sys.modules['google.cloud.storage'] = mock.MagicMock()

from pypiserver_redirection.cdn_config_examples.gcs_upload import GCSRedirectionHandler


class TestGCSRedirectionHandler(unittest.TestCase):
    """Test the GCSRedirectionHandler class"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for packages
        self.temp_dir = tempfile.TemporaryDirectory()
        self.packages_dir = self.temp_dir.name

        # Create some test package files
        self.package_files = [
            "test-package-1.0.0.tar.gz",
            "test-package-1.0.0-py3-none-any.whl",
        ]
        for filename in self.package_files:
            with open(os.path.join(self.packages_dir, filename), "w") as f:
                f.write("dummy content")

        # Create a test cache file
        self.cache_file = os.path.join(self.temp_dir.name, "test_gcs_cache.json")

        # Set up GCS mocks
        self.mock_storage_client = mock.MagicMock()
        self.mock_bucket = mock.MagicMock()
        self.mock_blob = mock.MagicMock()

        # Configure the mocks
        storage_module = sys.modules['google.cloud.storage']
        storage_module.Client.return_value = self.mock_storage_client
        self.mock_storage_client.bucket.return_value = self.mock_bucket
        self.mock_bucket.blob.return_value = self.mock_blob

        # Create the handler
        self.pypiserver_url = "http://localhost:8080"
        self.bucket_name = "test-gcs-bucket"
        self.object_prefix = "packages/"

        self.handler = GCSRedirectionHandler(
            pypiserver_url=self.pypiserver_url,
            packages_dir=self.packages_dir,
            bucket_name=self.bucket_name,
            object_prefix=self.object_prefix,
            cache_file=self.cache_file,
            public=True
        )

    def tearDown(self):
        """Clean up test fixtures"""
        self.temp_dir.cleanup()

    def test_init(self):
        """Test initialization of GCSRedirectionHandler"""
        # Verify GCS-specific attributes
        self.assertEqual(self.handler.bucket_name, self.bucket_name)
        self.assertEqual(self.handler.object_prefix, self.object_prefix)
        self.assertTrue(self.handler.public)

        # Verify GCS client was created correctly
        storage_module = sys.modules['google.cloud.storage']
        storage_module.Client.assert_called_once()
        self.mock_storage_client.bucket.assert_called_once_with(self.bucket_name)

        # Verify the CDN base URL
        expected_cdn_url = f"https://storage.googleapis.com/{self.bucket_name}/{self.object_prefix}"
        self.assertEqual(self.handler.cdn_base_url, expected_cdn_url)

    def test_upload_to_cdn(self):
        """Test uploading a package to GCS"""
        # Get a test package path
        filename = self.package_files[0]
        package_path = os.path.join(self.packages_dir, filename)

        # Call the method
        url = self.handler.upload_to_cdn(package_path)

        # Verify GCS operations were called correctly
        self.mock_bucket.blob.assert_called_once_with(f"{self.object_prefix}{filename}")
        self.mock_blob.upload_from_filename.assert_called_once_with(package_path)
        self.mock_blob.make_public.assert_called_once()

        # Verify the returned URL
        expected_url = f"https://storage.googleapis.com/{self.bucket_name}/{self.object_prefix}{filename}"
        self.assertEqual(url, expected_url)

    def test_upload_to_cdn_no_public(self):
        """Test uploading a package to GCS without making it public"""
        # Create a handler with public=False
        handler = GCSRedirectionHandler(
            pypiserver_url=self.pypiserver_url,
            packages_dir=self.packages_dir,
            bucket_name=self.bucket_name,
            object_prefix=self.object_prefix,
            cache_file=self.cache_file,
            public=False
        )

        # Reset the mocks
        self.mock_bucket.reset_mock()
        self.mock_blob.reset_mock()

        # Get a test package path
        filename = self.package_files[0]
        package_path = os.path.join(self.packages_dir, filename)

        # Call the method
        url = handler.upload_to_cdn(package_path)

        # Verify GCS operations were called correctly
        self.mock_bucket.blob.assert_called_once_with(f"{self.object_prefix}{filename}")
        self.mock_blob.upload_from_filename.assert_called_once_with(package_path)
        self.mock_blob.make_public.assert_not_called()

    def test_upload_to_cdn_error_handling(self):
        """Test error handling during GCS upload"""
        # Mock an upload error
        self.mock_blob.upload_from_filename.side_effect = Exception("GCS upload error")

        # Get a test package path
        filename = self.package_files[0]
        package_path = os.path.join(self.packages_dir, filename)

        # Call the method and expect an exception
        with self.assertRaises(Exception):
            self.handler.upload_to_cdn(package_path)

    def test_update_cache_mapping(self):
        """Test updating the cache mapping with GCS URLs"""
        # Call the update_cache_mapping method
        cache = self.handler.update_cache_mapping()

        # Verify all packages are in the cache
        self.assertEqual(len(cache), len(self.package_files))

        # Verify GCS operations were called for each package
        self.assertEqual(self.mock_bucket.blob.call_count, len(self.package_files))
        self.assertEqual(self.mock_blob.upload_from_filename.call_count, len(self.package_files))

        # Verify the URLs in the cache
        for filename in self.package_files:
            expected_url = f"https://storage.googleapis.com/{self.bucket_name}/{self.object_prefix}{filename}"
            self.assertEqual(cache[filename], expected_url)


if __name__ == "__main__":
    unittest.main()
"""
Unit tests for the GCSRedirectionHandler class
"""

import os
import tempfile
import unittest
from unittest import mock

# Add the parent directory to the path so we can import the module being tested
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create mocks for google.cloud.storage
gcs_mock = mock.MagicMock()
sys.modules['google.cloud'] = mock.MagicMock()
sys.modules['google.cloud.storage'] = gcs_mock

from cdn_config_examples.gcs_upload import GCSRedirectionHandler


class TestGCSRedirectionHandler(unittest.TestCase):
    """Test the GCSRedirectionHandler class"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for packages
        self.temp_dir = tempfile.TemporaryDirectory()
        self.packages_dir = self.temp_dir.name

        # Create some test package files
        self.package_files = [
            "test-package-1.0.0.tar.gz",
            "test-package-1.0.0-py3-none-any.whl",
        ]
        for filename in self.package_files:
            with open(os.path.join(self.packages_dir, filename), "w") as f:
                f.write("dummy content")

        # Create a test cache file
        self.cache_file = os.path.join(self.temp_dir.name, "test_gcs_cache.json")

        # Set up GCS mocks
        self.mock_storage_client = mock.MagicMock()
        self.mock_bucket = mock.MagicMock()
        self.mock_blob = mock.MagicMock()

        # Configure the mocks
        gcs_mock.Client.return_value = self.mock_storage_client
        self.mock_storage_client.bucket.return_value = self.mock_bucket
        self.mock_bucket.blob.return_value = self.mock_blob

        # Create the handler
        self.pypiserver_url = "http://localhost:8080"
        self.bucket_name = "test-gcs-bucket"
        self.object_prefix = "packages/"

        self.handler = GCSRedirectionHandler(
            pypiserver_url=self.pypiserver_url,
            packages_dir=self.packages_dir,
            bucket_name=self.bucket_name,
            object_prefix=self.object_prefix,
            cache_file=self.cache_file,
            public=True
        )

    def tearDown(self):
        """Clean up test fixtures"""
        self.temp_dir.cleanup()

    def test_init(self):
        """Test initialization of GCSRedirectionHandler"""
        # Verify GCS-specific attributes
        self.assertEqual(self.handler.bucket_name, self.bucket_name)
        self.assertEqual(self.handler.object_prefix, self.object_prefix)
        self.assertTrue(self.handler.public)

        # Verify GCS client was created correctly
        gcs_mock.Client.assert_called_once()
        self.mock_storage_client.bucket.assert_called_once_with(self.bucket_name)

        # Verify the CDN base URL
        expected_cdn_url = f"https://storage.googleapis.com/{self.bucket_name}/{self.object_prefix}"
        self.assertEqual(self.handler.cdn_base_url, expected_cdn_url)

    def test_upload_to_cdn(self):
        """Test uploading a package to GCS"""
        # Get a test package path
        filename = self.package_files[0]
        package_path = os.path.join(self.packages_dir, filename)

        # Call the method
        url = self.handler.upload_to_cdn(package_path)

        # Verify GCS operations were called correctly
        self.mock_bucket.blob.assert_called_once_with(f"{self.object_prefix}{filename}")
        self.mock_blob.upload_from_filename.assert_called_once_with(package_path)
        self.mock_blob.make_public.assert_called_once()

        # Verify the returned URL
        expected_url = f"https://storage.googleapis.com/{self.bucket_name}/{self.object_prefix}{filename}"
        self.assertEqual(url, expected_url)

    def test_upload_to_cdn_no_public(self):
        """Test uploading a package to GCS without making it public"""
        # Create a handler with public=False
        handler = GCSRedirectionHandler(
            pypiserver_url=self.pypiserver_url,
            packages_dir=self.packages_dir,
            bucket_name=self.bucket_name,
            object_prefix=self.object_prefix,
            cache_file=self.cache_file,
            public=False
        )

        # Reset the mocks
        self.mock_bucket.reset_mock()
        self.mock_blob.reset_mock()

        # Get a test package path
        filename = self.package_files[0]
        package_path = os.path.join(self.packages_dir, filename)

        # Call the method
        url = handler.upload_to_cdn(package_path)

        # Verify GCS operations were called correctly
        self.mock_bucket.blob.assert_called_once_with(f"{self.object_prefix}{filename}")
        self.mock_blob.upload_from_filename.assert_called_once_with(package_path)
        self.mock_blob.make_public.assert_not_called()

    def test_upload_to_cdn_error_handling(self):
        """Test error handling during GCS upload"""
        # Mock an upload error
        self.mock_blob.upload_from_filename.side_effect = Exception("GCS upload error")

        # Get a test package path
        filename = self.package_files[0]
        package_path = os.path.join(self.packages_dir, filename)

        # Call the method and expect an exception
        with self.assertRaises(Exception):
            self.handler.upload_to_cdn(package_path)

    def test_update_cache_mapping(self):
        """Test updating the cache mapping with GCS URLs"""
        # Call the update_cache_mapping method
        cache = self.handler.update_cache_mapping()

        # Verify all packages are in the cache
        self.assertEqual(len(cache), len(self.package_files))

        # Verify GCS operations were called for each package
        self.assertEqual(self.mock_bucket.blob.call_count, len(self.package_files))
        self.assertEqual(self.mock_blob.upload_from_filename.call_count, len(self.package_files))

        # Verify the URLs in the cache
        for filename in self.package_files:
            expected_url = f"https://storage.googleapis.com/{self.bucket_name}/{self.object_prefix}{filename}"
            self.assertEqual(cache[filename], expected_url)


if __name__ == "__main__":
    unittest.main()

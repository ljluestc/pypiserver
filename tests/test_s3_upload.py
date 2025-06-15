#!/usr/bin/env python
#!/usr/bin/env python

"""
Unit tests for the S3RedirectionHandler class
"""

import os
import tempfile
import unittest
from unittest import mock

from pypiserver_redirection.cdn_config_examples.s3_upload import S3RedirectionHandler


class TestS3RedirectionHandler(unittest.TestCase):
    """Test the S3RedirectionHandler class"""

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
        self.cache_file = os.path.join(self.temp_dir.name, "test_s3_cache.json")

        # Mock the boto3 client
        self.mock_s3_client = mock.MagicMock()
        self.boto3_patcher = mock.patch('boto3.client', return_value=self.mock_s3_client)
        self.mock_boto3 = self.boto3_patcher.start()

        # Create the handler
        self.pypiserver_url = "http://localhost:8080"
        self.bucket_name = "test-bucket"
        self.object_prefix = "packages/"
        self.region_name = "us-east-1"

        # The handler's initialization will call boto3.client
        self.handler = S3RedirectionHandler(
            pypiserver_url=self.pypiserver_url,
            packages_dir=self.packages_dir,
            bucket_name=self.bucket_name,
            object_prefix=self.object_prefix,
            region_name=self.region_name,
            cache_file=self.cache_file,
            public_read=True
        )

    def tearDown(self):
        """Clean up test fixtures"""
        self.boto3_patcher.stop()
        self.temp_dir.cleanup()

    def test_init(self):
        """Test initialization of S3RedirectionHandler"""
        # Verify S3-specific attributes
        self.assertEqual(self.handler.bucket_name, self.bucket_name)
        self.assertEqual(self.handler.object_prefix, self.object_prefix)
        self.assertEqual(self.handler.region_name, self.region_name)
        self.assertTrue(self.handler.public_read)

        # Verify boto3 client was created correctly
        self.mock_boto3.assert_called_once_with('s3', region_name=self.region_name)

        # Verify the CDN base URL
        expected_cdn_url = f"https://{self.bucket_name}.s3.amazonaws.com/{self.object_prefix}"
        self.assertEqual(self.handler.cdn_base_url, expected_cdn_url)

    def test_upload_to_cdn(self):
        """Test uploading a package to S3"""
        # Get a test package path
        filename = self.package_files[0]
        package_path = os.path.join(self.packages_dir, filename)

        # Call the method
        url = self.handler.upload_to_cdn(package_path)

        # Verify S3 client was called correctly
        self.mock_s3_client.upload_file.assert_called_once_with(
            package_path,
            self.bucket_name,
            f"{self.object_prefix}{filename}",
            ExtraArgs={'ACL': 'public-read'}
        )

        # Verify the returned URL
        expected_url = f"https://{self.bucket_name}.s3.amazonaws.com/{self.object_prefix}{filename}"
        self.assertEqual(url, expected_url)

    def test_upload_to_cdn_no_public_read(self):
        """Test uploading a package to S3 without public-read ACL"""
        # Create a handler with public_read=False
        handler = S3RedirectionHandler(
            pypiserver_url=self.pypiserver_url,
            packages_dir=self.packages_dir,
            bucket_name=self.bucket_name,
            object_prefix=self.object_prefix,
            region_name=self.region_name,
            cache_file=self.cache_file,
            public_read=False
        )

        # Reset the mock
        self.mock_s3_client.reset_mock()

        # Get a test package path
        filename = self.package_files[0]
        package_path = os.path.join(self.packages_dir, filename)

        # Call the method
        url = handler.upload_to_cdn(package_path)

        # Verify S3 client was called correctly (without ACL)
        self.mock_s3_client.upload_file.assert_called_once_with(
            package_path,
            self.bucket_name,
            f"{self.object_prefix}{filename}",
            ExtraArgs={}
        )
#!/usr/bin/env python

"""
Unit tests for the S3RedirectionHandler class
"""

import os
import tempfile
import unittest
from unittest import mock

from pypiserver_redirection.cdn_config_examples.s3_upload import S3RedirectionHandler


class TestS3RedirectionHandler(unittest.TestCase):
    """Test the S3RedirectionHandler class"""

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
        self.cache_file = os.path.join(self.temp_dir.name, "test_s3_cache.json")

        # Mock the boto3 client
        self.mock_s3_client = mock.MagicMock()
        self.boto3_patcher = mock.patch('boto3.client', return_value=self.mock_s3_client)
        self.mock_boto3 = self.boto3_patcher.start()

        # Create the handler
        self.pypiserver_url = "http://localhost:8080"
        self.bucket_name = "test-bucket"
        self.object_prefix = "packages/"
        self.region_name = "us-east-1"

        # The handler's initialization will call boto3.client
        self.handler = S3RedirectionHandler(
            pypiserver_url=self.pypiserver_url,
            packages_dir=self.packages_dir,
            bucket_name=self.bucket_name,
            object_prefix=self.object_prefix,
            region_name=self.region_name,
            cache_file=self.cache_file,
            public_read=True
        )

    def tearDown(self):
        """Clean up test fixtures"""
        self.boto3_patcher.stop()
        self.temp_dir.cleanup()

    def test_init(self):
        """Test initialization of S3RedirectionHandler"""
        # Verify S3-specific attributes
        self.assertEqual(self.handler.bucket_name, self.bucket_name)
        self.assertEqual(self.handler.object_prefix, self.object_prefix)
        self.assertEqual(self.handler.region_name, self.region_name)
        self.assertTrue(self.handler.public_read)

        # Verify boto3 client was created correctly
        self.mock_boto3.assert_called_once_with('s3', region_name=self.region_name)

        # Verify the CDN base URL
        expected_cdn_url = f"https://{self.bucket_name}.s3.amazonaws.com/{self.object_prefix}"
        self.assertEqual(self.handler.cdn_base_url, expected_cdn_url)

    def test_upload_to_cdn(self):
        """Test uploading a package to S3"""
        # Get a test package path
        filename = self.package_files[0]
        package_path = os.path.join(self.packages_dir, filename)

        # Call the method
        url = self.handler.upload_to_cdn(package_path)

        # Verify S3 client was called correctly
        self.mock_s3_client.upload_file.assert_called_once_with(
            package_path,
            self.bucket_name,
            f"{self.object_prefix}{filename}",
            ExtraArgs={'ACL': 'public-read'}
        )

        # Verify the returned URL
        expected_url = f"https://{self.bucket_name}.s3.amazonaws.com/{self.object_prefix}{filename}"
        self.assertEqual(url, expected_url)

    def test_upload_to_cdn_no_public_read(self):
        """Test uploading a package to S3 without public-read ACL"""
        # Create a handler with public_read=False
        handler = S3RedirectionHandler(
            pypiserver_url=self.pypiserver_url,
            packages_dir=self.packages_dir,
            bucket_name=self.bucket_name,
            object_prefix=self.object_prefix,
            region_name=self.region_name,
            cache_file=self.cache_file,
            public_read=False
        )

        # Reset the mock
        self.mock_s3_client.reset_mock()

        # Get a test package path
        filename = self.package_files[0]
        package_path = os.path.join(self.packages_dir, filename)

        # Call the method
        url = handler.upload_to_cdn(package_path)

        # Verify S3 client was called correctly (without ACL)
        self.mock_s3_client.upload_file.assert_called_once_with(
            package_path,
            self.bucket_name,
            f"{self.object_prefix}{filename}",
            ExtraArgs={}
        )

    def test_upload_to_cdn_error_handling(self):
        """Test error handling during S3 upload"""
        # Mock an S3 error
        from botocore.exceptions import ClientError
        error_response = {"Error": {"Code": "NoSuchBucket", "Message": "The bucket does not exist"}}
        self.mock_s3_client.upload_file.side_effect = ClientError(error_response, "upload_file")

        # Get a test package path
        filename = self.package_files[0]
        package_path = os.path.join(self.packages_dir, filename)

        # Call the method and expect an exception
        with self.assertRaises(ClientError):
            self.handler.upload_to_cdn(package_path)


if __name__ == "__main__":
    unittest.main()
    def test_upload_to_cdn_error_handling(self):
        """Test error handling during S3 upload"""
        # Mock an S3 error
        from botocore.exceptions import ClientError
        error_response = {"Error": {"Code": "NoSuchBucket", "Message": "The bucket does not exist"}}
        self.mock_s3_client.upload_file.side_effect = ClientError(error_response, "upload_file")

        # Get a test package path
        filename = self.package_files[0]
        package_path = os.path.join(self.packages_dir, filename)

        # Call the method and expect an exception
        with self.assertRaises(ClientError):
            self.handler.upload_to_cdn(package_path)

    def test_update_cache_mapping(self):
        """Test updating the cache mapping with S3 URLs"""
        # Call the update_cache_mapping method
        cache = self.handler.update_cache_mapping()

        # Verify all packages are in the cache
        self.assertEqual(len(cache), len(self.package_files))

        # Verify S3 client was called for each package
        self.assertEqual(self.mock_s3_client.upload_file.call_count, len(self.package_files))

        # Verify the URLs in the cache
        for filename in self.package_files:
            expected_url = f"https://{self.bucket_name}.s3.amazonaws.com/{self.object_prefix}{filename}"
            self.assertEqual(cache[filename], expected_url)


if __name__ == "__main__":
    unittest.main()
"""
Unit tests for the S3RedirectionHandler class
"""

import os
import tempfile
import unittest
from unittest import mock

# Add the parent directory to the path so we can import the module being tested
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cdn_config_examples.s3_upload import S3RedirectionHandler


class TestS3RedirectionHandler(unittest.TestCase):
    """Test the S3RedirectionHandler class"""

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
        self.cache_file = os.path.join(self.temp_dir.name, "test_s3_cache.json")

        # Mock the boto3 client
        self.mock_s3_client = mock.MagicMock()
        self.boto3_patcher = mock.patch('boto3.client', return_value=self.mock_s3_client)
        self.mock_boto3 = self.boto3_patcher.start()

        # Create the handler
        self.pypiserver_url = "http://localhost:8080"
        self.bucket_name = "test-bucket"
        self.object_prefix = "packages/"
        self.region_name = "us-east-1"

        # The handler's initialization will call boto3.client
        self.handler = S3RedirectionHandler(
            pypiserver_url=self.pypiserver_url,
            packages_dir=self.packages_dir,
            bucket_name=self.bucket_name,
            object_prefix=self.object_prefix,
            region_name=self.region_name,
            cache_file=self.cache_file,
            public_read=True
        )

    def tearDown(self):
        """Clean up test fixtures"""
        self.boto3_patcher.stop()
        self.temp_dir.cleanup()

    def test_init(self):
        """Test initialization of S3RedirectionHandler"""
        # Verify S3-specific attributes
        self.assertEqual(self.handler.bucket_name, self.bucket_name)
        self.assertEqual(self.handler.object_prefix, self.object_prefix)
        self.assertEqual(self.handler.region_name, self.region_name)
        self.assertTrue(self.handler.public_read)

        # Verify boto3 client was created correctly
        self.mock_boto3.assert_called_once_with('s3', region_name=self.region_name)

        # Verify the CDN base URL
        expected_cdn_url = f"https://{self.bucket_name}.s3.amazonaws.com/{self.object_prefix}"
        self.assertEqual(self.handler.cdn_base_url, expected_cdn_url)

    def test_upload_to_cdn(self):
        """Test uploading a package to S3"""
        # Get a test package path
        filename = self.package_files[0]
        package_path = os.path.join(self.packages_dir, filename)

        # Call the method
        url = self.handler.upload_to_cdn(package_path)

        # Verify S3 client was called correctly
        self.mock_s3_client.upload_file.assert_called_once_with(
            package_path,
            self.bucket_name,
            f"{self.object_prefix}{filename}",
            ExtraArgs={'ACL': 'public-read'}
        )

        # Verify the returned URL
        expected_url = f"https://{self.bucket_name}.s3.amazonaws.com/{self.object_prefix}{filename}"
        self.assertEqual(url, expected_url)

    def test_upload_to_cdn_no_public_read(self):
        """Test uploading a package to S3 without public-read ACL"""
        # Create a handler with public_read=False
        handler = S3RedirectionHandler(
            pypiserver_url=self.pypiserver_url,
            packages_dir=self.packages_dir,
            bucket_name=self.bucket_name,
            object_prefix=self.object_prefix,
            region_name=self.region_name,
            cache_file=self.cache_file,
            public_read=False
        )

        # Reset the mock
        self.mock_s3_client.reset_mock()

        # Get a test package path
        filename = self.package_files[0]
        package_path = os.path.join(self.packages_dir, filename)

        # Call the method
        url = handler.upload_to_cdn(package_path)

        # Verify S3 client was called correctly (without ACL)
        self.mock_s3_client.upload_file.assert_called_once_with(
            package_path,
            self.bucket_name,
            f"{self.object_prefix}{filename}",
            ExtraArgs={}
        )

    def test_upload_to_cdn_error_handling(self):
        """Test error handling during S3 upload"""
        # Mock an S3 error
        from botocore.exceptions import ClientError
        error_response = {"Error": {"Code": "NoSuchBucket", "Message": "The bucket does not exist"}}
        self.mock_s3_client.upload_file.side_effect = ClientError(error_response, "upload_file")

        # Get a test package path
        filename = self.package_files[0]
        package_path = os.path.join(self.packages_dir, filename)

        # Call the method and expect an exception
        with self.assertRaises(ClientError):
            self.handler.upload_to_cdn(package_path)

    def test_update_cache_mapping(self):
        """Test updating the cache mapping with S3 URLs"""
        # Call the update_cache_mapping method
        cache = self.handler.update_cache_mapping()

        # Verify all packages are in the cache
        self.assertEqual(len(cache), len(self.package_files))

        # Verify S3 client was called for each package
        self.assertEqual(self.mock_s3_client.upload_file.call_count, len(self.package_files))

        # Verify the URLs in the cache
        for filename in self.package_files:
            expected_url = f"https://{self.bucket_name}.s3.amazonaws.com/{self.object_prefix}{filename}"
            self.assertEqual(cache[filename], expected_url)


if __name__ == "__main__":
    unittest.main()

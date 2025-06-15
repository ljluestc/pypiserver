#!/usr/bin/env python
#!/usr/bin/env python
#!/usr/bin/env python

"""
Tests for the RedirectionHandler class.
"""

import os
import json
import tempfile
import unittest
from unittest import mock

from pypiserver_redirection import RedirectionHandler


class TestRedirectionHandler(unittest.TestCase):
    """Test the RedirectionHandler class."""

    def setUp(self):
        """Set up test fixtures."""
        self.pypiserver_url = "http://localhost:8080"
        self.cdn_base_url = "https://example-cdn.com/packages/"

        # Create a temporary directory for packages
        self.temp_dir = tempfile.TemporaryDirectory()
        self.packages_dir = self.temp_dir.name

        # Create a temporary cache file
        self.cache_file = os.path.join(self.temp_dir.name, "cache.json")

        # Create the handler
        self.handler = RedirectionHandler(
            pypiserver_url=self.pypiserver_url,
            packages_dir=self.packages_dir,
            cdn_base_url=self.cdn_base_url,
            cache_file=self.cache_file
        )

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_initialization(self):
        """Test that the handler initializes correctly."""
        self.assertEqual(self.handler.pypiserver_url, self.pypiserver_url)
        self.assertEqual(self.handler.packages_dir, self.packages_dir)
        self.assertEqual(self.handler.cdn_base_url, self.cdn_base_url)
        self.assertEqual(self.handler.cache_file, self.cache_file)
        self.assertEqual(self.handler.cache_mapping, {})

    def test_upload_to_cdn(self):
        """Test the upload_to_cdn method."""
        package_path = os.path.join(self.packages_dir, "test-package-1.0.0.whl")
        # Create an empty file
        with open(package_path, "w") as f:
            f.write("")

        # Test the method
        url = self.handler.upload_to_cdn(package_path)
        self.assertEqual(url, f"{self.cdn_base_url}test-package-1.0.0.whl")

    def test_update_cache_mapping(self):
        """Test the update_cache_mapping method."""
        # Create some test package files
        packages = ["test-1.0.0.whl", "test-2.0.0.tar.gz"]
        for pkg in packages:
            with open(os.path.join(self.packages_dir, pkg), "w") as f:
                f.write("")

        # Mock the upload_to_cdn method
        with mock.patch.object(self.handler, "upload_to_cdn") as mock_upload:
            mock_upload.side_effect = lambda p: f"{self.cdn_base_url}{os.path.basename(p)}"

            # Update the cache
            cache = self.handler.update_cache_mapping()

            # Check that the cache was updated correctly
            self.assertEqual(len(cache), 2)
            for pkg in packages:
                self.assertIn(pkg, cache)
                self.assertEqual(cache[pkg], f"{self.cdn_base_url}{pkg}")

            # Check that the cache file was created
            self.assertTrue(os.path.exists(self.cache_file))
            with open(self.cache_file, "r") as f:
                file_cache = json.load(f)
            self.assertEqual(file_cache, cache)

    def test_get_pypiserver_url_with_cache(self):
        """Test the get_pypiserver_url_with_cache method."""
        # Add some items to the cache
        self.handler.cache_mapping = {
            "test-1.0.0.whl": f"{self.cdn_base_url}test-1.0.0.whl",
            "test-2.0.0.tar.gz": f"{self.cdn_base_url}test-2.0.0.tar.gz"
        }

        # Test with default endpoint
        url = self.handler.get_pypiserver_url_with_cache()
        self.assertTrue(url.startswith(f"{self.pypiserver_url}/simple/?cached_links="))

        # Test with packages endpoint
        url = self.handler.get_pypiserver_url_with_cache("packages")
        self.assertTrue(url.startswith(f"{self.pypiserver_url}/packages/?cached_links="))


if __name__ == "__main__":
    unittest.main()
"""
Unit tests for the redirect_handler module
"""

import json
import os
import tempfile
import unittest
from unittest import mock
from urllib.parse import quote, unquote

from pypiserver_redirection.redirect_handler import RedirectionHandler


class TestRedirectionHandler(unittest.TestCase):
    """Test the RedirectionHandler class"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for packages
        self.temp_dir = tempfile.TemporaryDirectory()
        self.packages_dir = self.temp_dir.name

        # Create some test package files
        self.package_files = [
            "test-package-1.0.0.tar.gz",
            "test-package-1.0.0-py3-none-any.whl",
            "another-package-2.1.0.zip",
        ]
        for filename in self.package_files:
            with open(os.path.join(self.packages_dir, filename), "w") as f:
                f.write("dummy content")

        # Create a test cache file
        self.cache_file = os.path.join(self.temp_dir.name, "test_cache.json")

        # Create the handler
        self.pypiserver_url = "http://localhost:8080"
        self.cdn_base_url = "https://example-cdn.com/packages/"
        self.handler = RedirectionHandler(
            pypiserver_url=self.pypiserver_url,
            packages_dir=self.packages_dir,
            cdn_base_url=self.cdn_base_url,
            cache_file=self.cache_file
        )

    def tearDown(self):
        """Clean up test fixtures"""
        self.temp_dir.cleanup()

    def test_init(self):
        """Test initialization of RedirectionHandler"""
        self.assertEqual(self.handler.pypiserver_url, self.pypiserver_url)
        self.assertEqual(self.handler.packages_dir, os.path.abspath(self.packages_dir))
        self.assertEqual(self.handler.cdn_base_url, self.cdn_base_url)
        self.assertEqual(self.handler.cache_file, self.cache_file)
        self.assertEqual(self.handler.cache_mapping, {})

    def test_init_with_trailing_slashes(self):
        """Test initialization with trailing slashes"""
        handler = RedirectionHandler(
            pypiserver_url=self.pypiserver_url + "/",
            packages_dir=self.packages_dir,
            cdn_base_url=self.cdn_base_url + "/",
            cache_file=self.cache_file
        )
        self.assertEqual(handler.pypiserver_url, self.pypiserver_url)
        self.assertEqual(handler.cdn_base_url, self.cdn_base_url + "/")

    def test_scan_packages(self):
        """Test scanning packages directory"""
        packages = self.handler.scan_packages()
        self.assertEqual(len(packages), len(self.package_files))

        # Verify all expected files are found
        package_basenames = [os.path.basename(p) for p in packages]
        for filename in self.package_files:
            self.assertIn(filename, package_basenames)

    def test_upload_to_cdn(self):
        """Test the upload_to_cdn method"""
        # Get a test package path
        package_path = os.path.join(self.packages_dir, self.package_files[0])

        # Mock time.sleep to avoid delay
        with mock.patch('time.sleep'):
            # Call the method
            url = self.handler.upload_to_cdn(package_path)

        # Verify the URL
        expected_url = f"{self.cdn_base_url}{self.package_files[0]}"
        self.assertEqual(url, expected_url)

    def test_update_cache_mapping(self):
        """Test updating the cache mapping"""
        # Mock upload_to_cdn to avoid actual uploads
        self.handler.upload_to_cdn = mock.MagicMock(
            side_effect=lambda path: f"{self.cdn_base_url}{os.path.basename(path)}"
        )

        # Update the cache mapping
        cache = self.handler.update_cache_mapping()

        # Verify all packages are in the cache
        self.assertEqual(len(cache), len(self.package_files))
        for filename in self.package_files:
            self.assertIn(filename, cache)
            self.assertEqual(cache[filename], f"{self.cdn_base_url}{filename}")

        # Verify upload_to_cdn was called for each package
        self.assertEqual(self.handler.upload_to_cdn.call_count, len(self.package_files))

    def test_save_and_load_cache(self):
        """Test saving and loading the cache"""
        # Create a test cache mapping
        test_cache = {}
        for filename in self.package_files:
            test_cache[filename] = f"{self.cdn_base_url}{filename}"

        # Set the cache mapping and save it
        self.handler.cache_mapping = test_cache.copy()
        self.handler.save_cache()

        # Verify the cache file exists
        self.assertTrue(os.path.exists(self.cache_file))

        # Create a new handler and load the cache
        new_handler = RedirectionHandler(
            pypiserver_url=self.pypiserver_url,
            packages_dir=self.packages_dir,
            cdn_base_url=self.cdn_base_url,
            cache_file=self.cache_file
        )

        # Verify the loaded cache matches the original
        self.assertEqual(new_handler.cache_mapping, test_cache)

    def test_load_cache_invalid_json(self):
        """Test loading cache with invalid JSON"""
        # Create an invalid cache file
        with open(self.cache_file, "w") as f:
            f.write("invalid json")

        # Load the cache
        cache = self.handler.load_cache()

        # Verify an empty cache is returned
        self.assertEqual(cache, {})

    def test_update_cache_mapping_with_existing_cache(self):
        """Test updating with an existing cache"""
        # Create an initial cache with only one package
        initial_cache = {self.package_files[0]: f"{self.cdn_base_url}{self.package_files[0]}"}
        self.handler.cache_mapping = initial_cache.copy()
        self.handler.save_cache()

        # Create a new handler that will load this cache
        handler = RedirectionHandler(
            pypiserver_url=self.pypiserver_url,
            packages_dir=self.packages_dir,
            cdn_base_url=self.cdn_base_url,
            cache_file=self.cache_file
        )

        # Mock upload_to_cdn
        handler.upload_to_cdn = mock.MagicMock(
            side_effect=lambda path: f"{self.cdn_base_url}{os.path.basename(path)}"
        )

        # Update the cache mapping without forcing
        cache = handler.update_cache_mapping(force_update=False)

        # Verify all packages are now in the cache
        self.assertEqual(len(cache), len(self.package_files))

        # Verify upload_to_cdn was only called for the new packages (2)
        self.assertEqual(handler.upload_to_cdn.call_count, len(self.package_files) - 1)

    def test_update_cache_mapping_with_force(self):
        """Test force updating the cache"""
        # Create an initial cache with only one package
        initial_cache = {self.package_files[0]: f"{self.cdn_base_url}{self.package_files[0]}"}
        self.handler.cache_mapping = initial_cache.copy()
        self.handler.save_cache()

        # Create a new handler that will load this cache
        handler = RedirectionHandler(
            pypiserver_url=self.pypiserver_url,
            packages_dir=self.packages_dir,
            cdn_base_url=self.cdn_base_url,
            cache_file=self.cache_file
        )

        # Mock upload_to_cdn
        handler.upload_to_cdn = mock.MagicMock(
            side_effect=lambda path: f"{self.cdn_base_url}{os.path.basename(path)}"
        )

        # Update the cache mapping WITH forcing
        cache = handler.update_cache_mapping(force_update=True)

        # Verify all packages are now in the cache
        self.assertEqual(len(cache), len(self.package_files))

        # Verify upload_to_cdn was called for ALL packages
        self.assertEqual(handler.upload_to_cdn.call_count, len(self.package_files))

    def test_get_encoded_cache(self):
        """Test encoding the cache for URL inclusion"""
        # Create a test cache mapping
        test_cache = {}
        for filename in self.package_files:
            test_cache[filename] = f"{self.cdn_base_url}{filename}"

        # Set the cache mapping
        self.handler.cache_mapping = test_cache

        # Get the encoded cache
        encoded = self.handler.get_encoded_cache()

        # Verify it's a URL-encoded JSON string
        decoded = json.loads(unquote(encoded))
        self.assertEqual(decoded, test_cache)

    def test_get_pypiserver_url_with_cache(self):
        """Test generating PyPIServer URLs with cache"""
        # Create a test cache mapping
        test_cache = {self.package_files[0]: f"{self.cdn_base_url}{self.package_files[0]}"}
        self.handler.cache_mapping = test_cache

        # Get URLs for different endpoints
        simple_url = self.handler.get_pypiserver_url_with_cache("simple")
        packages_url = self.handler.get_pypiserver_url_with_cache("packages")

        # Verify the URLs
        encoded_cache = self.handler.get_encoded_cache()
        self.assertEqual(simple_url, f"{self.pypiserver_url}/simple/?cached_links={encoded_cache}")
        self.assertEqual(packages_url, f"{self.pypiserver_url}/packages/?cached_links={encoded_cache}")

    @mock.patch('requests.get')
    def test_verify_redirection_success(self, mock_get):
        """Test redirection verification - success case"""
        # Create a test cache mapping
        test_cache = {self.package_files[0]: f"{self.cdn_base_url}{self.package_files[0]}"}
        self.handler.cache_mapping = test_cache

        # Mock a successful response
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Call the method
        result = self.handler.verify_redirection()
#!/usr/bin/env python
"""
Tests for the RedirectionHandler class.
"""

import os
import json
import tempfile
import unittest
from unittest import mock

from pypiserver_redirection import RedirectionHandler


class TestRedirectionHandler(unittest.TestCase):
    """Test the RedirectionHandler class."""

    def setUp(self):
        """Set up test fixtures."""
        self.pypiserver_url = "http://localhost:8080"
        self.cdn_base_url = "https://example-cdn.com/packages/"

        # Create a temporary directory for packages
        self.temp_dir = tempfile.TemporaryDirectory()
        self.packages_dir = self.temp_dir.name

        # Create a temporary cache file
        self.cache_file = os.path.join(self.temp_dir.name, "cache.json")

        # Create the handler
        self.handler = RedirectionHandler(
            pypiserver_url=self.pypiserver_url,
            packages_dir=self.packages_dir,
            cdn_base_url=self.cdn_base_url,
            cache_file=self.cache_file
        )

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_initialization(self):
        """Test that the handler initializes correctly."""
        self.assertEqual(self.handler.pypiserver_url, self.pypiserver_url)
        self.assertEqual(self.handler.packages_dir, self.packages_dir)
        self.assertEqual(self.handler.cdn_base_url, self.cdn_base_url + "/")
        self.assertEqual(self.handler.cache_file, self.cache_file)
        self.assertEqual(self.handler.cache_mapping, {})

    def test_upload_to_cdn(self):
        """Test the upload_to_cdn method."""
        package_path = os.path.join(self.packages_dir, "test-package-1.0.0.whl")
        # Create an empty file
        with open(package_path, "w") as f:
            f.write("")

        # Test the method
        url = self.handler.upload_to_cdn(package_path)
        self.assertEqual(url, f"{self.cdn_base_url}/test-package-1.0.0.whl")

    def test_update_cache_mapping(self):
        """Test the update_cache_mapping method."""
        # Create some test package files
        packages = ["test-1.0.0.whl", "test-2.0.0.tar.gz"]
        for pkg in packages:
            with open(os.path.join(self.packages_dir, pkg), "w") as f:
                f.write("")

        # Mock the upload_to_cdn method
        with mock.patch.object(self.handler, "upload_to_cdn") as mock_upload:
            mock_upload.side_effect = lambda p: f"{self.cdn_base_url}/{os.path.basename(p)}"

            # Update the cache
            cache = self.handler.update_cache_mapping()

            # Check that the cache was updated correctly
            self.assertEqual(len(cache), 2)
            for pkg in packages:
                self.assertIn(pkg, cache)
                self.assertEqual(cache[pkg], f"{self.cdn_base_url}/{pkg}")

            # Check that the cache file was created
            self.assertTrue(os.path.exists(self.cache_file))
            with open(self.cache_file, "r") as f:
                file_cache = json.load(f)
            self.assertEqual(file_cache, cache)

    def test_get_pypiserver_url_with_cache(self):
        """Test the get_pypiserver_url_with_cache method."""
        # Add some items to the cache
        self.handler.cache_mapping = {
            "test-1.0.0.whl": f"{self.cdn_base_url}/test-1.0.0.whl",
            "test-2.0.0.tar.gz": f"{self.cdn_base_url}/test-2.0.0.tar.gz"
        }

        # Test with default endpoint
        url = self.handler.get_pypiserver_url_with_cache()
        self.assertTrue(url.startswith(f"{self.pypiserver_url}/simple/?cached_links="))

        # Test with packages endpoint
        url = self.handler.get_pypiserver_url_with_cache("packages")
        self.assertTrue(url.startswith(f"{self.pypiserver_url}/packages/?cached_links="))


if __name__ == "__main__":
    unittest.main()
        # Verify the result
        self.assertTrue(result)
        mock_get.assert_called_once()

    @mock.patch('requests.get')
    def test_verify_redirection_failure(self, mock_get):
        """Test redirection verification - failure case"""
        # Create a test cache mapping
        test_cache = {self.package_files[0]: f"{self.cdn_base_url}{self.package_files[0]}"}
        self.handler.cache_mapping = test_cache

        # Mock a failed response
        mock_response = mock.MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Call the method
        result = self.handler.verify_redirection()

        # Verify the result
        self.assertFalse(result)
        mock_get.assert_called_once()

    @mock.patch('requests.get')
    def test_verify_redirection_exception(self, mock_get):
        """Test redirection verification - exception case"""
        # Create a test cache mapping
        test_cache = {self.package_files[0]: f"{self.cdn_base_url}{self.package_files[0]}"}
        self.handler.cache_mapping = test_cache

        # Mock an exception
        mock_get.side_effect = requests.RequestException("Test exception")

        # Call the method
        result = self.handler.verify_redirection()

        # Verify the result
        self.assertFalse(result)
        mock_get.assert_called_once()


if __name__ == "__main__":
    unittest.main()
"""
Unit tests for the redirect_handler module
"""

import json
import os
import tempfile
import unittest
from unittest import mock
from urllib.parse import quote, unquote

# Add the parent directory to the path so we can import the module being tested
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redirect_handler import RedirectionHandler


class TestRedirectionHandler(unittest.TestCase):
    """Test the RedirectionHandler class"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for packages
        self.temp_dir = tempfile.TemporaryDirectory()
        self.packages_dir = self.temp_dir.name

        # Create some test package files
        self.package_files = [
            "test-package-1.0.0.tar.gz",
            "test-package-1.0.0-py3-none-any.whl",
            "another-package-2.1.0.zip",
        ]
        for filename in self.package_files:
            with open(os.path.join(self.packages_dir, filename), "w") as f:
                f.write("dummy content")

        # Create a test cache file
        self.cache_file = os.path.join(self.temp_dir.name, "test_cache.json")

        # Create the handler
        self.pypiserver_url = "http://localhost:8080"
        self.cdn_base_url = "https://example-cdn.com/packages/"
        self.handler = RedirectionHandler(
            pypiserver_url=self.pypiserver_url,
            packages_dir=self.packages_dir,
            cdn_base_url=self.cdn_base_url,
            cache_file=self.cache_file
        )

    def tearDown(self):
        """Clean up test fixtures"""
        self.temp_dir.cleanup()

    def test_init(self):
        """Test initialization of RedirectionHandler"""
        self.assertEqual(self.handler.pypiserver_url, self.pypiserver_url)
        self.assertEqual(self.handler.packages_dir, self.packages_dir)
        self.assertEqual(self.handler.cdn_base_url, self.cdn_base_url)
        self.assertEqual(self.handler.cache_file, self.cache_file)
        self.assertEqual(self.handler.cache_mapping, {})

    def test_scan_packages(self):
        """Test scanning packages directory"""
        packages = self.handler.scan_packages()
        self.assertEqual(len(packages), len(self.package_files))

        # Verify all expected files are found
        package_basenames = [os.path.basename(p) for p in packages]
        for filename in self.package_files:
            self.assertIn(filename, package_basenames)

    def test_upload_to_cdn(self):
        """Test the upload_to_cdn method"""
        # Get a test package path
        package_path = os.path.join(self.packages_dir, self.package_files[0])

        # Call the method
        url = self.handler.upload_to_cdn(package_path)

        # Verify the URL
        expected_url = f"{self.cdn_base_url}{self.package_files[0]}"
        self.assertEqual(url, expected_url)

    def test_update_cache_mapping(self):
        """Test updating the cache mapping"""
        # Mock upload_to_cdn to avoid actual uploads
        self.handler.upload_to_cdn = mock.MagicMock(
            side_effect=lambda path: f"{self.cdn_base_url}{os.path.basename(path)}"
        )

        # Update the cache mapping
        cache = self.handler.update_cache_mapping()

        # Verify all packages are in the cache
        self.assertEqual(len(cache), len(self.package_files))
        for filename in self.package_files:
            self.assertIn(filename, cache)
            self.assertEqual(cache[filename], f"{self.cdn_base_url}{filename}")

        # Verify upload_to_cdn was called for each package
        self.assertEqual(self.handler.upload_to_cdn.call_count, len(self.package_files))

    def test_save_and_load_cache(self):
        """Test saving and loading the cache"""
        # Create a test cache mapping
        test_cache = {}
        for filename in self.package_files:
            test_cache[filename] = f"{self.cdn_base_url}{filename}"

        # Set the cache mapping and save it
        self.handler.cache_mapping = test_cache.copy()
        self.handler.save_cache()

        # Verify the cache file exists
        self.assertTrue(os.path.exists(self.cache_file))

        # Create a new handler and load the cache
        new_handler = RedirectionHandler(
            pypiserver_url=self.pypiserver_url,
            packages_dir=self.packages_dir,
            cdn_base_url=self.cdn_base_url,
            cache_file=self.cache_file
        )

        # Verify the loaded cache matches the original
        self.assertEqual(new_handler.cache_mapping, test_cache)

    def test_update_cache_mapping_with_existing_cache(self):
        """Test updating with an existing cache"""
        # Create an initial cache with only one package
        initial_cache = {self.package_files[0]: f"{self.cdn_base_url}{self.package_files[0]}"}
        self.handler.cache_mapping = initial_cache.copy()
        self.handler.save_cache()

        # Create a new handler that will load this cache
        handler = RedirectionHandler(
            pypiserver_url=self.pypiserver_url,
            packages_dir=self.packages_dir,
            cdn_base_url=self.cdn_base_url,
            cache_file=self.cache_file
        )

        # Mock upload_to_cdn
        handler.upload_to_cdn = mock.MagicMock(
            side_effect=lambda path: f"{self.cdn_base_url}{os.path.basename(path)}"
        )

        # Update the cache mapping without forcing
        cache = handler.update_cache_mapping(force_update=False)

        # Verify all packages are now in the cache
        self.assertEqual(len(cache), len(self.package_files))

        # Verify upload_to_cdn was only called for the new packages (2)
        self.assertEqual(handler.upload_to_cdn.call_count, len(self.package_files) - 1)

    def test_update_cache_mapping_with_force(self):
        """Test force updating the cache"""
        # Create an initial cache with only one package
        initial_cache = {self.package_files[0]: f"{self.cdn_base_url}{self.package_files[0]}"}
        self.handler.cache_mapping = initial_cache.copy()
        self.handler.save_cache()

        # Create a new handler that will load this cache
        handler = RedirectionHandler(
            pypiserver_url=self.pypiserver_url,
            packages_dir=self.packages_dir,
            cdn_base_url=self.cdn_base_url,
            cache_file=self.cache_file
        )

        # Mock upload_to_cdn
        handler.upload_to_cdn = mock.MagicMock(
            side_effect=lambda path: f"{self.cdn_base_url}{os.path.basename(path)}"
        )

        # Update the cache mapping WITH forcing
        cache = handler.update_cache_mapping(force_update=True)

        # Verify all packages are now in the cache
        self.assertEqual(len(cache), len(self.package_files))

        # Verify upload_to_cdn was called for ALL packages
        self.assertEqual(handler.upload_to_cdn.call_count, len(self.package_files))

    def test_get_encoded_cache(self):
        """Test encoding the cache for URL inclusion"""
        # Create a test cache mapping
        test_cache = {}
        for filename in self.package_files:
            test_cache[filename] = f"{self.cdn_base_url}{filename}"

        # Set the cache mapping
        self.handler.cache_mapping = test_cache

        # Get the encoded cache
        encoded = self.handler.get_encoded_cache()

        # Verify it's a URL-encoded JSON string
        decoded = json.loads(unquote(encoded))
        self.assertEqual(decoded, test_cache)

    def test_get_pypiserver_url_with_cache(self):
        """Test generating PyPIServer URLs with cache"""
        # Create a test cache mapping
        test_cache = {self.package_files[0]: f"{self.cdn_base_url}{self.package_files[0]}"}
        self.handler.cache_mapping = test_cache

        # Get URLs for different endpoints
        simple_url = self.handler.get_pypiserver_url_with_cache("simple")
        packages_url = self.handler.get_pypiserver_url_with_cache("packages")

        # Verify the URLs
        encoded_cache = self.handler.get_encoded_cache()
        self.assertEqual(simple_url, f"{self.pypiserver_url}/simple/?cached_links={encoded_cache}")
        self.assertEqual(packages_url, f"{self.pypiserver_url}/packages/?cached_links={encoded_cache}")

    @mock.patch('requests.get')
    def test_verify_redirection_success(self, mock_get):
        """Test redirection verification - success case"""
        # Create a test cache mapping
        test_cache = {self.package_files[0]: f"{self.cdn_base_url}{self.package_files[0]}"}
        self.handler.cache_mapping = test_cache

        # Mock a successful response
        mock_response = mock.MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Call the method
        result = self.handler.verify_redirection()

        # Verify the result
        self.assertTrue(result)
        mock_get.assert_called_once()

    @mock.patch('requests.get')
    def test_verify_redirection_failure(self, mock_get):
        """Test redirection verification - failure case"""
        # Create a test cache mapping
        test_cache = {self.package_files[0]: f"{self.cdn_base_url}{self.package_files[0]}"}
        self.handler.cache_mapping = test_cache

        # Mock a failed response
        mock_response = mock.MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        # Call the method
        result = self.handler.verify_redirection()

        # Verify the result
        self.assertFalse(result)
        mock_get.assert_called_once()

    @mock.patch('requests.get')
    def test_verify_redirection_exception(self, mock_get):
        """Test redirection verification - exception case"""
        # Create a test cache mapping
        test_cache = {self.package_files[0]: f"{self.cdn_base_url}{self.package_files[0]}"}
        self.handler.cache_mapping = test_cache

        # Mock an exception
        mock_get.side_effect = Exception("Test exception")

        # Call the method
        result = self.handler.verify_redirection()

        # Verify the result
        self.assertFalse(result)
        mock_get.assert_called_once()


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python
#!/usr/bin/env python

"""
Integration tests for the pypiserver redirection feature

These tests simulate the end-to-end workflow of:
1. Setting up pypiserver
2. Creating a redirection cache
3. Verifying redirection works
"""

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock
from urllib.parse import quote

import requests

from pypiserver_redirection.redirect_handler import RedirectionHandler


@unittest.skipIf(not os.environ.get('RUN_INTEGRATION_TESTS'), "Integration tests skipped")
class TestRedirectionIntegration(unittest.TestCase):
    """Integration tests for the redirection feature"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for packages
        self.temp_dir = tempfile.TemporaryDirectory()
        self.packages_dir = os.path.join(self.temp_dir.name, "packages")
        os.makedirs(self.packages_dir)

        # Create a temporary directory for the "CDN"
        self.cdn_dir = os.path.join(self.temp_dir.name, "cdn")
        os.makedirs(self.cdn_dir)

        # Create a test package file
        self.package_name = "test-package-1.0.0.tar.gz"
        self.package_path = os.path.join(self.packages_dir, self.package_name)
        with open(self.package_path, "wb") as f:
            f.write(b"dummy package content")

        # Create a cache file
        self.cache_file = os.path.join(self.temp_dir.name, "redirect_cache.json")

        # Configure PyPIServer
        self.pypiserver_port = 8123  # Use a non-standard port to avoid conflicts
        self.pypiserver_url = f"http://localhost:{self.pypiserver_port}"
        self.cdn_base_url = f"file://{os.path.abspath(self.cdn_dir)}/"

        # Start PyPIServer
        self.start_pypiserver()

    def tearDown(self):
        """Clean up test fixtures"""
        # Stop PyPIServer
        if hasattr(self, "pypiserver_process"):
            self.pypiserver_process.terminate()
            self.pypiserver_process.wait()

        # Clean up temporary directory
        self.temp_dir.cleanup()

    def start_pypiserver(self):
        """Start PyPIServer as a subprocess"""
        cmd = [
            sys.executable, "-m", "pypiserver", "run",
            f"--port={self.pypiserver_port}",
            self.packages_dir
        ]

        self.pypiserver_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Give the server a moment to start
        time.sleep(2)

        # Verify the server is running
        try:
            response = requests.get(f"{self.pypiserver_url}/simple/")
            if response.status_code != 200:
                self.fail(f"PyPIServer failed to start, status code: {response.status_code}")
        except requests.RequestException as e:
            self.fail(f"PyPIServer failed to start: {e}")

    def test_redirection_workflow(self):
        """Test the complete redirection workflow"""
        # Create a custom RedirectionHandler that copies files to our local "CDN"
        class LocalRedirectionHandler(RedirectionHandler):
            def upload_to_cdn(self, package_path):
                filename = os.path.basename(package_path)
                dst_path = os.path.join(self.temp_dir, filename)
                with open(package_path, "rb") as src, open(dst_path, "wb") as dst:
                    dst.write(src.read())
                return f"{self.cdn_base_url}{filename}"

        # Initialize the handler
        handler = LocalRedirectionHandler(
            pypiserver_url=self.pypiserver_url,
            packages_dir=self.packages_dir,
            cdn_base_url=self.cdn_base_url,
            cache_file=self.cache_file
        )
        handler.temp_dir = self.cdn_dir  # Add temp_dir attribute for our custom upload_to_cdn

        # Update the cache mapping
        cache = handler.update_cache_mapping()

        # Verify the package is in the cache
        self.assertIn(self.package_name, cache)

        # Verify the package was copied to the CDN
        cdn_file_path = os.path.join(self.cdn_dir, self.package_name)
        self.assertTrue(os.path.exists(cdn_file_path))

        # Get the URL with the cache mapping
        encoded_cache = handler.get_encoded_cache()
        package_url = f"{self.pypiserver_url}/packages/{self.package_name}?cached_links={encoded_cache}"

        # Request the package URL with redirect=False to check redirection
        response = requests.get(package_url, allow_redirects=False)

        # Verify we got a redirect
        self.assertIn(response.status_code, (301, 302, 303, 307))

        # Verify the redirect URL matches our CDN URL
        expected_redirect = f"{self.cdn_base_url}{self.package_name}"
        self.assertEqual(response.headers.get('Location'), expected_redirect)


# Alternative integration test that doesn't require an actual PyPIServer
class TestMockIntegration(unittest.TestCase):
    """Mock integration tests for the redirection feature"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for packages
        self.temp_dir = tempfile.TemporaryDirectory()
        self.packages_dir = os.path.join(self.temp_dir.name, "packages")
        os.makedirs(self.packages_dir)

        # Create a temporary directory for the "CDN"
        self.cdn_dir = os.path.join(self.temp_dir.name, "cdn")
        os.makedirs(self.cdn_dir)

        # Create a test package file
        self.package_name = "test-package-1.0.0.tar.gz"
        self.package_path = os.path.join(self.packages_dir, self.package_name)
        with open(self.package_path, "wb") as f:
            f.write(b"dummy package content")

        # Create a cache file
        self.cache_file = os.path.join(self.temp_dir.name, "redirect_cache.json")

        # Configure mock server
        self.pypiserver_url = "http://localhost:8080"
        self.cdn_base_url = f"file://{os.path.abspath(self.cdn_dir)}/"

    def tearDown(self):
        """Clean up test fixtures"""
        self.temp_dir.cleanup()

    @mock.patch('requests.get')
    def test_mock_redirection_workflow(self, mock_get):
        """Test the redirection workflow with mocked server"""
        # Create a custom RedirectionHandler that copies files to our local "CDN"
        class LocalRedirectionHandler(RedirectionHandler):
            def upload_to_cdn(self, package_path):
                filename = os.path.basename(package_path)
                dst_path = os.path.join(self.temp_dir, filename)
                with open(package_path, "rb") as src, open(dst_path, "wb") as dst:
                    dst.write(src.read())
                return f"{self.cdn_base_url}{filename}"

        # Mock a successful response from the server
        mock_response = mock.MagicMock()
        mock_response.status_code = 302  # Redirect status
        mock_response.headers = {'Location': f"{self.cdn_base_url}{self.package_name}"}
        mock_get.return_value = mock_response

        # Initialize the handler
        handler = LocalRedirectionHandler(
            pypiserver_url=self.pypiserver_url,
            packages_dir=self.packages_dir,
            cdn_base_url=self.cdn_base_url,
            cache_file=self.cache_file
        )
        handler.temp_dir = self.cdn_dir  # Add temp_dir attribute for our custom upload_to_cdn

        # Update the cache mapping
        cache = handler.update_cache_mapping()

        # Verify the package is in the cache
        self.assertIn(self.package_name, cache)

        # Verify the package was copied to the CDN
        cdn_file_path = os.path.join(self.cdn_dir, self.package_name)
        self.assertTrue(os.path.exists(cdn_file_path))

        # Test redirection verification
        result = handler.verify_redirection()
        self.assertTrue(result)

        # Verify the correct URL was requested
        encoded_cache = handler.get_encoded_cache()
        packages_url = f"{self.pypiserver_url}/packages/?cached_links={encoded_cache}"
        mock_get.assert_called_with(packages_url, allow_redirects=False)


if __name__ == "__main__":
    unittest.main()
"""
Integration tests for the pypiserver redirection feature

These tests simulate the end-to-end workflow of:
1. Setting up pypiserver
2. Creating a redirection cache
3. Verifying redirection works
"""

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock
from urllib.parse import quote

import requests

# Add the parent directory to the path so we can import the module being tested
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from redirect_handler import RedirectionHandler


@unittest.skipIf(not os.environ.get('RUN_INTEGRATION_TESTS'), "Integration tests skipped")
class TestRedirectionIntegration(unittest.TestCase):
    """Integration tests for the redirection feature"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for packages
        self.temp_dir = tempfile.TemporaryDirectory()
        self.packages_dir = os.path.join(self.temp_dir.name, "packages")
        os.makedirs(self.packages_dir)

        # Create a temporary directory for the "CDN"
        self.cdn_dir = os.path.join(self.temp_dir.name, "cdn")
        os.makedirs(self.cdn_dir)

        # Create a test package file
        self.package_name = "test-package-1.0.0.tar.gz"
        self.package_path = os.path.join(self.packages_dir, self.package_name)
        with open(self.package_path, "wb") as f:
            f.write(b"dummy package content")

        # Create a cache file
        self.cache_file = os.path.join(self.temp_dir.name, "redirect_cache.json")

        # Configure PyPIServer
        self.pypiserver_port = 8123  # Use a non-standard port to avoid conflicts
        self.pypiserver_url = f"http://localhost:{self.pypiserver_port}"
        self.cdn_base_url = f"file://{os.path.abspath(self.cdn_dir)}/"

        # Start PyPIServer
        self.start_pypiserver()

    def tearDown(self):
        """Clean up test fixtures"""
        # Stop PyPIServer
        if hasattr(self, "pypiserver_process"):
            self.pypiserver_process.terminate()
            self.pypiserver_process.wait()

        # Clean up temporary directory
        self.temp_dir.cleanup()

    def start_pypiserver(self):
        """Start PyPIServer as a subprocess"""
        cmd = [
            sys.executable, "-m", "pypiserver", "run",
            f"--port={self.pypiserver_port}",
            self.packages_dir
        ]

        self.pypiserver_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Give the server a moment to start
        time.sleep(2)

        # Verify the server is running
        try:
            response = requests.get(f"{self.pypiserver_url}/simple/")
            if response.status_code != 200:
                self.fail(f"PyPIServer failed to start, status code: {response.status_code}")
        except requests.RequestException as e:
            self.fail(f"PyPIServer failed to start: {e}")

    def test_redirection_workflow(self):
        """Test the complete redirection workflow"""
        # Create a custom RedirectionHandler that copies files to our local "CDN"
        class LocalRedirectionHandler(RedirectionHandler):
            def upload_to_cdn(self, package_path):
                filename = os.path.basename(package_path)
                dst_path = os.path.join(self.temp_dir, filename)
                with open(package_path, "rb") as src, open(dst_path, "wb") as dst:
                    dst.write(src.read())
                return f"{self.cdn_base_url}{filename}"

        # Initialize the handler
        handler = LocalRedirectionHandler(
            pypiserver_url=self.pypiserver_url,
            packages_dir=self.packages_dir,
            cdn_base_url=self.cdn_base_url,
            cache_file=self.cache_file
        )
        handler.temp_dir = self.cdn_dir  # Add temp_dir attribute for our custom upload_to_cdn

        # Update the cache mapping
        cache = handler.update_cache_mapping()

        # Verify the package is in the cache
        self.assertIn(self.package_name, cache)

        # Verify the package was copied to the CDN
        cdn_file_path = os.path.join(self.cdn_dir, self.package_name)
        self.assertTrue(os.path.exists(cdn_file_path))

        # Get the URL with the cache mapping
        encoded_cache = handler.get_encoded_cache()
        package_url = f"{self.pypiserver_url}/packages/{self.package_name}?cached_links={encoded_cache}"

        # Request the package URL with redirect=False to check redirection
        response = requests.get(package_url, allow_redirects=False)

        # Verify we got a redirect
        self.assertIn(response.status_code, (301, 302, 303, 307))

        # Verify the redirect URL matches our CDN URL
        expected_redirect = f"{self.cdn_base_url}{self.package_name}"
        self.assertEqual(response.headers.get('Location'), expected_redirect)


# Alternative integration test that doesn't require an actual PyPIServer
class TestMockIntegration(unittest.TestCase):
    """Mock integration tests for the redirection feature"""

    def setUp(self):
        """Set up test fixtures"""
        # Create a temporary directory for packages
        self.temp_dir = tempfile.TemporaryDirectory()
        self.packages_dir = os.path.join(self.temp_dir.name, "packages")
        os.makedirs(self.packages_dir)

        # Create a temporary directory for the "CDN"
        self.cdn_dir = os.path.join(self.temp_dir.name, "cdn")
        os.makedirs(self.cdn_dir)

        # Create a test package file
        self.package_name = "test-package-1.0.0.tar.gz"
        self.package_path = os.path.join(self.packages_dir, self.package_name)
        with open(self.package_path, "wb") as f:
            f.write(b"dummy package content")

        # Create a cache file
        self.cache_file = os.path.join(self.temp_dir.name, "redirect_cache.json")

        # Configure mock server
        self.pypiserver_url = "http://localhost:8080"
        self.cdn_base_url = f"file://{os.path.abspath(self.cdn_dir)}/"

    def tearDown(self):
        """Clean up test fixtures"""
        self.temp_dir.cleanup()

    @mock.patch('requests.get')
    def test_mock_redirection_workflow(self, mock_get):
        """Test the redirection workflow with mocked server"""
        # Create a custom RedirectionHandler that copies files to our local "CDN"
        class LocalRedirectionHandler(RedirectionHandler):
            def upload_to_cdn(self, package_path):
                filename = os.path.basename(package_path)
                dst_path = os.path.join(self.temp_dir, filename)
                with open(package_path, "rb") as src, open(dst_path, "wb") as dst:
                    dst.write(src.read())
                return f"{self.cdn_base_url}{filename}"

        # Mock a successful response from the server
        mock_response = mock.MagicMock()
        mock_response.status_code = 302  # Redirect status
        mock_response.headers = {'Location': f"{self.cdn_base_url}{self.package_name}"}
        mock_get.return_value = mock_response

        # Initialize the handler
        handler = LocalRedirectionHandler(
            pypiserver_url=self.pypiserver_url,
            packages_dir=self.packages_dir,
            cdn_base_url=self.cdn_base_url,
            cache_file=self.cache_file
        )
        handler.temp_dir = self.cdn_dir  # Add temp_dir attribute for our custom upload_to_cdn

        # Update the cache mapping
        cache = handler.update_cache_mapping()

        # Verify the package is in the cache
        self.assertIn(self.package_name, cache)

        # Verify the package was copied to the CDN
        cdn_file_path = os.path.join(self.cdn_dir, self.package_name)
        self.assertTrue(os.path.exists(cdn_file_path))

        # Test redirection verification
        result = handler.verify_redirection()
        self.assertTrue(result)

        # Verify the correct URL was requested
        encoded_cache = handler.get_encoded_cache()
        packages_url = f"{self.pypiserver_url}/packages/?cached_links={encoded_cache}"
        mock_get.assert_called_with(packages_url, allow_redirects=False)


if __name__ == "__main__":
    unittest.main()

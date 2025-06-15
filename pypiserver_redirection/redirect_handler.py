#!/usr/bin/env python
#!/usr/bin/env python

"""
Redirection handler for PyPIServer.

This module provides functionality to redirect package downloads from PyPIServer
to external URLs such as CDNs or cloud storage services.
"""

import json
import os
import logging
import argparse
from urllib.parse import quote
import requests

logger = logging.getLogger(__name__)


class RedirectionHandler:
    """
    Base class for handling redirections from PyPIServer to external URLs.
    This can be extended for specific storage backends.
    """

    def __init__(self, pypiserver_url, packages_dir, cdn_base_url, cache_file=None):
        """
        Initialize the redirection handler.

        Args:
            pypiserver_url: The base URL of your pypiserver instance
            packages_dir: Local directory where packages are stored
            cdn_base_url: Base URL for the CDN or storage service
            cache_file: Optional file to persist the cache mapping
        """
        self.pypiserver_url = pypiserver_url.rstrip('/')
        self.packages_dir = packages_dir
        self.cdn_base_url = cdn_base_url.rstrip('/') + '/'
        self.cache_file = cache_file
        self.cache_mapping = {}

        # Load cache if available
        if cache_file and os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    self.cache_mapping = json.load(f)
                logger.info(f"Loaded {len(self.cache_mapping)} entries from cache file")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse cache file {cache_file}")

    def upload_to_cdn(self, package_path):
        """
        Upload a package to a CDN or storage service.
        This method should be implemented by subclasses for specific storage backends.

        Args:
            package_path: Path to the package file to upload

        Returns:
            The URL where the package can be accessed
        """
        filename = os.path.basename(package_path)
        return f"{self.cdn_base_url}{filename}"

    def update_cache_mapping(self, force_update=False):
        """
        Update the cache mapping of package filenames to their CDN URLs.

        Args:
            force_update: If True, update all packages even if they're already in cache

        Returns:
            The updated cache mapping dictionary
        """
        # List all packages in the directory
        logger.info(f"Scanning packages in {self.packages_dir}")
        for filename in os.listdir(self.packages_dir):
            if filename.endswith((".whl", ".tar.gz", ".zip", ".egg")):
                full_path = os.path.join(self.packages_dir, filename)

                # Skip if already in cache and not forcing update
                if filename in self.cache_mapping and not force_update:
                    logger.debug(f"Skipping {filename} (already in cache)")
                    continue

                # Upload to CDN and get the URL
                cdn_url = self.upload_to_cdn(full_path)

                # Add to mapping
                self.cache_mapping[filename] = cdn_url
                logger.info(f"Added {filename} -> {cdn_url}")

        # Save the cache
        if self.cache_file:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache_mapping, f, indent=2)
            logger.info(f"Saved cache mapping to {self.cache_file}")

        return self.cache_mapping

    def get_pypiserver_url_with_cache(self, endpoint="simple"):
        """
        Get the PyPIServer URL with the cache mapping included as a query parameter.

        Args:
            endpoint: The PyPIServer endpoint ("simple" or "packages")

        Returns:
            URL with cache mapping as a query parameter
        """
        cache_json = json.dumps(self.cache_mapping)
        encoded_cache = quote(cache_json)
        return f"{self.pypiserver_url}/{endpoint}/?cached_links={encoded_cache}"

    def verify_redirection(self, package_name=None):
        """
        Verify that redirection is working for a specific package.

        Args:
            package_name: Optional specific package to test

        Returns:
            True if redirection is working, False otherwise
        """
        if not package_name and self.cache_mapping:
            # Use the first package in the cache
            package_name = next(iter(self.cache_mapping.keys()))

        if not package_name:
            logger.error("No package available to test redirection")
            return False

        # Get the URL for the package
        cache_json = json.dumps(self.cache_mapping)
        encoded_cache = quote(cache_json)
        package_url = f"{self.pypiserver_url}/packages/{package_name}?cached_links={encoded_cache}"

        # Make the request with allow_redirects=False to see the redirect
        try:
            response = requests.get(package_url, allow_redirects=False)

            if response.status_code in (301, 302, 303, 307):
                redirect_url = response.headers.get('Location')
                if redirect_url and redirect_url == self.cache_mapping.get(package_name):
                    logger.info(f"Redirection verified: {package_url} -> {redirect_url}")
                    return True
                else:
                    logger.error(f"Unexpected redirect: {redirect_url}")
                    return False
            else:
                logger.error(f"Expected redirect, got status code {response.status_code}")
                return False
        except requests.RequestException as e:
            logger.error(f"Request error during verification: {e}")
            return False


def main():
    """
    Command-line interface for the redirection handler.
    """
    parser = argparse.ArgumentParser(description="PyPIServer redirection handler")
    parser.add_argument("--pypiserver", default="http://localhost:8080", help="PyPI server URL")
    parser.add_argument("--packages-dir", default="./packages", help="Directory containing packages")
    parser.add_argument("--cdn-url", required=True, help="Base URL for the CDN or storage service")
    parser.add_argument("--cache-file", default="redirect_cache.json", help="File to store cache mapping")
    parser.add_argument("--force-update", action="store_true", help="Force update of all packages")
    parser.add_argument("--print-url", action="store_true", help="Print the pypiserver URL with cache mapping")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Create the handler
    handler = RedirectionHandler(
        pypiserver_url=args.pypiserver,
        packages_dir=args.packages_dir,
        cdn_base_url=args.cdn_url,
        cache_file=args.cache_file
    )

    # Update the cache
    handler.update_cache_mapping(force_update=args.force_update)

    # Print URLs for pip
    if args.print_url:
        simple_url = handler.get_pypiserver_url_with_cache("simple")
        packages_url = handler.get_pypiserver_url_with_cache("packages")

        print("\nPypiserver URLs with cache mapping:")
        print(f"Simple index: {simple_url}")
        print(f"Packages index: {packages_url}")
        print("\nTo use with pip:")
        print(f"pip install --extra-index-url {simple_url} <package>")

    # Verify redirection
    handler.verify_redirection()


if __name__ == "__main__":
    main()
"""
Redirection handler for pypiserver

This module provides functionality to handle redirecting package downloads to external URLs
such as CDNs or other storage services. It uploads package files to external storage,
maintains a cache of file-to-URL mappings, and formats the cache for use with pypiserver.
"""

import json
import os
import sys
import time
from urllib.parse import quote
import requests
from typing import Dict, List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RedirectionHandler:
    """
    Handles the upload of packages to external storage and maintains a cache of URL mappings
    for use with pypiserver's redirection feature.
    """

    def __init__(self, 
                 pypiserver_url: str, 
                 packages_dir: str, 
                 cdn_base_url: str,
                 cache_file: Optional[str] = None):
        """
        Initialize the redirection handler.

        Args:
            pypiserver_url: The base URL of your pypiserver instance
            packages_dir: Local directory where packages are stored
            cdn_base_url: Base URL of your CDN or storage service
            cache_file: Optional file to persist the cache mapping
        """
        self.pypiserver_url = pypiserver_url.rstrip('/')
        self.packages_dir = os.path.abspath(packages_dir)
        self.cdn_base_url = cdn_base_url.rstrip('/') + '/'
        self.cache_file = cache_file
        self.cache_mapping = {}

        # Load cache from file if it exists
        if cache_file and os.path.exists(cache_file):
            self.load_cache()

    def upload_to_cdn(self, package_path: str) -> str:
        """
        Upload a package to a CDN or storage service.

        This is a placeholder method that should be overridden with your actual
        upload implementation. This example simply returns a URL without actually
        uploading anything.

        Args:
            package_path: Path to the package file to upload

        Returns:
            The URL where the package can be accessed
        """
        filename = os.path.basename(package_path)
        # In a real implementation, you would upload the file here
        # Example: upload_to_s3(package_path, filename)
        logger.info(f"Uploading {filename} to CDN")

        # Simulate upload delay
        time.sleep(0.1)

        return f"{self.cdn_base_url}{filename}"

    def scan_packages(self) -> List[str]:
        """
        Scan the packages directory for package files.

        Returns:
            List of package file paths
        """
        package_files = []
        for filename in os.listdir(self.packages_dir):
            if filename.endswith(('.whl', '.tar.gz', '.zip', '.egg')):
                package_files.append(os.path.join(self.packages_dir, filename))
        return package_files

    def update_cache_mapping(self, force_update: bool = False) -> Dict[str, str]:
        """
        Update the cache mapping with all packages in the directory.

        Args:
            force_update: If True, update all packages even if they're already in the cache

        Returns:
            The updated cache mapping
        """
        package_files = self.scan_packages()
        logger.info(f"Found {len(package_files)} packages in {self.packages_dir}")

        for package_path in package_files:
            filename = os.path.basename(package_path)

            # Skip if already in cache and not forcing update
            if filename in self.cache_mapping and not force_update:
                logger.debug(f"Skipping {filename} (already in cache)")
                continue

            # Upload to CDN and get URL
            cdn_url = self.upload_to_cdn(package_path)
            self.cache_mapping[filename] = cdn_url
            logger.info(f"Added {filename} -> {cdn_url}")

        # Save cache if cache file is specified
        if self.cache_file:
            self.save_cache()

        return self.cache_mapping

    def save_cache(self) -> None:
        """
        Save the cache mapping to the cache file.
        """
        if not self.cache_file:
            return
#!/usr/bin/env python
"""
Redirection handler for PyPIServer.

This module provides functionality to redirect package downloads from PyPIServer
to external URLs such as CDNs or cloud storage services.
"""

import json
import os
import logging
from urllib.parse import quote
import requests

logger = logging.getLogger(__name__)

class RedirectionHandler:
    """
    Base class for handling redirections from PyPIServer to external URLs.
    This can be extended for specific storage backends.
    """

    def __init__(self, pypiserver_url, packages_dir, cdn_base_url, cache_file=None):
        """
        Initialize the redirection handler.

        Args:
            pypiserver_url: The base URL of your pypiserver instance
            packages_dir: Local directory where packages are stored
            cdn_base_url: Base URL for the CDN or storage service
            cache_file: Optional file to persist the cache mapping
        """
        self.pypiserver_url = pypiserver_url.rstrip('/')
        self.packages_dir = packages_dir
        self.cdn_base_url = cdn_base_url.rstrip('/') + '/'
        self.cache_file = cache_file
        self.cache_mapping = {}

        # Load cache if available
        if cache_file and os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    self.cache_mapping = json.load(f)
                logger.info(f"Loaded {len(self.cache_mapping)} entries from cache file")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse cache file {cache_file}")

    def upload_to_cdn(self, package_path):
        """
        Upload a package to a CDN or storage service.
        This method should be implemented by subclasses for specific storage backends.

        Args:
            package_path: Path to the package file to upload

        Returns:
            The URL where the package can be accessed
        """
        filename = os.path.basename(package_path)
        return f"{self.cdn_base_url}{filename}"

    def update_cache_mapping(self, force_update=False):
        """
        Update the cache mapping of package filenames to their CDN URLs.

        Args:
            force_update: If True, update all packages even if they're already in cache

        Returns:
            The updated cache mapping dictionary
        """
        # List all packages in the directory
        logger.info(f"Scanning packages in {self.packages_dir}")
        for filename in os.listdir(self.packages_dir):
            if filename.endswith((".whl", ".tar.gz", ".zip", ".egg")):
                full_path = os.path.join(self.packages_dir, filename)

                # Skip if already in cache and not forcing update
                if filename in self.cache_mapping and not force_update:
                    logger.debug(f"Skipping {filename} (already in cache)")
                    continue

                # Upload to CDN and get the URL
                cdn_url = self.upload_to_cdn(full_path)

                # Add to mapping
                self.cache_mapping[filename] = cdn_url
                logger.info(f"Added {filename} -> {cdn_url}")

        # Save the cache
        if self.cache_file:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache_mapping, f, indent=2)
            logger.info(f"Saved cache mapping to {self.cache_file}")

        return self.cache_mapping

    def get_pypiserver_url_with_cache(self, endpoint="simple"):
        """
        Get the PyPIServer URL with the cache mapping included as a query parameter.

        Args:
            endpoint: The PyPIServer endpoint ("simple" or "packages")

        Returns:
            URL with cache mapping as a query parameter
        """
        cache_json = json.dumps(self.cache_mapping)
        encoded_cache = quote(cache_json)
        return f"{self.pypiserver_url}/{endpoint}/?cached_links={encoded_cache}"

    def verify_redirection(self, package_name=None):
        """
        Verify that redirection is working for a specific package.

        Args:
            package_name: Optional specific package to test

        Returns:
            True if redirection is working, False otherwise
        """
        if not package_name and self.cache_mapping:
            # Use the first package in the cache
            package_name = next(iter(self.cache_mapping.keys()))

        if not package_name:
            logger.error("No package available to test redirection")
            return False
#!/usr/bin/env python
"""
Redirection handler for PyPIServer.

This module provides functionality to redirect package downloads from PyPIServer
to external URLs such as CDNs or cloud storage services.
"""

import json
import os
import logging
from urllib.parse import quote
import requests

logger = logging.getLogger(__name__)

class RedirectionHandler:
    """
    Base class for handling redirections from PyPIServer to external URLs.
    This can be extended for specific storage backends.
    """

    def __init__(self, pypiserver_url, packages_dir, cdn_base_url, cache_file=None):
        """
        Initialize the redirection handler.

        Args:
            pypiserver_url: The base URL of your pypiserver instance
            packages_dir: Local directory where packages are stored
            cdn_base_url: Base URL for the CDN or storage service
            cache_file: Optional file to persist the cache mapping
        """
        self.pypiserver_url = pypiserver_url.rstrip('/')
        self.packages_dir = packages_dir
        self.cdn_base_url = cdn_base_url.rstrip('/') + '/'
        self.cache_file = cache_file
        self.cache_mapping = {}

        # Load cache if available
        if cache_file and os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    self.cache_mapping = json.load(f)
                logger.info(f"Loaded {len(self.cache_mapping)} entries from cache file")
            except json.JSONDecodeError:
                logger.error(f"Failed to parse cache file {cache_file}")

    def upload_to_cdn(self, package_path):
        """
        Upload a package to a CDN or storage service.
        This method should be implemented by subclasses for specific storage backends.

        Args:
            package_path: Path to the package file to upload

        Returns:
            The URL where the package can be accessed
        """
        filename = os.path.basename(package_path)
        return f"{self.cdn_base_url}{filename}"

    def update_cache_mapping(self, force_update=False):
        """
        Update the cache mapping of package filenames to their CDN URLs.

        Args:
            force_update: If True, update all packages even if they're already in cache

        Returns:
            The updated cache mapping dictionary
        """
        # List all packages in the directory
        logger.info(f"Scanning packages in {self.packages_dir}")
        for filename in os.listdir(self.packages_dir):
            if filename.endswith((".whl", ".tar.gz", ".zip", ".egg")):
                full_path = os.path.join(self.packages_dir, filename)

                # Skip if already in cache and not forcing update
                if filename in self.cache_mapping and not force_update:
                    logger.debug(f"Skipping {filename} (already in cache)")
                    continue

                # Upload to CDN and get the URL
                cdn_url = self.upload_to_cdn(full_path)

                # Add to mapping
                self.cache_mapping[filename] = cdn_url
                logger.info(f"Added {filename} -> {cdn_url}")

        # Save the cache
        if self.cache_file:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache_mapping, f, indent=2)
            logger.info(f"Saved cache mapping to {self.cache_file}")

        return self.cache_mapping

    def get_pypiserver_url_with_cache(self, endpoint="simple"):
        """
        Get the PyPIServer URL with the cache mapping included as a query parameter.

        Args:
            endpoint: The PyPIServer endpoint ("simple" or "packages")

        Returns:
            URL with cache mapping as a query parameter
        """
        cache_json = json.dumps(self.cache_mapping)
        encoded_cache = quote(cache_json)
        return f"{self.pypiserver_url}/{endpoint}/?cached_links={encoded_cache}"

    def verify_redirection(self, package_name=None):
        """
        Verify that redirection is working for a specific package.

        Args:
            package_name: Optional specific package to test

        Returns:
            True if redirection is working, False otherwise
        """
        if not package_name and self.cache_mapping:
            # Use the first package in the cache
            package_name = next(iter(self.cache_mapping.keys()))

        if not package_name:
            logger.error("No package available to test redirection")
            return False

        # Get the URL for the package
        cache_json = json.dumps(self.cache_mapping)
        encoded_cache = quote(cache_json)
        package_url = f"{self.pypiserver_url}/packages/{package_name}?cached_links={encoded_cache}"

        # Make the request with allow_redirects=False to see the redirect
        try:
            response = requests.get(package_url, allow_redirects=False)

            if response.status_code in (301, 302, 303, 307):
                redirect_url = response.headers.get('Location')
                if redirect_url and redirect_url == self.cache_mapping.get(package_name):
                    logger.info(f"Redirection verified: {package_url} -> {redirect_url}")
                    return True
                else:
                    logger.error(f"Unexpected redirect: {redirect_url}")
                    return False
            else:
                logger.error(f"Expected redirect, got status code {response.status_code}")
                return False
        except requests.RequestException as e:
            logger.error(f"Request error during verification: {e}")
            return False
        # Get the URL for the package
        cache_json = json.dumps(self.cache_mapping)
        encoded_cache = quote(cache_json)
        package_url = f"{self.pypiserver_url}/packages/{package_name}?cached_links={encoded_cache}"

        # Make the request with allow_redirects=False to see the redirect
        try:
            response = requests.get(package_url, allow_redirects=False)

            if response.status_code in (301, 302, 303, 307):
                redirect_url = response.headers.get('Location')
                if redirect_url and redirect_url == self.cache_mapping.get(package_name):
                    logger.info(f"Redirection verified: {package_url} -> {redirect_url}")
                    return True
                else:
                    logger.error(f"Unexpected redirect: {redirect_url}")
                    return False
            else:
                logger.error(f"Expected redirect, got status code {response.status_code}")
                return False
        except requests.RequestException as e:
            logger.error(f"Request error during verification: {e}")
            return False
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache_mapping, f, indent=2)
        logger.info(f"Saved cache mapping to {self.cache_file}")

    def load_cache(self) -> Dict[str, str]:
        """
        Load the cache mapping from the cache file.

        Returns:
            The loaded cache mapping
        """
        if not self.cache_file or not os.path.exists(self.cache_file):
            return {}

        try:
            with open(self.cache_file, 'r') as f:
                self.cache_mapping = json.load(f)
            logger.info(f"Loaded cache mapping from {self.cache_file} with {len(self.cache_mapping)} entries")
            return self.cache_mapping
        except json.JSONDecodeError:
            logger.error(f"Failed to parse cache file {self.cache_file}")
            return {}

    def get_encoded_cache(self) -> str:
        """
        Get the URL-encoded cache mapping string for use with pypiserver.

        Returns:
            URL-encoded JSON string of the cache mapping
        """
        cache_json = json.dumps(self.cache_mapping)
        return quote(cache_json)

    def get_pypiserver_url_with_cache(self, endpoint: str = "simple") -> str:
        """
        Get the pypiserver URL with the cache mapping included.

        Args:
            endpoint: The pypiserver endpoint ("simple" or "packages")

        Returns:
            URL to use for pip or other tools
        """
        encoded_cache = self.get_encoded_cache()
        endpoint = endpoint.strip('/')
        return f"{self.pypiserver_url}/{endpoint}/?cached_links={encoded_cache}"

    def verify_redirection(self, package_name: Optional[str] = None) -> bool:
        """
        Verify that redirection is working by making a test request.

        Args:
            package_name: Optional specific package to test

        Returns:
            True if redirection is working, False otherwise
        """
        url = self.get_pypiserver_url_with_cache("packages")
        try:
            response = requests.get(url, allow_redirects=False)
            if response.status_code == 200:
                logger.info("Redirection test successful")
                return True
            else:
                logger.error(f"Redirection test failed with status code {response.status_code}")
                return False
        except requests.RequestException as e:
            logger.error(f"Failed to connect to pypiserver: {e}")
            return False


def main():
    """
    Example usage of the RedirectionHandler class.
    """
    # Get configuration from command line or environment
    pypiserver_url = os.environ.get("PYPISERVER_URL", "http://localhost:8080")
    packages_dir = os.environ.get("PACKAGES_DIR", "./packages")
    cdn_base_url = os.environ.get("CDN_BASE_URL", "https://example-cdn.com/packages/")
    cache_file = os.environ.get("CACHE_FILE", "redirect_cache.json")

    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Manage package redirection for pypiserver")
    parser.add_argument("--pypiserver", default=pypiserver_url, help="PyPI server URL")
    parser.add_argument("--packages-dir", default=packages_dir, help="Directory containing packages")
    parser.add_argument("--cdn-url", default=cdn_base_url, help="Base URL of CDN or storage service")
    parser.add_argument("--cache-file", default=cache_file, help="File to store cache mapping")
    parser.add_argument("--force-update", action="store_true", help="Force update of all packages")
    parser.add_argument("--print-url", action="store_true", help="Print the pypiserver URL with cache mapping")

    args = parser.parse_args()

    # Create the handler
    handler = RedirectionHandler(
        pypiserver_url=args.pypiserver,
        packages_dir=args.packages_dir,
        cdn_base_url=args.cdn_url,
        cache_file=args.cache_file
    )

    # Update the cache
    handler.update_cache_mapping(force_update=args.force_update)

    # Print URLs for pip
    simple_url = handler.get_pypiserver_url_with_cache("simple")
    packages_url = handler.get_pypiserver_url_with_cache("packages")

    if args.print_url:
        print("\nPypiserver URLs with cache mapping:")
        print(f"Simple index: {simple_url}")
        print(f"Packages index: {packages_url}")
        print("\nTo use with pip:")
        print(f"pip install --extra-index-url {simple_url} <package>")

    # Verify redirection
    handler.verify_redirection()


if __name__ == "__main__":
    main()

#!/usr/bin/env python
#!/usr/bin/env python

"""
Example Google Cloud Storage integration for PyPIServer redirection

This extends the RedirectionHandler with a GCS-specific implementation.
"""

import os
import sys
import logging

# Import from parent module
from pypiserver_redirection import RedirectionHandler

logger = logging.getLogger(__name__)

class GCSRedirectionHandler(RedirectionHandler):
    """
    Extends RedirectionHandler with Google Cloud Storage specific functionality
    """

    def __init__(self, 
                 pypiserver_url: str, 
                 packages_dir: str, 
                 bucket_name: str,
                 object_prefix: str = "packages/",
                 cache_file: str = None,
                 public: bool = True):
        """
        Initialize GCS redirection handler

        Args:
            pypiserver_url: The base URL of your pypiserver instance
            packages_dir: Local directory where packages are stored
            bucket_name: Name of the GCS bucket
            object_prefix: Prefix for objects in the bucket (default: "packages/")
            cache_file: Optional file to persist the cache mapping
            public: Whether to make uploaded objects publicly accessible
        """
        try:
            from google.cloud import storage
        except ImportError:
            raise ImportError("google-cloud-storage package is required. Install with 'pip install google-cloud-storage'")

        # GCS specific settings
        self.bucket_name = bucket_name
        self.object_prefix = object_prefix.rstrip("/") + "/"
        self.public = public

        # Initialize GCS client
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(bucket_name)

        # Calculate the CDN base URL for GCS
        cdn_base_url = f"https://storage.googleapis.com/{self.bucket_name}/{self.object_prefix}"

        # Initialize the parent class
        super().__init__(pypiserver_url, packages_dir, cdn_base_url, cache_file)

    def upload_to_cdn(self, package_path: str) -> str:
        """
        Upload a package to Google Cloud Storage bucket

        Args:
            package_path: Path to the package file to upload

        Returns:
            The URL where the package can be accessed
        """
        filename = os.path.basename(package_path)
        object_name = f"{self.object_prefix}{filename}"

        # Create a blob
        blob = self.bucket.blob(object_name)

        # Upload the file
        try:
            logger.info(f"Uploading {filename} to GCS bucket {self.bucket_name}")
            blob.upload_from_filename(package_path)

            # Make the blob publicly accessible if requested
            if self.public:
                blob.make_public()

            logger.info(f"Successfully uploaded {filename} to GCS")
        except Exception as e:
            logger.error(f"Failed to upload {filename} to GCS: {e}")
            raise

        # Return the URL
        return f"{self.cdn_base_url}{filename}"


def main():
    """
    Example usage of the GCSRedirectionHandler
    """
    import argparse

    parser = argparse.ArgumentParser(description="Manage package redirection for pypiserver using Google Cloud Storage")
    parser.add_argument("--pypiserver", default="http://localhost:8080", help="PyPI server URL")
    parser.add_argument("--packages-dir", default="./packages", help="Directory containing packages")
    parser.add_argument("--bucket", required=True, help="GCS bucket name")
    parser.add_argument("--prefix", default="packages/", help="Object prefix in GCS bucket")
    parser.add_argument("--cache-file", default="gcs_redirect_cache.json", help="File to store cache mapping")
    parser.add_argument("--force-update", action="store_true", help="Force update of all packages")
    parser.add_argument("--no-public", action="store_true", help="Don't make objects publicly accessible")
    parser.add_argument("--print-url", action="store_true", help="Print the pypiserver URL with cache mapping")

    args = parser.parse_args()

    # Create the handler
    handler = GCSRedirectionHandler(
        pypiserver_url=args.pypiserver,
        packages_dir=args.packages_dir,
        bucket_name=args.bucket,
        object_prefix=args.prefix,
        cache_file=args.cache_file,
        public=not args.no_public
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
Example Google Cloud Storage integration for PyPIServer redirection

This extends the RedirectionHandler with a GCS-specific implementation.
"""

import os
import sys
from google.cloud import storage
import logging

from ..redirect_handler import RedirectionHandler

logger = logging.getLogger(__name__)

class GCSRedirectionHandler(RedirectionHandler):
    """
    Extends RedirectionHandler with Google Cloud Storage specific functionality
    """

    def __init__(self, 
                 pypiserver_url: str, 
                 packages_dir: str, 
                 bucket_name: str,
                 object_prefix: str = "packages/",
                 cache_file: str = None,
                 public: bool = True):
        """
        Initialize GCS redirection handler

        Args:
            pypiserver_url: The base URL of your pypiserver instance
            packages_dir: Local directory where packages are stored
            bucket_name: Name of the GCS bucket
            object_prefix: Prefix for objects in the bucket (default: "packages/")
            cache_file: Optional file to persist the cache mapping
            public: Whether to make uploaded objects publicly accessible
        """
        # GCS specific settings
        self.bucket_name = bucket_name
        self.object_prefix = object_prefix.rstrip("/") + "/"
        self.public = public

        # Initialize GCS client
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(bucket_name)

        # Calculate the CDN base URL for GCS
        cdn_base_url = f"https://storage.googleapis.com/{self.bucket_name}/{self.object_prefix}"

        # Initialize the parent class
        super().__init__(pypiserver_url, packages_dir, cdn_base_url, cache_file)

    def upload_to_cdn(self, package_path: str) -> str:
        """
        Upload a package to Google Cloud Storage bucket

        Args:
            package_path: Path to the package file to upload

        Returns:
            The URL where the package can be accessed
        """
        filename = os.path.basename(package_path)
        object_name = f"{self.object_prefix}{filename}"

        # Create a blob
        blob = self.bucket.blob(object_name)

        # Upload the file
        try:
            logger.info(f"Uploading {filename} to GCS bucket {self.bucket_name}")
            blob.upload_from_filename(package_path)

            # Make the blob publicly accessible if requested
            if self.public:
                blob.make_public()

            logger.info(f"Successfully uploaded {filename} to GCS")
        except Exception as e:
            logger.error(f"Failed to upload {filename} to GCS: {e}")
            raise

        # Return the URL
        return f"{self.cdn_base_url}{filename}"


def main():
    """
    Example usage of the GCSRedirectionHandler
    """
    import argparse

    parser = argparse.ArgumentParser(description="Manage package redirection for pypiserver using Google Cloud Storage")
    parser.add_argument("--pypiserver", default="http://localhost:8080", help="PyPI server URL")
    parser.add_argument("--packages-dir", default="./packages", help="Directory containing packages")
    parser.add_argument("--bucket", required=True, help="GCS bucket name")
    parser.add_argument("--prefix", default="packages/", help="Object prefix in GCS bucket")
    parser.add_argument("--cache-file", default="gcs_redirect_cache.json", help="File to store cache mapping")
    parser.add_argument("--force-update", action="store_true", help="Force update of all packages")
    parser.add_argument("--no-public", action="store_true", help="Don't make objects publicly accessible")
    parser.add_argument("--print-url", action="store_true", help="Print the pypiserver URL with cache mapping")

    args = parser.parse_args()

    # Create the handler
    handler = GCSRedirectionHandler(
        pypiserver_url=args.pypiserver,
        packages_dir=args.packages_dir,
        bucket_name=args.bucket,
        object_prefix=args.prefix,
        cache_file=args.cache_file,
        public=not args.no_public
    )
#!/usr/bin/env python

"""
Example Google Cloud Storage integration for PyPIServer redirection

This extends the RedirectionHandler with a GCS-specific implementation.
"""

import os
import sys
import logging
from google.cloud import storage

# Add the parent directory to the path so we can import the RedirectionHandler
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pypiserver_redirection.redirect_handler import RedirectionHandler

logger = logging.getLogger(__name__)

class GCSRedirectionHandler(RedirectionHandler):
    """
    Extends RedirectionHandler with Google Cloud Storage specific functionality
    """

    def __init__(self, 
                 pypiserver_url: str, 
                 packages_dir: str, 
                 bucket_name: str,
                 object_prefix: str = "packages/",
                 cache_file: str = None,
                 public: bool = True):
        """
        Initialize GCS redirection handler

        Args:
            pypiserver_url: The base URL of your pypiserver instance
            packages_dir: Local directory where packages are stored
            bucket_name: Name of the GCS bucket
            object_prefix: Prefix for objects in the bucket (default: "packages/")
            cache_file: Optional file to persist the cache mapping
            public: Whether to make uploaded objects publicly accessible
        """
        # GCS specific settings
        self.bucket_name = bucket_name
        self.object_prefix = object_prefix.rstrip("/") + "/"
        self.public = public

        # Initialize GCS client
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(bucket_name)

        # Calculate the CDN base URL for GCS
        cdn_base_url = f"https://storage.googleapis.com/{self.bucket_name}/{self.object_prefix}"

        # Initialize the parent class
        super().__init__(pypiserver_url, packages_dir, cdn_base_url, cache_file)

    def upload_to_cdn(self, package_path: str) -> str:
        """
        Upload a package to Google Cloud Storage bucket

        Args:
            package_path: Path to the package file to upload

        Returns:
            The URL where the package can be accessed
        """
        filename = os.path.basename(package_path)
        object_name = f"{self.object_prefix}{filename}"

        # Create a blob
        blob = self.bucket.blob(object_name)

        # Upload the file
        try:
            logger.info(f"Uploading {filename} to GCS bucket {self.bucket_name}")
            blob.upload_from_filename(package_path)

            # Make the blob publicly accessible if requested
            if self.public:
                blob.make_public()

            logger.info(f"Successfully uploaded {filename} to GCS")
        except Exception as e:
            logger.error(f"Failed to upload {filename} to GCS: {e}")
            raise

        # Return the URL
        return f"{self.cdn_base_url}{filename}"


def main():
    """
    Example usage of the GCSRedirectionHandler
    """
    import argparse

    parser = argparse.ArgumentParser(description="Manage package redirection for pypiserver using Google Cloud Storage")
    parser.add_argument("--pypiserver", default="http://localhost:8080", help="PyPI server URL")
    parser.add_argument("--packages-dir", default="./packages", help="Directory containing packages")
    parser.add_argument("--bucket", required=True, help="GCS bucket name")
    parser.add_argument("--prefix", default="packages/", help="Object prefix in GCS bucket")
    parser.add_argument("--cache-file", default="gcs_redirect_cache.json", help="File to store cache mapping")
    parser.add_argument("--force-update", action="store_true", help="Force update of all packages")
    parser.add_argument("--no-public", action="store_true", help="Don't make objects publicly accessible")
    parser.add_argument("--print-url", action="store_true", help="Print the pypiserver URL with cache mapping")

    args = parser.parse_args()

    # Create the handler
    handler = GCSRedirectionHandler(
        pypiserver_url=args.pypiserver,
        packages_dir=args.packages_dir,
        bucket_name=args.bucket,
        object_prefix=args.prefix,
        cache_file=args.cache_file,
        public=not args.no_public
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

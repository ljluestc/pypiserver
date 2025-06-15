#!/usr/bin/env python

"""
Example AWS S3 integration for PyPIServer redirection

This extends the RedirectionHandler with an S3-specific implementation.
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError
import logging

from ..redirect_handler import RedirectionHandler

logger = logging.getLogger(__name__)

class S3RedirectionHandler(RedirectionHandler):
    """
    Extends RedirectionHandler with AWS S3 specific functionality
    """

    def __init__(self, 
                 pypiserver_url: str, 
                 packages_dir: str, 
                 bucket_name: str,
                 object_prefix: str = "packages/",
                 region_name: str = "us-east-1",
                 cache_file: str = None,
                 public_read: bool = True):
        """
        Initialize S3 redirection handler

        Args:
            pypiserver_url: The base URL of your pypiserver instance
            packages_dir: Local directory where packages are stored
            bucket_name: Name of the S3 bucket
            object_prefix: Prefix for objects in the bucket (default: "packages/")
            region_name: AWS region name (default: "us-east-1")
            cache_file: Optional file to persist the cache mapping
            public_read: Whether to set public-read ACL on uploads
        """
        # S3 specific settings
        self.bucket_name = bucket_name
        self.object_prefix = object_prefix.rstrip("/") + "/"
        self.region_name = region_name
        self.public_read = public_read

        # Initialize S3 client
        self.s3_client = boto3.client('s3', region_name=self.region_name)

        # Calculate the CDN base URL for S3
        cdn_base_url = f"https://{self.bucket_name}.s3.amazonaws.com/{self.object_prefix}"

        # Initialize the parent class
        super().__init__(pypiserver_url, packages_dir, cdn_base_url, cache_file)

    def upload_to_cdn(self, package_path: str) -> str:
        """
        Upload a package to AWS S3 bucket

        Args:
            package_path: Path to the package file to upload
#!/usr/bin/env python

"""
Example AWS S3 integration for PyPIServer redirection

This extends the RedirectionHandler with an S3-specific implementation.
"""

import os
import sys
import boto3
import logging

# Import from parent module
from pypiserver_redirection import RedirectionHandler

logger = logging.getLogger(__name__)

class S3RedirectionHandler(RedirectionHandler):
    """
    Extends RedirectionHandler with AWS S3 specific functionality
    """

    def __init__(self, 
                 pypiserver_url: str, 
                 packages_dir: str, 
                 bucket_name: str,
                 object_prefix: str = "packages/",
                 region_name: str = None,
                 cache_file: str = None,
                 public: bool = True):
        """
        Initialize S3 redirection handler

        Args:
            pypiserver_url: The base URL of your pypiserver instance
            packages_dir: Local directory where packages are stored
            bucket_name: Name of the S3 bucket
            object_prefix: Prefix for objects in the bucket (default: "packages/")
            region_name: AWS region name
            cache_file: Optional file to persist the cache mapping
            public: Whether to make uploaded objects publicly accessible
        """
        # S3 specific settings
        self.bucket_name = bucket_name
        self.object_prefix = object_prefix.rstrip("/") + "/"
        self.public = public

        # Initialize S3 client
        self.s3_client = boto3.client('s3', region_name=region_name)

        # Calculate the CDN base URL for S3
        if region_name and region_name != 'us-east-1':
            cdn_base_url = f"https://{bucket_name}.s3.{region_name}.amazonaws.com/{self.object_prefix}"
        else:
            cdn_base_url = f"https://{bucket_name}.s3.amazonaws.com/{self.object_prefix}"

        # Initialize the parent class
        super().__init__(pypiserver_url, packages_dir, cdn_base_url, cache_file)

    def upload_to_cdn(self, package_path: str) -> str:
        """
        Upload a package to AWS S3 bucket

        Args:
            package_path: Path to the package file to upload

        Returns:
            The URL where the package can be accessed
        """
        filename = os.path.basename(package_path)
        object_name = f"{self.object_prefix}{filename}"

        # Set the ACL based on the public setting
        extra_args = {}
        if self.public:
            extra_args['ACL'] = 'public-read'

        # Upload the file
        try:
            logger.info(f"Uploading {filename} to S3 bucket {self.bucket_name}")
            with open(package_path, 'rb') as file_obj:
                self.s3_client.upload_fileobj(
                    file_obj, 
                    self.bucket_name, 
                    object_name,
                    ExtraArgs=extra_args
                )
            logger.info(f"Successfully uploaded {filename} to S3")
        except Exception as e:
            logger.error(f"Failed to upload {filename} to S3: {e}")
            raise

        # Return the URL
        return f"{self.cdn_base_url}{filename}"


def main():
    """
    Example usage of the S3RedirectionHandler
    """
    import argparse

    parser = argparse.ArgumentParser(description="Manage package redirection for pypiserver using AWS S3")
    parser.add_argument("--pypiserver", default="http://localhost:8080", help="PyPI server URL")
    parser.add_argument("--packages-dir", default="./packages", help="Directory containing packages")
    parser.add_argument("--bucket", required=True, help="S3 bucket name")
    parser.add_argument("--prefix", default="packages/", help="Object prefix in S3 bucket")
    parser.add_argument("--region", help="AWS region name")
    parser.add_argument("--cache-file", default="s3_redirect_cache.json", help="File to store cache mapping")
    parser.add_argument("--force-update", action="store_true", help="Force update of all packages")
    parser.add_argument("--no-public", action="store_true", help="Don't make objects publicly accessible")
    parser.add_argument("--print-url", action="store_true", help="Print the pypiserver URL with cache mapping")

    args = parser.parse_args()

    # Create the handler
    handler = S3RedirectionHandler(
        pypiserver_url=args.pypiserver,
        packages_dir=args.packages_dir,
        bucket_name=args.bucket,
        object_prefix=args.prefix,
        region_name=args.region,
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
        Returns:
            The URL where the package can be accessed
        """
        filename = os.path.basename(package_path)
        object_name = f"{self.object_prefix}{filename}"

        # Set extra args for upload
        extra_args = {}
        if self.public_read:
            extra_args['ACL'] = 'public-read'

        # Upload the file
        try:
            logger.info(f"Uploading {filename} to S3 bucket {self.bucket_name}")
            self.s3_client.upload_file(
                package_path, 
                self.bucket_name, 
                object_name,
                ExtraArgs=extra_args
            )
            logger.info(f"Successfully uploaded {filename} to S3")
        except ClientError as e:
            logger.error(f"Failed to upload {filename} to S3: {e}")
            raise

        # Return the URL
        return f"{self.cdn_base_url}{filename}"


def main():
    """
    Example usage of the S3RedirectionHandler
    """
    import argparse

    parser = argparse.ArgumentParser(description="Manage package redirection for pypiserver using AWS S3")
    parser.add_argument("--pypiserver", default="http://localhost:8080", help="PyPI server URL")
    parser.add_argument("--packages-dir", default="./packages", help="Directory containing packages")
    parser.add_argument("--bucket", required=True, help="S3 bucket name")
    parser.add_argument("--prefix", default="packages/", help="Object prefix in S3 bucket")
    parser.add_argument("--region", default="us-east-1", help="AWS region name")
    parser.add_argument("--cache-file", default="s3_redirect_cache.json", help="File to store cache mapping")
    parser.add_argument("--force-update", action="store_true", help="Force update of all packages")
    parser.add_argument("--no-public-read", action="store_true", help="Don't set public-read ACL on uploads")
    parser.add_argument("--print-url", action="store_true", help="Print the pypiserver URL with cache mapping")
#!/usr/bin/env python

"""
Example AWS S3 integration for PyPIServer redirection

This extends the RedirectionHandler with an S3-specific implementation.
"""

import os
import sys
import logging
import boto3
from botocore.exceptions import ClientError

# Add the parent directory to the path so we can import the RedirectionHandler
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pypiserver_redirection.redirect_handler import RedirectionHandler

logger = logging.getLogger(__name__)


class S3RedirectionHandler(RedirectionHandler):
    """
    Extends RedirectionHandler with AWS S3 specific functionality
    """

    def __init__(self,
                 pypiserver_url: str,
                 packages_dir: str,
                 bucket_name: str,
                 object_prefix: str = "packages/",
                 region_name: str = "us-east-1",
                 cache_file: str = None,
                 public_read: bool = True):
        """
        Initialize S3 redirection handler

        Args:
            pypiserver_url: The base URL of your pypiserver instance
            packages_dir: Local directory where packages are stored
            bucket_name: Name of the S3 bucket
            object_prefix: Prefix for objects in the bucket (default: "packages/")
            region_name: AWS region name
            cache_file: Optional file to persist the cache mapping
            public_read: Whether to make uploaded objects publicly readable
        """
        # S3 specific settings
        self.bucket_name = bucket_name
        self.object_prefix = object_prefix.rstrip("/") + "/"
        self.region_name = region_name
        self.public_read = public_read

        # Initialize S3 client
        self.s3_client = boto3.client('s3', region_name=region_name)

        # Calculate the CDN base URL for S3
        cdn_base_url = f"https://{bucket_name}.s3.amazonaws.com/{self.object_prefix}"

        # Initialize the parent class
        super().__init__(pypiserver_url, packages_dir, cdn_base_url, cache_file)

    def upload_to_cdn(self, package_path: str) -> str:
        """
        Upload a package to S3 bucket

        Args:
            package_path: Path to the package file to upload

        Returns:
            The URL where the package can be accessed
        """
        filename = os.path.basename(package_path)
        object_name = f"{self.object_prefix}{filename}"

        # Set extra arguments for upload
        extra_args = {}
        if self.public_read:
            extra_args['ACL'] = 'public-read'

        # Upload the file
        try:
            logger.info(f"Uploading {filename} to S3 bucket {self.bucket_name}")
            self.s3_client.upload_file(
                package_path,
                self.bucket_name,
                object_name,
                ExtraArgs=extra_args
            )
            logger.info(f"Successfully uploaded {filename} to S3")
        except ClientError as e:
            logger.error(f"Failed to upload {filename} to S3: {e}")
            raise

        # Return the URL
        return f"{self.cdn_base_url}{filename}"


def main():
    """
    Example usage of the S3RedirectionHandler
    """
    import argparse

    parser = argparse.ArgumentParser(description="Manage package redirection for pypiserver using AWS S3")
    parser.add_argument("--pypiserver", default="http://localhost:8080", help="PyPI server URL")
    parser.add_argument("--packages-dir", default="./packages", help="Directory containing packages")
    parser.add_argument("--bucket", required=True, help="S3 bucket name")
    parser.add_argument("--prefix", default="packages/", help="Object prefix in S3 bucket")
    parser.add_argument("--region", default="us-east-1", help="AWS region name")
    parser.add_argument("--cache-file", default="s3_redirect_cache.json", help="File to store cache mapping")
    parser.add_argument("--force-update", action="store_true", help="Force update of all packages")
    parser.add_argument("--no-public", action="store_true", help="Don't set public-read ACL")
    parser.add_argument("--print-url", action="store_true", help="Print the pypiserver URL with cache mapping")

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Create the handler
    handler = S3RedirectionHandler(
        pypiserver_url=args.pypiserver,
        packages_dir=args.packages_dir,
        bucket_name=args.bucket,
        object_prefix=args.prefix,
        region_name=args.region,
        cache_file=args.cache_file,
        public_read=not args.no_public
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
    args = parser.parse_args()

    # Create the handler
    handler = S3RedirectionHandler(
        pypiserver_url=args.pypiserver,
        packages_dir=args.packages_dir,
        bucket_name=args.bucket,
        object_prefix=args.prefix,
        region_name=args.region,
        cache_file=args.cache_file,
        public_read=not args.no_public_read
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

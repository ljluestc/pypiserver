#!/usr/bin/env python
"""
Example script to demonstrate how to use the redirection feature with pypiserver.

This script shows how to upload packages to a CDN or other storage service and
then configure pypiserver to redirect requests to those external URLs while
maintaining the package index.
"""

import json
import os
import sys
import time
import logging
from urllib.parse import quote
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration
PYPISERVER_URL = "http://localhost:8080"  # Your pypiserver URL
PACKAGES_DIR = "./packages"  # Local directory with packages
CDN_BASE_URL = "https://example-cdn.com/packages/"  # Your CDN or storage URL
CACHE_FILE = "redirect_cache.json"  # File to store the cache mapping


def upload_to_cdn(package_path):
    """
    Upload a package to a CDN or storage service.
    This is a placeholder function - implement your actual upload logic here.

    Returns the URL where the package can be accessed.
    """
    # This is a mock implementation - replace with your actual upload code
    filename = os.path.basename(package_path)
    logger.info(f"Uploading {filename} to CDN")

    # Simulate upload delay
    time.sleep(0.1)

    return f"{CDN_BASE_URL}{filename}"


def create_cache_mapping(force_update=False):
    """
    Create a mapping of package filenames to their CDN URLs.

    Args:
        force_update: If True, update all packages even if they're already in cache
    """
    cache_mapping = {}

    # Load existing cache if available
    if os.path.exists(CACHE_FILE) and not force_update:
        try:
            with open(CACHE_FILE, 'r') as f:
                cache_mapping = json.load(f)
            logger.info(f"Loaded {len(cache_mapping)} entries from cache file")
        except json.JSONDecodeError:
            logger.error(f"Failed to parse cache file {CACHE_FILE}")

    # List all packages in the directory
    logger.info(f"Scanning packages in {PACKAGES_DIR}")
    for filename in os.listdir(PACKAGES_DIR):
        if filename.endswith((".whl", ".tar.gz", ".zip", ".egg")):
            full_path = os.path.join(PACKAGES_DIR, filename)

            # Skip if already in cache and not forcing update
            if filename in cache_mapping and not force_update:
                logger.debug(f"Skipping {filename} (already in cache)")
                continue

            # Upload to CDN and get the URL
            cdn_url = upload_to_cdn(full_path)

            # Add to mapping
            cache_mapping[filename] = cdn_url
            logger.info(f"Added {filename} -> {cdn_url}")

    # Save the cache
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache_mapping, f, indent=2)
    logger.info(f"Saved cache mapping to {CACHE_FILE}")

    return cache_mapping


def query_pypiserver_with_cache(cache_mapping):
    """
    Query pypiserver with the cache mapping to get redirectable links.

    Args:
        cache_mapping: Dictionary mapping filenames to CDN URLs
    """
    # Convert the mapping to a JSON string and URL encode it
    cache_json = json.dumps(cache_mapping)
    encoded_cache = quote(cache_json)

    # Build the URLs with the cache parameter
    packages_url = f"{PYPISERVER_URL}/packages/?cached_links={encoded_cache}"
    simple_url = f"{PYPISERVER_URL}/simple/?cached_links={encoded_cache}"

    # Make the request
    try:
        response = requests.get(packages_url)
        if response.status_code == 200:
            logger.info(f"Successfully queried packages with cache mapping")
            return {
                "packages_url": packages_url,
                "simple_url": simple_url
            }
        else:
            logger.error(f"Failed to query packages: {response.status_code}")
            return None
    except requests.RequestException as e:
        logger.error(f"Request error: {e}")
        return None


def verify_redirection(cache_mapping, package_name=None):
    """
    Verify that redirection is working for a specific package.

    Args:
        cache_mapping: Dictionary mapping filenames to CDN URLs
        package_name: Optional specific package to test
    """
    if not package_name and cache_mapping:
        # Use the first package in the cache
        package_name = next(iter(cache_mapping.keys()))

    if not package_name:
        logger.error("No package available to test redirection")
        return False

    # Get the URL for the package
    cache_json = json.dumps(cache_mapping)
    encoded_cache = quote(cache_json)
    package_url = f"{PYPISERVER_URL}/packages/{package_name}?cached_links={encoded_cache}"

    # Make the request with allow_redirects=False to see the redirect
    try:
        response = requests.get(package_url, allow_redirects=False)

        if response.status_code in (301, 302, 303, 307):
            redirect_url = response.headers.get('Location')
            if redirect_url and redirect_url == cache_mapping.get(package_name):
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
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description="Demonstrate PyPIServer redirection")
    parser.add_argument("--pypiserver", default=PYPISERVER_URL, help="PyPI server URL")
    parser.add_argument("--packages-dir", default=PACKAGES_DIR, help="Directory containing packages")
    parser.add_argument("--cdn-url", default=CDN_BASE_URL, help="Base URL of CDN or storage service")
    parser.add_argument("--cache-file", default=CACHE_FILE, help="File to store cache mapping")
    parser.add_argument("--force-update", action="store_true", help="Force update of all packages")
    parser.add_argument("--verify", action="store_true", help="Verify redirection works")

    args = parser.parse_args()

    # Update globals with command line arguments
    global PYPISERVER_URL, PACKAGES_DIR, CDN_BASE_URL, CACHE_FILE
    PYPISERVER_URL = args.pypiserver
    PACKAGES_DIR = args.packages_dir
    CDN_BASE_URL = args.cdn_url
    CACHE_FILE = args.cache_file

    # Create the cache mapping
    logger.info("Creating cache mapping...")
    cache_mapping = create_cache_mapping(force_update=args.force_update)
    logger.info(f"Created mapping for {len(cache_mapping)} packages")

    # Use the cache mapping with pypiserver
    logger.info("Querying pypiserver with cache mapping...")
    urls = query_pypiserver_with_cache(cache_mapping)

    if urls:
        print("\nPypiserver URLs with cache mapping:")
        print(f"Simple index: {urls['simple_url']}")
        print(f"Packages index: {urls['packages_url']}")
        print("\nTo use with pip:")
        print(f"pip install --extra-index-url {urls['simple_url']} <package>")

    # Verify redirection if requested
    if args.verify:
        logger.info("Verifying redirection...")
        if verify_redirection(cache_mapping):
            print("\nRedirection verified successfully!")
        else:
            print("\nRedirection verification failed!")


if __name__ == "__main__":
    main()

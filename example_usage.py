#!/usr/bin/env python

"""
Example script demonstrating how to use the redirection feature with PyPIServer.

This script shows the complete workflow:
1. Set up the PyPIServer instance
2. Upload packages to an external storage
3. Create a cache mapping
4. Use pip with the redirected URLs
"""

import os
import subprocess
import sys
import time
import tempfile
import shutil
from urllib.parse import quote

from redirect_handler import RedirectionHandler

# Configuration
PYPISERVER_PORT = 8080
PACKAGES_DIR = "./packages"
TEST_PACKAGE = "example_package-0.1.0.tar.gz"


def ensure_packages_dir():
    """Create packages directory if it doesn't exist"""
    if not os.path.exists(PACKAGES_DIR):
        os.makedirs(PACKAGES_DIR)
        print(f"Created packages directory: {PACKAGES_DIR}")


def create_test_package():
    """Create a simple test package"""
    if not os.path.exists(PACKAGES_DIR):
        os.makedirs(PACKAGES_DIR)

    # Create a temporary directory for the package
    with tempfile.TemporaryDirectory() as temp_dir:
        package_dir = os.path.join(temp_dir, "example_package")
        os.makedirs(package_dir)

        # Create a simple setup.py
        with open(os.path.join(package_dir, "setup.py"), "w") as f:
            f.write("""\
from setuptools import setup

setup(
    name="example_package",
    version="0.1.0",
    description="An example package for testing PyPIServer redirection",
    author="Example Author",
    author_email="example@example.com",
    packages=[],
)
""")

        # Create an empty __init__.py
        with open(os.path.join(package_dir, "__init__.py"), "w") as f:
            f.write("")

        # Build the package
        subprocess.run(
            [sys.executable, "setup.py", "sdist"],
            cwd=package_dir,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Copy the package to the packages directory
        src = os.path.join(package_dir, "dist", TEST_PACKAGE)
        dst = os.path.join(PACKAGES_DIR, TEST_PACKAGE)
        shutil.copy(src, dst)
        print(f"Created test package: {dst}")


def start_pypiserver():
    """Start PyPIServer as a subprocess"""
    cmd = [
        sys.executable, "-m", "pypiserver", "run",
        f"--port={PYPISERVER_PORT}",
        PACKAGES_DIR
    ]

    print(f"Starting PyPIServer: {' '.join(cmd)}")
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Give the server a moment to start
    time.sleep(2)

    return process


def run_redirection_handler():
    """Run the redirection handler to create a cache mapping"""
    # Use a simple local directory as our "CDN"
    cdn_dir = "./cdn_files"
    if not os.path.exists(cdn_dir):
        os.makedirs(cdn_dir)

    # Create a custom redirection handler that just copies files to our CDN directory
    class LocalRedirectionHandler(RedirectionHandler):
        def upload_to_cdn(self, package_path):
            filename = os.path.basename(package_path)
            dst_path = os.path.join(cdn_dir, filename)
            shutil.copy(package_path, dst_path)
            return f"{self.cdn_base_url}{filename}"

    # Initialize the handler
    handler = LocalRedirectionHandler(
        pypiserver_url=f"http://localhost:{PYPISERVER_PORT}",
        packages_dir=PACKAGES_DIR,
        cdn_base_url=f"file://{os.path.abspath(cdn_dir)}/",
        cache_file="local_redirect_cache.json"
    )

    # Update the cache mapping
    handler.update_cache_mapping(force_update=True)

    # Get the URL with cache mapping
    simple_url = handler.get_pypiserver_url_with_cache("simple")
    print(f"\nRedirection URL: {simple_url}")

    return simple_url


def test_pip_install(redirection_url):
    """Test installing a package with pip using the redirection URL"""
    # Create a temporary virtual environment
    with tempfile.TemporaryDirectory() as venv_dir:
        # Create the virtual environment
        subprocess.run(
            [sys.executable, "-m", "venv", venv_dir],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Determine the pip executable path
        if sys.platform == "win32":
            pip_path = os.path.join(venv_dir, "Scripts", "pip.exe")
        else:
            pip_path = os.path.join(venv_dir, "bin", "pip")

        # Try to install the package using the redirection URL
        print(f"\nTesting pip install with redirection...")
        result = subprocess.run(
            [
                pip_path, "install", 
                "--extra-index-url", redirection_url,
                "--no-cache-dir",
                "example_package"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        print(result.stdout)
        if result.stderr:
            print(f"Errors: {result.stderr}")

        if result.returncode == 0:
            print("Successfully installed package using redirection!")
        else:
            print("Failed to install package using redirection.")


def main():
    """Run the complete example"""
    print("=== PyPIServer Redirection Example ===")

    # Ensure we have the packages directory
    ensure_packages_dir()

    # Create a test package if needed
    if not os.path.exists(os.path.join(PACKAGES_DIR, TEST_PACKAGE)):
        create_test_package()

    # Start PyPIServer
    server_process = start_pypiserver()

    try:
        # Set up redirection
        redirection_url = run_redirection_handler()

        # Test pip install
        test_pip_install(redirection_url)
    finally:
        # Clean up
        print("\nShutting down PyPIServer...")
        server_process.terminate()
        server_process.wait()


if __name__ == "__main__":
    main()

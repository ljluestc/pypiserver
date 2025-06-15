# Package Redirection for PyPIServer

This documentation explains how to use PyPIServer's redirection feature to serve package links from external sources like CDNs or storage services.

## Overview

PyPIServer supports redirecting package download requests to external URLs. This allows you to:

1. Host your actual package files on a CDN or storage service for better performance
2. Keep using PyPIServer for package indexing and authentication
3. Reduce bandwidth and storage requirements on your PyPIServer host

## How It Works

The redirection system uses a cache mapping mechanism:

1. You upload packages to an external service (CDN, S3, etc.)
2. You create a mapping between package filenames and their external URLs
3. You include this mapping when accessing PyPIServer by appending a `cached_links` parameter
4. When a client requests a package, PyPIServer redirects to the external URL instead of serving the file directly

## Using the Redirection Handler

This repository includes a `redirect_handler.py` script that helps manage this process:

```bash
# Basic usage (with defaults)
python redirect_handler.py

# Customized usage
python redirect_handler.py \
  --pypiserver http://your-pypiserver.com \
  --packages-dir /path/to/packages \
  --cdn-url https://your-cdn.com/packages/ \
  --cache-file cache.json \
  --force-update \
  --print-url
```

### Configuration Options

- `--pypiserver`: URL of your PyPIServer instance
- `--packages-dir`: Directory containing your packages
- `--cdn-url`: Base URL of your CDN or storage service
- `--cache-file`: File to store the cache mapping
- `--force-update`: Force update of all packages (even if already in cache)
- `--print-url`: Print the PyPIServer URL with cache mapping

## Using with pip

Once you have your cache mapping set up, you can use pip with the extra-index-url option:

```bash
# Use the URL printed by the redirect_handler.py script
pip install --extra-index-url "http://your-pypiserver.com/simple/?cached_links=%7B...%7D" package-name
```

## Implementation Details

The `redirect_handler.py` script:

1. Scans your packages directory for packages
2. Uploads packages to your CDN (you need to customize this part)
3. Creates a mapping between filenames and CDN URLs
4. Encodes this mapping for use with PyPIServer
5. Provides URLs you can use with pip

## Customizing the Upload Process

The script includes a placeholder `upload_to_cdn` method that you should customize to work with your specific storage service. For example, to use with AWS S3:

```python
def upload_to_cdn(self, package_path: str) -> str:
    """Upload a package to S3"""
    import boto3
    s3 = boto3.client('s3')
    bucket_name = 'your-bucket'
    filename = os.path.basename(package_path)
    object_name = f"packages/{filename}"

    # Upload the file
    s3.upload_file(package_path, bucket_name, object_name)

    # Return the URL
    return f"https://{bucket_name}.s3.amazonaws.com/{object_name}"
```

## Caching Strategy

The script maintains a cache file to avoid re-uploading packages that have already been processed. This makes subsequent runs much faster. You can force a full update with the `--force-update` flag.

## Security Considerations

- Make sure your CDN or storage service has proper access controls
- Consider using signed URLs if you need to control access to packages
- Continue using authentication on PyPIServer for upload protection

## Limitations

- The cache mapping must be included in the URL, which can become large for many packages
- Each client needs to use the URL with the cache parameter
- The redirection URLs need to be updated when packages change

## Further Resources

For more information, see the `examples/cache_external_links.py` file in the PyPIServer repository.

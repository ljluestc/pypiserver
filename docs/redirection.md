# External Package Redirection

## Overview

PypiServer now supports redirection to external URLs for package downloads. This feature allows you to:

1. Host your package files on an external CDN or storage service
2. Maintain the package index in pypiserver
3. Redirect download requests to the external locations

This approach gives you the best of both worlds: pypiserver's simple package indexing and authentication, with the scalability and performance of external storage services.

## How It Works

The redirection system works by accepting a cache mapping in the query string when accessing package listings. When a package is requested, pypiserver will check if there's a corresponding external URL and redirect the client to that URL instead of serving the file directly.

### Workflow

1. Upload your packages to an external service (CDN, S3, etc.)
2. Create a mapping of package filenames to their external URLs
3. Include this mapping when querying pypiserver
4. When a client requests a package, pypiserver redirects to the external URL

## Usage

### Creating the Cache Mapping

The cache mapping is a JSON object where keys are package filenames and values are the external URLs:

```json
{
  "package-1.0.0.whl": "https://cdn.example.com/packages/package-1.0.0.whl",
  "library-2.1.0.tar.gz": "https://cdn.example.com/packages/library-2.1.0.tar.gz"
}
```

### Using the Cache Mapping

To use the cache mapping, URL-encode it and include it as the `cached_links` parameter when accessing pypiserver:

```
http://your-pypiserver.com/packages/?cached_links=%7B%22package-1.0.0.whl%22%3A%22https%3A%2F%2Fcdn.example.com%2Fpackages%2Fpackage-1.0.0.whl%22%7D
```

This also works with the `/simple/` endpoint:

```
http://your-pypiserver.com/simple/package/?cached_links=%7B%22package-1.0.0.whl%22%3A%22https%3A%2F%2Fcdn.example.com%2Fpackages%2Fpackage-1.0.0.whl%22%7D
```

### Example Script

An example script for implementing this workflow is included in the `examples` directory: `cache_external_links.py`. This script demonstrates:

1. Uploading packages to a CDN (simulated)
2. Creating the cache mapping
3. Querying pypiserver with the cache mapping

## Benefits

- **Performance**: Offload bandwidth-intensive downloads to specialized services
- **Cost**: Potentially reduce hosting costs by using optimized storage services
- **Flexibility**: Keep your pypiserver instance light while serving large files externally
- **Security**: Maintain pypiserver's authentication while storing files elsewhere

## Caching Strategies

There are several approaches to managing the cache mapping:

1. **Generate on-demand**: Create the mapping when needed, such as during deployment
2. **Store persistently**: Save the mapping to a file and update it when packages change
3. **Service integration**: Have your CDN or storage service provide an API for generating the mapping

Choose the approach that best fits your workflow and update frequency.

## Limitations

- The cache mapping must be included in the URL, which may have length limitations in some environments
- For security reasons, always validate external URLs before including them in your cache mapping
- This feature is best used with trusted CDNs or storage services

## Example Implementation

See the included `examples/cache_external_links.py` script for a complete implementation example.

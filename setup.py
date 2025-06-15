#!/usr/bin/env python
"""
Fallback setup.py for older pip versions.
All package configuration is in pyproject.toml.
"""

from setuptools import setup

# Using setup.py for backward compatibility
# Modern installations should use pyproject.toml
setup()
import re
from pathlib import Path

from setuptools import setup, find_packages

tests_require = [
    "pytest>=2.3",
    "tox",
    "twine",
    "passlib>=1.6",
    "webtest",
    "build>=1.2.0;python_version>='3.8'",
]

setup_requires = [
    "setuptools",
    "setuptools-git>=0.3",
    "wheel>=0.25.0",
]
install_requires = [
    "pip>=7",
    "packaging>=23.2",
    "importlib_resources;python_version>'3.8' and python_version<'3.12'",
]
#!/usr/bin/env python

"""
Fallback setup.py for older pip versions that don't support pyproject.toml.
Modern installations should use the pyproject.toml file.
"""

from setuptools import setup, find_packages

setup(
    name="pypiserver-redirection",
    version="0.1.0",
    description="PyPIServer extension for redirecting package downloads to external URLs",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="PyPIServer Contributors",
    author_email="pypiserver@example.com",
    url="https://github.com/pypiserver/pypiserver-redirection",
    packages=["pypiserver_redirection", "pypiserver_redirection.cdn_config_examples"],
    install_requires=["pypiserver>=2.3.2", "requests>=2.28.0"],
    entry_points={"paste.app_factory": ["main=pypiserver:paste_app_factory"]},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.8",
)

def read_file(rel_path: str):
    return Path(__file__).parent.joinpath(rel_path).read_text()


def get_version():
    locals_ = {}
    version_line = re.compile(
        r'^[\w =]*__version__ = "\d+\.\d+\.\d+\.?\w*\d*"$'
    )
    try:
        for ln in filter(
            version_line.match,
            read_file("pypiserver/__init__.py").splitlines(),
        ):
            exec(ln, locals_)
    except (ImportError, RuntimeError):
        pass
    return locals_["__version__"]


setup(
    name="pypiserver",
    description="A minimal PyPI server for use with pip/easy_install.",
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    version=get_version(),
    packages=find_packages(include=["pypiserver", "pypiserver.*"]),
    package_data={"pypiserver": ["welcome.html"]},
    python_requires=">=3.8",
    install_requires=install_requires,
    setup_requires=setup_requires,
    extras_require={"passlib": ["passlib>=1.6"], "cache": ["watchdog"]},
    tests_require=tests_require,
    url="https://github.com/pypiserver/pypiserver",
    maintainer=(
        "Kostis Anagnostopoulos <ankostis@gmail.com>"
        "Matthew Planchard <mplanchard@gmail.com>"
    ),
    maintainer_email="ankostis@gmail.com",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: BSD License",
        "License :: OSI Approved :: zlib/libpng License",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Software Development :: Build Tools",
        "Topic :: System :: Software Distribution",
    ],
    zip_safe=True,
    entry_points={
        "paste.app_factory": ["main=pypiserver:paste_app_factory"],
        "console_scripts": ["pypi-server=pypiserver.__main__:main"],
    },
    platforms=["any"],
)

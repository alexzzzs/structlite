#!/usr/bin/env python3
"""Setup script for structlite package."""

import os

from setuptools import find_packages, setup


# Read the README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), "README.md")
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


# Read version from __init__.py
def get_version():
    version_file = os.path.join(os.path.dirname(__file__), "structlite", "__init__.py")
    if os.path.exists(version_file):
        with open(version_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("__version__"):
                    return line.split("=")[1].strip().strip("\"'")
    return "0.1.0"


setup(
    name="structlite",
    version=get_version(),
    author="Your Name",
    author_email="your.email@example.com",
    description="A powerful, flexible struct-like class for Python with validation, immutability, serialization, and more",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/structlite",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
        "Typing :: Typed",
    ],
    python_requires=">=3.8",
    install_requires=[
        # No external dependencies - pure Python!
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-asyncio>=0.18.0",
            "black>=22.0",
            "isort>=5.0",
            "mypy>=0.900",
            "flake8>=4.0",
        ],
        "test": [
            "pytest>=6.0",
            "pytest-asyncio>=0.18.0",
        ],
    },
    keywords="struct dataclass validation serialization immutable builder async",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/structlite/issues",
        "Source": "https://github.com/yourusername/structlite",
        "Documentation": "https://github.com/yourusername/structlite#readme",
    },
    include_package_data=True,
    zip_safe=False,
)

#!/usr/bin/env python3
"""
Setup script for Datash.
"""

import os
from setuptools import setup, find_packages

# Get version from version.py
VERSION = "0.1.0"

# Get the long description from the README file
with open("README.md", encoding="utf-8") as f:
    long_description = f.read()

# Core dependencies
REQUIRED = [
    "requests>=2.28.0,<3.0.0",     # HTTP requests for API
    "python-dotenv>=1.0.0,<2.0.0", # Environment variables
    "colorama>=0.4.4",             # Colored terminal output
]

# Platform-specific dependencies
EXTRAS = {
    "dev": [
        "pytest>=7.3.1",
        "pytest-cov>=4.1.0",
        "black>=23.3.0",
        "mypy>=1.3.0",
        "responses>=0.23.1",
    ],
    "windows": [
        "pyreadline3>=3.4.1",
    ],
    "unix": [
        "readline>=6.2.4.1",
    ],
    "db": [
        "mysql-connector-python>=8.3.0",
        "psycopg2-binary>=2.9.6",
        "pymongo>=4.4.0",
    ],
}

setup(
    name="datash",
    version=VERSION,
    description="A terminal assistant for programmers with AI-powered suggestions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Julio Campos Machado",
    author_email="juliocamposmachado@gmail.com",
    url="https://github.com/juliocamposmachado/datash",
    packages=find_packages(exclude=["tests", "tests.*"]),
    py_modules=["main"],
    install_requires=REQUIRED,
    extras_require=EXTRAS,
    entry_points={
        "console_scripts": [
            "datash=main:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    keywords="ai, assistant, terminal, bash, shell, programming",
    project_urls={
        "Documentation": "https://github.com/juliocamposmachado/datash",
        "Source": "https://github.com/juliocamposmachado/datash",
        "Issues": "https://github.com/juliocamposmachado/datash/issues",
    },
)


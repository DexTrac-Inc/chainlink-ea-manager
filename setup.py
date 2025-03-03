#!/usr/bin/env python3
"""
Setup script for the Chainlink EA Manager
"""

from setuptools import setup, find_packages

setup(
    name="chainlink-ea-manager",
    version="0.1.0",
    description="Chainlink External Adapter Manager",
    author="DexTrac Inc",
    author_email="info@dextrac.com",
    url="https://github.com/DexTrac-Inc/chainlink-ea-manager",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "ea-manager=chainlink_ea_manager.cli:main",
        ],
    },
    install_requires=[
        "docker>=5.0.0",
        "PyYAML>=6.0",
        "colorama>=0.4.4",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.7",
)
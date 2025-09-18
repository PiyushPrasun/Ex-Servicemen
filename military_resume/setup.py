#!/usr/bin/env python3
"""
Setup script for NeoResuMaker - Ex-Servicemen Resume Builder
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    requirements = []
    if os.path.exists(requirements_path):
        with open(requirements_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    requirements.append(line)
    return requirements

setup(
    name="neoresumaker",
    version="1.0.0",
    author="NeoResuMaker Team",
    author_email="contact@neoresumaker.com",
    description="AI-enhanced resume builder for military veterans transitioning to civilian careers",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/neoresumaker",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Office/Business :: Financial :: Accounting",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "ocr": [
            "pytesseract>=0.3.10",
            "Pillow>=10.0.0",
        ],
        "ai": [
            "mistralai>=0.4.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "neoresumaker=resume:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.md", "*.txt", "*.yml", "*.yaml"],
    },
    keywords="resume, military, veterans, AI, OCR, career-transition, streamlit",
    project_urls={
        "Bug Reports": "https://github.com/your-username/neoresumaker/issues",
        "Source": "https://github.com/your-username/neoresumaker",
        "Documentation": "https://github.com/your-username/neoresumaker/blob/main/README.md",
    },
)

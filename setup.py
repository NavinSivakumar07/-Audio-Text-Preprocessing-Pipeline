"""
Setup script for India Speaks Cleaner package.
"""

from setuptools import setup, find_packages
import os

# Read README file
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    try:
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "Preprocessing pipeline for Indic language audio-text data"

# Read requirements
def read_requirements():
    requirements_path = os.path.join(os.path.dirname(__file__), 'requirements.txt')
    try:
        with open(requirements_path, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        return ['pandas>=1.3.0', 'numpy>=1.21.0', 'torchaudio>=0.9.0', 'torch>=1.9.0']

setup(
    name='india-speaks-cleaner',
    version='1.0.0',
    author='India Speaks Team',
    author_email='team@indiaspeaks.ai',
    description='Preprocessing pipeline for Indic language audio-text data',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/indiaspeaks/audio-text-preprocessing',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Text Processing :: Linguistic',
        'Topic :: Multimedia :: Sound/Audio :: Speech',
    ],
    keywords='speech-processing asr tts indic-languages audio-preprocessing text-normalization',
    python_requires='>=3.8',
    install_requires=read_requirements(),
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.0',
            'black>=21.0',
            'flake8>=3.8',
            'mypy>=0.900',
        ],
        'docs': [
            'sphinx>=4.0',
            'sphinx-rtd-theme>=1.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'india_speaks_cleaner=india_speaks_cleaner.cli:main',
        ],
    },
    include_package_data=True,
    zip_safe=False,
    project_urls={
        'Bug Reports': 'https://github.com/indiaspeaks/audio-text-preprocessing/issues',
        'Source': 'https://github.com/indiaspeaks/audio-text-preprocessing',
        'Documentation': 'https://indiaspeaks.github.io/audio-text-preprocessing/',
    },
) 
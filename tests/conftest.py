#!/usr/bin/env python3
"""
Shared pytest fixtures and configuration for all tests.
This file is automatically discovered by pytest and makes fixtures available to all test modules.
"""

import os
import pytest
from backend.config import Config
from backend.services import TranscriptionService, FileUploadService
from backend.validators import FileValidator


@pytest.fixture
def test_config():
    """Create a test configuration with default values."""
    return Config(
        gemini_api_key='test-api-key',
        max_file_size=100 * 1024 * 1024,  # 100MB for testing
        default_chunk_length=12
    )


@pytest.fixture
def transcription_service(test_config):
    """Create a TranscriptionService instance for testing."""
    return TranscriptionService(test_config)


@pytest.fixture
def file_validator(test_config):
    """Create a FileValidator instance for testing."""
    return FileValidator(
        allowed_extensions=test_config.allowed_extensions,
        max_size=test_config.max_file_size
    )


@pytest.fixture
def file_upload_service(file_validator):
    """Create a FileUploadService instance for testing."""
    return FileUploadService(file_validator)




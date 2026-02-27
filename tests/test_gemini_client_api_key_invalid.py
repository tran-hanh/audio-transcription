#!/usr/bin/env python3
"""
Extra coverage for GeminiClient initialization error branches, including
the invalid/expired API key message.
"""

import pytest
from unittest.mock import MagicMock, patch

from src.gemini_client import GeminiClient
from src.exceptions import ModelInitializationError


@patch("src.gemini_client.genai")
def test_init_lists_models_invalid_api_key_message(mock_genai):
    """When list_models raises an API_KEY_INVALID style error, we expose a clear message."""
    # Simulate Google client raising an error containing API_KEY_INVALID
    mock_genai.list_models.side_effect = Exception(
        '400 API key not valid. Please pass a valid API key. [reason: "API_KEY_INVALID"]'
    )

    with pytest.raises(ModelInitializationError) as exc_info:
        GeminiClient(api_key="bad-key")

    msg = str(exc_info.value)
    assert "Gemini API key is invalid or expired" in msg
    assert "aistudio.google.com/apikey" in msg


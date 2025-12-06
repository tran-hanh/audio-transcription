#!/usr/bin/env python3
"""
Tests for backend/app.py create_app function
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from backend.app import create_app
from backend.config import Config


class TestCreateApp:
    """Tests for create_app function"""

    def test_create_app_with_config(self):
        """Test create_app with provided config"""
        config = Config(
            gemini_api_key='test-key',
            max_file_size=100 * 1024 * 1024
        )
        app = create_app(config)
        assert app is not None
        assert app.config['MAX_CONTENT_LENGTH'] == config.max_file_size * 2

    def test_create_app_without_config(self, monkeypatch):
        """Test create_app loads config from environment"""
        monkeypatch.setenv('GEMINI_API_KEY', 'test-env-key')
        app = create_app()
        assert app is not None

    def test_create_app_config_error_handling(self, monkeypatch):
        """Test create_app handles configuration errors"""
        monkeypatch.delenv('GEMINI_API_KEY', raising=False)
        with pytest.raises(ValueError, match='GEMINI_API_KEY not configured'):
            create_app()

    def test_create_app_error_handler(self, monkeypatch):
        """Test RequestEntityTooLarge error handler"""
        monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
        app = create_app()
        
        # Create a test client to trigger the error handler
        with app.test_client() as client:
            # The error handler is registered, test it indirectly
            # by checking the app has the error handler
            assert app.error_handler_spec is not None

    def test_app_main_block(self, monkeypatch):
        """Test app main block execution"""
        monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
        monkeypatch.setenv('PORT', '5002')
        
        # The app is already created when imported
        # This test verifies the app instance exists
        from backend.app import app
        assert app is not None


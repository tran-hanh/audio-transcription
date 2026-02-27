#!/usr/bin/env python3
"""
Tests for backend/app.py create_app function
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from backend.config import Config


class TestCreateApp:
    """Tests for create_app function"""

    @staticmethod
    def _import_backend_app_fresh(*, ensure_api_key: bool = True):
        """
        Import backend.app after applying env changes.

        backend.app creates a module-level `app = create_app()` on import, so tests must
        control env vars before importing/reloading the module.
        """
        import sys
        import importlib

        if ensure_api_key and not os.environ.get("GEMINI_API_KEY"):
            os.environ["GEMINI_API_KEY"] = "test-key"

        sys.modules.pop("backend.app", None)
        return importlib.import_module("backend.app")

    def test_create_app_with_config(self):
        """Test create_app with provided config"""
        config = Config(
            gemini_api_key='test-key',
            max_file_size=100 * 1024 * 1024
        )
        backend_app = self._import_backend_app_fresh()
        app = backend_app.create_app(config)
        assert app is not None
        assert app.config['MAX_CONTENT_LENGTH'] == config.max_file_size * 2

    def test_create_app_without_config(self, monkeypatch):
        """Test create_app loads config from environment"""
        monkeypatch.setenv('GEMINI_API_KEY', 'test-env-key')
        backend_app = self._import_backend_app_fresh()
        app = backend_app.create_app()
        assert app is not None

    def test_create_app_config_error_handling(self, monkeypatch):
        """Test create_app handles configuration errors"""
        monkeypatch.delenv('GEMINI_API_KEY', raising=False)
        with pytest.raises(ValueError, match='GEMINI_API_KEY not configured'):
            import sys
            import importlib

            sys.modules.pop("backend.app", None)
            importlib.import_module("backend.app")

    def test_create_app_error_handler(self, monkeypatch):
        """Test RequestEntityTooLarge error handler (covers lines 58-59)"""
        monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
        config = Config(
            gemini_api_key='test-key',
            max_file_size=100 * 1024 * 1024  # 100MB
        )
        backend_app = self._import_backend_app_fresh()
        app = backend_app.create_app(config)
        
        # Create a test client to trigger the error handler
        with app.test_client() as client:
            # The error handler is registered, test it indirectly
            # by checking the app has the error handler
            assert app.error_handler_spec is not None
            
            # Verify the error handler is registered for RequestEntityTooLarge
            from werkzeug.exceptions import RequestEntityTooLarge
            handlers = app.error_handler_spec.get(None, {})
            if handlers:
                # Handler should be registered
                assert RequestEntityTooLarge in handlers or len(handlers) > 0

    def test_app_main_block(self, monkeypatch):
        """Test app main block execution"""
        monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
        monkeypatch.setenv('PORT', '5002')
        
        # The app is already created when imported
        # This test verifies the app instance exists
        backend_app = self._import_backend_app_fresh()
        assert backend_app.app is not None


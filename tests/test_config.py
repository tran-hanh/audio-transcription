#!/usr/bin/env python3
"""
Tests for backend configuration module
"""

import os
import pytest
from backend.config import Config


class TestConfig:
    """Tests for Config class"""

    def test_config_defaults(self):
        """Test Config with default values"""
        config = Config(gemini_api_key='test-key')
        assert config.gemini_api_key == 'test-key'
        assert config.max_file_size == 1024 * 1024 * 1024  # 1GB
        assert config.default_chunk_length == 12
        assert config.min_chunk_length == 1
        assert config.max_chunk_length == 30
        assert config.host == '0.0.0.0'
        assert config.port == 5001
        assert config.debug is False
        assert 'mp3' in config.allowed_extensions
        assert 'wav' in config.allowed_extensions
        assert 'm4a' in config.allowed_extensions

    def test_config_custom_allowed_extensions(self):
        """Test Config with custom allowed extensions"""
        custom_extensions = {'mp3', 'wav'}
        config = Config(
            gemini_api_key='test-key',
            allowed_extensions=custom_extensions
        )
        assert config.allowed_extensions == custom_extensions

    def test_config_from_env_missing_api_key(self, monkeypatch):
        """Test Config.from_env raises error when API key is missing"""
        monkeypatch.delenv('GEMINI_API_KEY', raising=False)
        with pytest.raises(ValueError, match='GEMINI_API_KEY not configured'):
            Config.from_env()

    def test_config_from_env_with_api_key(self, monkeypatch):
        """Test Config.from_env creates config from environment"""
        monkeypatch.setenv('GEMINI_API_KEY', 'test-env-key')
        monkeypatch.delenv('MAX_FILE_SIZE', raising=False)
        monkeypatch.delenv('DEFAULT_CHUNK_LENGTH', raising=False)
        monkeypatch.delenv('PORT', raising=False)
        monkeypatch.delenv('FLASK_DEBUG', raising=False)
        
        config = Config.from_env()
        assert config.gemini_api_key == 'test-env-key'
        assert config.max_file_size == 1024 * 1024 * 1024  # Default 1GB

    def test_config_from_env_with_custom_max_file_size(self, monkeypatch):
        """Test Config.from_env with custom MAX_FILE_SIZE"""
        monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
        monkeypatch.setenv('MAX_FILE_SIZE', '500000000')  # 500MB
        
        config = Config.from_env()
        assert config.max_file_size == 500000000

    def test_config_from_env_with_custom_chunk_length(self, monkeypatch):
        """Test Config.from_env with custom DEFAULT_CHUNK_LENGTH"""
        monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
        monkeypatch.setenv('DEFAULT_CHUNK_LENGTH', '15')
        
        config = Config.from_env()
        assert config.default_chunk_length == 15

    def test_config_from_env_with_custom_port(self, monkeypatch):
        """Test Config.from_env with custom PORT"""
        monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
        monkeypatch.setenv('PORT', '8080')
        
        config = Config.from_env()
        assert config.port == 8080

    def test_config_from_env_with_flask_debug_true(self, monkeypatch):
        """Test Config.from_env with FLASK_DEBUG=true"""
        monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
        monkeypatch.setenv('FLASK_DEBUG', 'true')
        
        config = Config.from_env()
        assert config.debug is True

    def test_config_from_env_with_flask_debug_false(self, monkeypatch):
        """Test Config.from_env with FLASK_DEBUG=false"""
        monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
        monkeypatch.setenv('FLASK_DEBUG', 'false')
        
        config = Config.from_env()
        assert config.debug is False

    def test_config_from_env_with_flask_debug_case_insensitive(self, monkeypatch):
        """Test Config.from_env with FLASK_DEBUG case insensitive"""
        monkeypatch.setenv('GEMINI_API_KEY', 'test-key')
        monkeypatch.setenv('FLASK_DEBUG', 'TRUE')
        
        config = Config.from_env()
        assert config.debug is True


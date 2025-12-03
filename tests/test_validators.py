#!/usr/bin/env python3
"""
Tests for backend validators module
"""

import os
import tempfile
import pytest
from pathlib import Path
from backend.validators import FileValidator, ValidationError


class TestFileValidator:
    """Tests for FileValidator class"""

    @pytest.fixture
    def validator(self):
        """Create a FileValidator instance for testing"""
        return FileValidator(
            allowed_extensions={'mp3', 'wav', 'm4a'},
            max_size=100 * 1024 * 1024  # 100MB for testing
        )

    class TestValidateFilename:
        """Tests for validate_filename method"""

        def test_valid_mp3(self, validator):
            """Test valid MP3 filename"""
            is_valid, error = validator.validate_filename('test.mp3')
            assert is_valid is True
            assert error is None

        def test_valid_wav(self, validator):
            """Test valid WAV filename"""
            is_valid, error = validator.validate_filename('test.wav')
            assert is_valid is True
            assert error is None

        def test_valid_m4a(self, validator):
            """Test valid M4A filename"""
            is_valid, error = validator.validate_filename('test.m4a')
            assert is_valid is True
            assert error is None

        def test_case_insensitive(self, validator):
            """Test case insensitive extension check"""
            is_valid, error = validator.validate_filename('test.MP3')
            assert is_valid is True
            assert error is None

        def test_empty_filename(self, validator):
            """Test empty filename"""
            is_valid, error = validator.validate_filename('')
            assert is_valid is False
            assert error == 'No file selected'

        def test_whitespace_filename(self, validator):
            """Test filename with only whitespace"""
            is_valid, error = validator.validate_filename('   ')
            assert is_valid is False
            assert error == 'No file selected'

        def test_no_extension(self, validator):
            """Test filename without extension"""
            is_valid, error = validator.validate_filename('test')
            assert is_valid is False
            assert error == 'File must have an extension'

        def test_disallowed_extension(self, validator):
            """Test disallowed file extension"""
            is_valid, error = validator.validate_filename('test.txt')
            assert is_valid is False
            assert 'not allowed' in error.lower()
            assert 'mp3' in error.lower() or 'wav' in error.lower() or 'm4a' in error.lower()

        def test_multiple_dots(self, validator):
            """Test filename with multiple dots"""
            is_valid, error = validator.validate_filename('test.file.mp3')
            assert is_valid is True
            assert error is None

    class TestValidateFileSize:
        """Tests for validate_file_size method"""

        def test_valid_file_size(self, validator):
            """Test file within size limit"""
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(b'x' * (50 * 1024 * 1024))  # 50MB
                tmp_path = tmp.name
            
            try:
                is_valid, error = validator.validate_file_size(tmp_path)
                assert is_valid is True
                assert error is None
            finally:
                os.unlink(tmp_path)

        def test_file_too_large(self, validator):
            """Test file exceeding size limit"""
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(b'x' * (150 * 1024 * 1024))  # 150MB > 100MB limit
                tmp_path = tmp.name
            
            try:
                is_valid, error = validator.validate_file_size(tmp_path)
                assert is_valid is False
                assert 'too large' in error.lower()
                assert '100' in error  # Should show max size
            finally:
                os.unlink(tmp_path)

        def test_file_at_limit(self, validator):
            """Test file exactly at size limit"""
            max_size = 100 * 1024 * 1024
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp.write(b'x' * max_size)
                tmp_path = tmp.name
            
            try:
                is_valid, error = validator.validate_file_size(tmp_path)
                assert is_valid is True
                assert error is None
            finally:
                os.unlink(tmp_path)

        def test_file_not_found(self, validator):
            """Test file that doesn't exist"""
            is_valid, error = validator.validate_file_size('/nonexistent/file.mp3')
            assert is_valid is False
            assert 'Cannot read file size' in error

        def test_empty_file(self, validator):
            """Test empty file"""
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp_path = tmp.name
            
            try:
                is_valid, error = validator.validate_file_size(tmp_path)
                assert is_valid is True  # Empty file is within limit
                assert error is None
            finally:
                os.unlink(tmp_path)

    class TestValidateChunkLength:
        """Tests for validate_chunk_length method"""

        def test_valid_chunk_length(self, validator):
            """Test valid chunk length"""
            assert validator.validate_chunk_length(12) == 12
            assert validator.validate_chunk_length(15) == 15
            assert validator.validate_chunk_length(1) == 1
            assert validator.validate_chunk_length(30) == 30

        def test_chunk_length_too_low(self, validator):
            """Test chunk length below minimum"""
            assert validator.validate_chunk_length(0) == 12
            assert validator.validate_chunk_length(-5) == 12

        def test_chunk_length_too_high(self, validator):
            """Test chunk length above maximum"""
            assert validator.validate_chunk_length(31) == 12
            assert validator.validate_chunk_length(100) == 12

        def test_chunk_length_boundary(self, validator):
            """Test chunk length at boundaries"""
            assert validator.validate_chunk_length(1) == 1
            assert validator.validate_chunk_length(30) == 30


class TestValidationError:
    """Tests for ValidationError exception"""

    def test_validation_error_can_be_raised(self):
        """Test ValidationError can be raised and caught"""
        with pytest.raises(ValidationError):
            raise ValidationError("Test error")


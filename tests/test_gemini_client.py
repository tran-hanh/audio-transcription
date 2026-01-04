"""
Tests for GeminiClient following TDD principles
"""

import pytest
from unittest.mock import Mock, MagicMock, patch

from src.gemini_client import GeminiClient
from src.domain import TranscriptChunk
from src.exceptions import (
    ModelInitializationError,
    TranscriptionAPIError,
    SafetyFilterBlockError
)


class TestGeminiClient:
    """Test suite for GeminiClient"""
    
    @patch('src.gemini_client.genai')
    def test_init_with_api_key(self, mock_genai):
        """Test GeminiClient initialization with API key"""
        mock_genai.list_models.return_value = [
            MagicMock(name="models/gemini-1.5-flash", supported_generation_methods=["generateContent"])
        ]
        mock_genai.GenerativeModel.return_value = MagicMock()
        
        client = GeminiClient(api_key="test-api-key")
        
        assert client.model is not None
        mock_genai.configure.assert_called_once_with(api_key="test-api-key")
    
    @patch('src.gemini_client.genai')
    def test_init_without_api_key(self, mock_genai):
        """Test GeminiClient initialization without API key"""
        with pytest.raises(ModelInitializationError) as exc_info:
            GeminiClient(api_key="")
        
        assert "API key" in str(exc_info.value)
    
    @patch('src.gemini_client.genai')
    def test_init_model_initialization_failure(self, mock_genai):
        """Test model initialization failure"""
        mock_genai.list_models.side_effect = Exception("API error")
        mock_genai.GenerativeModel.side_effect = Exception("Model error")
        
        with pytest.raises(ModelInitializationError):
            GeminiClient(api_key="test-api-key")
    
    @patch('src.gemini_client.genai')
    def test_transcribe_chunk_success(self, mock_genai):
        """Test successful chunk transcription"""
        # Setup mocks
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.list_models.return_value = [
            MagicMock(name="models/gemini-1.5-flash", supported_generation_methods=["generateContent"])
        ]
        
        # Mock file upload
        mock_file = MagicMock()
        mock_file.state.name = "ACTIVE"
        mock_genai.upload_file.return_value = mock_file
        
        # Mock response
        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].finish_reason = 0  # STOP
        mock_response.candidates[0].content.parts = [MagicMock(text="Transcribed text")]
        mock_response.text = "Transcribed text"
        mock_model.generate_content.return_value = mock_response
        
        client = GeminiClient(api_key="test-api-key")
        
        result = client.transcribe_chunk(
            chunk_path="/path/to/chunk.mp3",
            chunk_number=1,
            total_chunks=5,
            language="vi"
        )
        
        assert isinstance(result, TranscriptChunk)
        assert result.is_successful
        assert result.text == "Transcribed text"
        assert result.chunk_number == 1
    
    @patch('src.gemini_client.genai')
    def test_transcribe_chunk_safety_block(self, mock_genai):
        """Test chunk transcription with safety block"""
        # Setup mocks
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.list_models.return_value = [
            MagicMock(name="models/gemini-1.5-flash", supported_generation_methods=["generateContent"])
        ]
        
        # Mock file upload
        mock_file = MagicMock()
        mock_file.state.name = "ACTIVE"
        mock_genai.upload_file.return_value = mock_file
        
        # Mock safety block response
        mock_response = MagicMock()
        mock_response.candidates = [MagicMock()]
        mock_response.candidates[0].finish_reason = 1  # SAFETY
        mock_response.candidates[0].content = None
        mock_model.generate_content.return_value = mock_response
        
        client = GeminiClient(api_key="test-api-key")
        
        result = client.transcribe_chunk(
            chunk_path="/path/to/chunk.mp3",
            chunk_number=1,
            total_chunks=5,
            language="vi"
        )
        
        assert isinstance(result, TranscriptChunk)
        assert result.is_error
        assert "safety filters" in (result.error_message or "").lower()
    
    @patch('src.gemini_client.genai')
    def test_transcribe_chunk_file_processing_failed(self, mock_genai):
        """Test chunk transcription with file processing failure"""
        # Setup mocks
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.list_models.return_value = [
            MagicMock(name="models/gemini-1.5-flash", supported_generation_methods=["generateContent"])
        ]
        
        # Mock file upload with failed state
        mock_file = MagicMock()
        mock_file.state.name = "FAILED"
        mock_genai.upload_file.return_value = mock_file
        
        client = GeminiClient(api_key="test-api-key")
        
        result = client.transcribe_chunk(
            chunk_path="/path/to/chunk.mp3",
            chunk_number=1,
            total_chunks=5,
            language="vi"
        )
        
        assert isinstance(result, TranscriptChunk)
        assert result.is_error
        assert "processing failed" in (result.error_message or "").lower()
    
    @patch('src.gemini_client.genai')
    def test_extract_text_from_response(self, mock_genai):
        """Test text extraction from response"""
        # Setup mocks
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_genai.list_models.return_value = [
            MagicMock(name="models/gemini-1.5-flash", supported_generation_methods=["generateContent"])
        ]
        
        client = GeminiClient(api_key="test-api-key")
        
        # Test with response.text
        mock_response = MagicMock()
        mock_response.text = "Test transcription"
        mock_response.candidates = [MagicMock()]
        
        text = client._extract_text(mock_response)
        assert text == "Test transcription"
        
        # Test with parts
        mock_response.text = None
        mock_response.candidates[0].content.parts = [
            MagicMock(text="Part 1"),
            MagicMock(text="Part 2")
        ]
        
        text = client._extract_text(mock_response)
        assert text == "Part 1 Part 2"






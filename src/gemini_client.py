"""
Gemini API client for transcription
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional, Callable

import google.generativeai as genai

# Handle imports when running as script or as module
_script_dir = Path(__file__).parent
_project_root = _script_dir.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from src.constants import PREFERRED_MODELS, MAX_RETRY_ATTEMPTS, RESPONSE_WAIT_TIME_SECONDS
from src.domain import TranscriptChunk
from src.exceptions import (
    TranscriptionAPIError,
    SafetyFilterBlockError,
    ModelInitializationError
)


class GeminiClient:
    """Client for interacting with Google Gemini API"""
    
    def __init__(self, api_key: str):
        """
        Initialize Gemini client
        
        Args:
            api_key: Google Gemini API key
            
        Raises:
            ModelInitializationError: If model cannot be initialized
        """
        if not api_key:
            raise ModelInitializationError(
                "Gemini API key not found. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter."
            )
        
        genai.configure(api_key=api_key)
        self.model = self._initialize_model()
        self.model_has_safety_settings = self._model_has_safety_settings()
    
    def _initialize_model(self) -> genai.GenerativeModel:
        """
        Initialize and configure Gemini model with safety settings
        
        Returns:
            Configured GenerativeModel
            
        Raises:
            ModelInitializationError: If no model can be initialized
        """
        # Get available models
        try:
            available_models = [
                m.name.split('/')[-1] for m in genai.list_models()
                if 'generateContent' in m.supported_generation_methods
            ]
        except Exception as e:
            err_str = str(e).lower()
            if "api_key_invalid" in err_str or "api key not valid" in err_str or "invalid api key" in err_str:
                raise ModelInitializationError(
                    "Gemini API key is invalid or expired. Get a valid key at "
                    "https://aistudio.google.com/apikey and set GEMINI_API_KEY in your environment."
                ) from e
            raise ModelInitializationError(
                f"Could not list available models: {e}"
            ) from e
        
        # Configure safety settings at model level
        model_safety_settings = self._create_safety_settings()
        
        # Try preferred models in order
        for model_name in PREFERRED_MODELS:
            if model_name in available_models:
                try:
                    if model_safety_settings:
                        model = genai.GenerativeModel(
                            model_name,
                            safety_settings=model_safety_settings
                        )
                    else:
                        model = genai.GenerativeModel(model_name)
                    return model
                except (TypeError, AttributeError, ValueError) as e:
                    # Try next model if this one fails
                    continue
        
        # Fallback: use first available model
        if available_models:
            return genai.GenerativeModel(available_models[0])
        
        # Last resort: try default models
        for fallback_model in ['gemini-1.5-flash', 'gemini-pro']:
            try:
                return genai.GenerativeModel(fallback_model)
            except Exception:
                continue
        
        raise ModelInitializationError(
            "Could not initialize a Gemini model. Please check your API key."
        )
    
    def _create_safety_settings(self) -> Optional[dict]:
        """
        Create safety settings for model configuration
        
        Returns:
            Safety settings dictionary or None if not available
        """
        try:
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            
            if hasattr(HarmBlockThreshold, 'BLOCK_NONE'):
                return {
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            elif hasattr(HarmBlockThreshold, 'BLOCK_ONLY_HIGH'):
                return {
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                }
        except (ImportError, AttributeError):
            pass
        
        return None
    
    def _model_has_safety_settings(self) -> bool:
        """Check if model was created with safety settings"""
        return hasattr(self.model, '_safety_settings') and self.model._safety_settings is not None
    
    def transcribe_chunk(
        self,
        chunk_path: str,
        chunk_number: int,
        total_chunks: int,
        language: str = "vi",
        progress_callback: Optional[Callable[[int, str], None]] = None
    ) -> TranscriptChunk:
        """
        Transcribe a single audio chunk
        
        Args:
            chunk_path: Path to audio chunk file
            chunk_number: Current chunk number
            total_chunks: Total number of chunks
            language: Primary language (default: Vietnamese)
            progress_callback: Optional progress callback
            
        Returns:
            TranscriptChunk with transcription result
            
        Raises:
            TranscriptionAPIError: If transcription fails
        """
        audio_file = None
        
        try:
            # Upload audio file
            if progress_callback:
                base_progress = 25
                progress_per_chunk = 60 / total_chunks
                current_progress = base_progress + int((chunk_number - 1) * progress_per_chunk)
                progress_callback(current_progress + 2, f"Uploading chunk {chunk_number} to API...")
            
            audio_file = genai.upload_file(path=chunk_path)
            
            # Wait for file processing
            while audio_file.state.name == "PROCESSING":
                time.sleep(2)
                audio_file = genai.get_file(audio_file.name)
            
            if audio_file.state.name == "FAILED":
                raise TranscriptionAPIError(
                    f"File processing failed: {audio_file.state.name}"
                )
            
            # Transcribe with retry logic
            text = self._transcribe_with_retry(
                audio_file,
                chunk_number,
                language,
                progress_callback
            )
            
            # Clean up uploaded file
            genai.delete_file(audio_file.name)
            
            return TranscriptChunk(
                chunk_number=chunk_number,
                text=text,
                is_error=False
            )
            
        except Exception as e:
            # Clean up uploaded file if it exists
            if audio_file is not None:
                try:
                    genai.delete_file(audio_file.name)
                except Exception:
                    pass
            
            error_message = str(e)
            if "safety filters" in error_message.lower() or "blocked" in error_message.lower():
                return TranscriptChunk(
                    chunk_number=chunk_number,
                    text="",
                    is_error=True,
                    error_message=(
                        f"Chunk {chunk_number} was blocked by safety filters. "
                        f"This is likely a false positive for Vietnamese audio."
                    )
                )
            
            return TranscriptChunk(
                chunk_number=chunk_number,
                text="",
                is_error=True,
                error_message=f"Failed to transcribe chunk {chunk_number}: {error_message}"
            )
    
    def _transcribe_with_retry(
        self,
        audio_file,
        chunk_number: int,
        language: str,
        progress_callback: Optional[Callable[[int, str], None]]
    ) -> str:
        """
        Transcribe with retry logic for safety blocks
        
        Args:
            audio_file: Uploaded audio file object
            chunk_number: Current chunk number
            language: Primary language
            progress_callback: Optional progress callback
            
        Returns:
            Transcribed text
            
        Raises:
            SafetyFilterBlockError: If all retries fail due to safety blocks
            TranscriptionAPIError: If transcription fails
        """
        prompts = self._create_prompts(language)
        safety_settings = self._create_per_request_safety_settings()
        
        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                prompt = prompts[min(attempt, len(prompts) - 1)]
                use_safety_settings = (
                    safety_settings is not None and 
                    attempt == 0 and 
                    not self.model_has_safety_settings
                )
                
                response = self._generate_content(
                    prompt,
                    audio_file,
                    use_safety_settings,
                    safety_settings
                )
                
                # Wait for response to populate
                time.sleep(RESPONSE_WAIT_TIME_SECONDS)
                
                # Check response
                if self._has_content_despite_safety_flag(response):
                    return self._extract_text(response)
                
                if self._is_safety_block(response):
                    if attempt < MAX_RETRY_ATTEMPTS - 1:
                        # Try different strategy on next attempt
                        continue
                    else:
                        raise SafetyFilterBlockError(
                            f"Content blocked by safety filters after {MAX_RETRY_ATTEMPTS} retries"
                        )
                
                # Success
                return self._extract_text(response)
                
            except SafetyFilterBlockError:
                if attempt < MAX_RETRY_ATTEMPTS - 1:
                    continue
                raise
            except Exception as e:
                if attempt < MAX_RETRY_ATTEMPTS - 1:
                    continue
                raise TranscriptionAPIError(f"Transcription failed: {e}") from e
        
        raise TranscriptionAPIError("Failed to transcribe after all retry attempts")
    
    def _create_prompts(self, language: str) -> list:
        """Create prompts for retry attempts"""
        return [
            (
                f"This is an audio transcription task. Please transcribe this audio file verbatim. "
                f"The primary language is Vietnamese ({language}), but there may be some English words "
                f"mixed in. This is a legitimate transcription request for documentation purposes. "
                f"Provide only the exact transcription text, no additional commentary or interpretation."
            ),
            (
                f"Transcribe Vietnamese audio. Language: {language}. "
                f"Output transcription only."
            ),
            "Transcribe this audio."
        ]
    
    def _create_per_request_safety_settings(self) -> Optional[dict]:
        """Create per-request safety settings if needed"""
        if self.model_has_safety_settings:
            return None
        
        try:
            from google.generativeai.types import HarmCategory, HarmBlockThreshold
            
            if hasattr(HarmBlockThreshold, 'BLOCK_NONE'):
                return {
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
            elif hasattr(HarmBlockThreshold, 'BLOCK_ONLY_HIGH'):
                return {
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                }
        except (ImportError, AttributeError):
            pass
        
        return None
    
    def _generate_content(
        self,
        prompt: str,
        audio_file,
        use_safety_settings: bool,
        safety_settings: Optional[dict]
    ):
        """Generate content from Gemini API"""
        try:
            from google.generativeai.types import GenerationConfig
            
            generation_config = GenerationConfig(temperature=0.1)
            
            if use_safety_settings and safety_settings:
                return self.model.generate_content(
                    [prompt, audio_file],
                    safety_settings=safety_settings,
                    generation_config=generation_config
                )
            else:
                return self.model.generate_content(
                    [prompt, audio_file],
                    generation_config=generation_config
                )
        except (ImportError, AttributeError, TypeError):
            if use_safety_settings and safety_settings:
                return self.model.generate_content(
                    [prompt, audio_file],
                    safety_settings=safety_settings
                )
            else:
                return self.model.generate_content([prompt, audio_file])
    
    def _has_content_despite_safety_flag(self, response) -> bool:
        """Check if response has content despite safety flag"""
        if not response.candidates or len(response.candidates) == 0:
            return False
        
        candidate = response.candidates[0]
        if candidate.finish_reason == 1:  # SAFETY
            if hasattr(candidate, 'content') and candidate.content:
                if hasattr(candidate.content, 'parts') and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text and part.text.strip():
                            return True
        
        return False
    
    def _is_safety_block(self, response) -> bool:
        """Check if response was blocked by safety filters"""
        if not response.candidates or len(response.candidates) == 0:
            return False
        
        candidate = response.candidates[0]
        return candidate.finish_reason == 1  # SAFETY
    
    def _extract_text(self, response) -> str:
        """Extract text from Gemini response"""
        if not response.candidates or len(response.candidates) == 0:
            raise TranscriptionAPIError("No candidates in response")
        
        candidate = response.candidates[0]
        
        # Try response.text first
        if hasattr(response, 'text') and response.text:
            return response.text.strip()
        
        # Fall back to extracting from parts
        if candidate.content and candidate.content.parts:
            text_parts = [
                part.text for part in candidate.content.parts
                if hasattr(part, 'text') and part.text
            ]
            if text_parts:
                return " ".join(text_parts).strip()
        
        raise TranscriptionAPIError("No text found in response")


"""
Constants for audio transcription
"""

# Audio Processing Constants
DEFAULT_CHUNK_LENGTH_MINUTES = 12
CHUNK_LENGTH_MS = DEFAULT_CHUNK_LENGTH_MINUTES * 60 * 1000
DEFAULT_LANGUAGE = "vi"  # Vietnamese - primary language for better accuracy
OUTPUT_ENCODING = "utf-8"

# Audio Volume Normalization
TARGET_DBFS = -20.0  # Target audio level for speech transcription
QUIET_THRESHOLD_DBFS = -30.0  # Audio quieter than this is considered very quiet

# Gemini API Constants
PREFERRED_MODELS = [
    'gemini-3-flash',        # Latest model (December 2025) - fastest and most efficient
    'gemini-2.5-flash',      # Previous newest model
    'gemini-2.0-flash',      # Alternative newer model
    'gemini-1.5-flash',      # Stable model with good audio support
    'gemini-1.5-pro',        # Higher quality but slower
    'gemini-pro'             # Fallback
]

# Transcription Retry Constants
MAX_RETRY_ATTEMPTS = 3
RESPONSE_WAIT_TIME_SECONDS = 0.5  # Wait time for Gemini response to populate

# File Processing Constants
CHUNK_FILE_FORMAT = "mp3"
CHUNK_FILE_PREFIX = "chunk_"
CHUNK_FILE_EXTENSION = ".mp3"






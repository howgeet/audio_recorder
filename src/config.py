"""Configuration management for the Meeting Transcriber application."""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration class."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # API Keys
        self.openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.huggingface_token: Optional[str] = os.getenv("HUGGINGFACE_TOKEN")
        
        # Audio Settings
        self.sample_rate: int = int(os.getenv("SAMPLE_RATE", "16000"))
        self.channels: int = int(os.getenv("CHANNELS", "2"))
        self.chunk_size: int = int(os.getenv("CHUNK_SIZE", "1024"))
        
        # Transcription Settings (OpenAI Whisper)
        self.transcription_model: str = os.getenv("WHISPER_MODEL", "whisper-1")
        self.languages: list = ["tr", "en"]  # Turkish and English
        
        # Output Settings
        self.output_dir: Path = Path(os.getenv("OUTPUT_DIR", "outputs"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Diarization Settings
        self.min_speakers: int = int(os.getenv("MIN_SPEAKERS", "2"))
        self.max_speakers: int = int(os.getenv("MAX_SPEAKERS", "10"))
        
        # LLM Settings for Summarization (OpenAI GPT)
        self.llm_model: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.temperature: float = float(os.getenv("TEMPERATURE", "0.3"))
        
    def validate(self) -> tuple[bool, list[str]]:
        """Validate configuration.
        
        Returns:
            tuple: (is_valid, list of error messages)
        """
        errors = []
        
        if not self.openai_api_key:
            errors.append("OPENAI_API_KEY is not set. Required for transcription and summarization.")
        
        return len(errors) == 0, errors
    
    def __str__(self) -> str:
        """String representation of configuration (hiding sensitive data)."""
        return f"""
Configuration:
  Sample Rate: {self.sample_rate} Hz
  Channels: {self.channels}
  Transcription Model: {self.transcription_model}
  LLM Model: {self.llm_model}
  Output Directory: {self.output_dir}
  Min Speakers: {self.min_speakers}
  Max Speakers: {self.max_speakers}
  OpenAI API Key: {'Set' if self.openai_api_key else 'Not Set'}
"""

# Global configuration instance
config = Config()

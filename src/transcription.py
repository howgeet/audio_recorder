"""Transcription module using OpenAI Whisper API with chunking support for large files.

This module is Python 3.13+ compatible, using ffmpeg for audio processing
instead of pydub (which depends on the deprecated audioop module).
Falls back to local faster-whisper when OpenAI is unavailable.
"""

import os
import time
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List, Callable
from openai import OpenAI

from src.config import config
from src.ffmpeg_utils import (
    check_ffmpeg_installed,
    get_ffmpeg_error_message,
    get_audio_duration,
    split_audio_file,
    calculate_chunk_duration_for_size,
    FFmpegError
)

# Constants for file size limits
MAX_FILE_SIZE_BYTES = 24 * 1024 * 1024  # 24MB (safe threshold below 25MB API limit)
TARGET_CHUNK_SIZE_BYTES = 20 * 1024 * 1024  # 20MB target chunk size


class LocalTranscriber:
    """Handles audio transcription using faster-whisper locally (no API key required)."""

    DEFAULT_MODEL = "base"

    def __init__(self, model_size: str = DEFAULT_MODEL):
        """Initialize the local transcriber."""
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise ImportError(
                "faster-whisper is not installed. Run: pip install faster-whisper"
            )
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        self.model_size = model_size

    def transcribe_audio(self, audio_file: Path, language: Optional[str] = None,
                         progress_callback: Optional[Callable[[str], None]] = None) -> Dict[str, Any]:
        """Transcribe audio file locally using faster-whisper."""
        def log(msg: str):
            print(msg)
            if progress_callback:
                progress_callback(msg)

        selected_language = language or getattr(config, "whisper_language", None)

        log(f"\n🖥️  Starting local transcription (faster-whisper {self.model_size})...")
        log(f"   File: {audio_file.name}")
        log(f"   Language: {selected_language}")

        start_time = time.time()
        segments_iter, info = self.model.transcribe(
            str(audio_file),
            language=selected_language,
            beam_size=5
        )

        segments = []
        words = []
        full_text_parts = []

        for seg in segments_iter:
            segments.append({
                'start': seg.start,
                'end': seg.end,
                'text': seg.text
            })
            full_text_parts.append(seg.text.strip())
            if seg.words:
                for w in seg.words:
                    words.append({'start': w.start, 'end': w.end, 'word': w.word})

        elapsed = time.time() - start_time
        log(f"✅ Local transcription completed in {elapsed:.2f} seconds")
        log(f"   Detected language: {info.language}")

        return {
            'text': ' '.join(full_text_parts),
            'language': info.language,
            'duration': info.duration,
            'segments': segments,
            'words': words
        }


class Transcriber:
    """Handles audio transcription using OpenAI Whisper API with chunking for large files."""
    
    def __init__(self):
        """Initialize the transcriber."""
        self.client = OpenAI(api_key=config.openai_api_key or "")
        self.model = config.transcription_model
        self.default_language = getattr(config, "whisper_language", None)
        self.local_model_size = getattr(config, "local_whisper_model", "medium")
        
    def _get_file_size(self, audio_file: Path) -> int:
        """Get file size in bytes."""
        return audio_file.stat().st_size
    
    def _needs_chunking(self, audio_file: Path) -> bool:
        """Check if file needs to be split into chunks."""
        return self._get_file_size(audio_file) > MAX_FILE_SIZE_BYTES
    
    def _split_audio_into_chunks(self, audio_file: Path, progress_callback: Optional[Callable] = None) -> List[tuple]:
        """Split audio file into smaller chunks using ffmpeg.
        
        Args:
            audio_file: Path to the audio file
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of tuples: (chunk_path, start_time_ms)
        """
        # Check ffmpeg is available
        if not check_ffmpeg_installed():
            raise FFmpegError(get_ffmpeg_error_message())
        
        if progress_callback:
            progress_callback("Analyzing audio file for chunking...")
        
        # Calculate optimal chunk duration based on file size
        file_size = self._get_file_size(audio_file)
        chunk_duration = calculate_chunk_duration_for_size(audio_file, TARGET_CHUNK_SIZE_BYTES)
        
        if progress_callback:
            progress_callback(f"Splitting audio into chunks (~{int(chunk_duration)}s each)...")
        
        # Create temporary directory for chunks
        temp_dir = Path(tempfile.mkdtemp(prefix="transcription_chunks_"))
        
        try:
            # Split the audio file
            chunks = split_audio_file(
                audio_file=audio_file,
                output_dir=temp_dir,
                chunk_duration_seconds=chunk_duration,
                output_format='wav'
            )
            
            if progress_callback:
                progress_callback(f"Created {len(chunks)} chunks")
            
            return chunks
            
        except FFmpegError as e:
            # Clean up on error
            self._cleanup_temp_dir(temp_dir)
            raise
    
    def _transcribe_single_chunk(self, audio_file: Path, language: Optional[str] = None) -> Dict[str, Any]:
        """Transcribe a single audio file/chunk.
        
        Args:
            audio_file: Path to audio file
            language: Language code (optional)
            
        Returns:
            Dictionary containing transcription text and metadata
        """
        with open(audio_file, "rb") as audio:
            params = {
                "model": self.model,
                "file": audio,
                "response_format": "verbose_json",
                "timestamp_granularities": ["word", "segment"]
            }
            
            if language:
                params["language"] = language
            
            response = self.client.audio.transcriptions.create(**params)
        
        # Extract results
        detected_language = getattr(response, 'language', language)
        duration = getattr(response, 'duration', None)
        
        # Parse segments
        segments = []
        if hasattr(response, 'segments') and response.segments:
            for seg in response.segments:
                segments.append({
                    'start': seg.get('start', 0) if isinstance(seg, dict) else getattr(seg, 'start', 0),
                    'end': seg.get('end', 0) if isinstance(seg, dict) else getattr(seg, 'end', 0),
                    'text': seg.get('text', '') if isinstance(seg, dict) else getattr(seg, 'text', '')
                })
        
        # Parse words
        words = []
        if hasattr(response, 'words') and response.words:
            for word in response.words:
                words.append({
                    'start': word.get('start', 0) if isinstance(word, dict) else getattr(word, 'start', 0),
                    'end': word.get('end', 0) if isinstance(word, dict) else getattr(word, 'end', 0),
                    'word': word.get('word', '') if isinstance(word, dict) else getattr(word, 'word', '')
                })
        
        return {
            'text': response.text,
            'language': detected_language,
            'duration': duration,
            'segments': segments,
            'words': words
        }
    
    def _merge_transcripts(self, transcripts: List[Dict], chunk_offsets_ms: List[float]) -> Dict[str, Any]:
        """Merge transcripts from multiple chunks with adjusted timestamps.
        
        Args:
            transcripts: List of transcript dictionaries from each chunk
            chunk_offsets_ms: Start time offset for each chunk in milliseconds
            
        Returns:
            Merged transcript dictionary
        """
        merged_text = []
        merged_segments = []
        merged_words = []
        total_duration = 0
        detected_language = None
        
        for i, (transcript, offset_ms) in enumerate(zip(transcripts, chunk_offsets_ms)):
            offset_seconds = offset_ms / 1000.0
            
            # Append text
            text = transcript.get('text', '').strip()
            if text:
                merged_text.append(text)
            
            # Get language from first chunk
            if not detected_language and transcript.get('language'):
                detected_language = transcript['language']
            
            # Adjust segment timestamps
            for segment in transcript.get('segments', []):
                merged_segments.append({
                    'start': segment['start'] + offset_seconds,
                    'end': segment['end'] + offset_seconds,
                    'text': segment['text']
                })
            
            # Adjust word timestamps
            for word in transcript.get('words', []):
                merged_words.append({
                    'start': word['start'] + offset_seconds,
                    'end': word['end'] + offset_seconds,
                    'word': word['word']
                })
            
            # Track total duration
            if transcript.get('duration'):
                total_duration = max(total_duration, offset_seconds + transcript['duration'])
        
        return {
            'text': ' '.join(merged_text),
            'language': detected_language,
            'duration': total_duration,
            'segments': merged_segments,
            'words': merged_words
        }
    
    def _cleanup_chunks(self, chunk_data: List[tuple]):
        """Clean up temporary chunk files."""
        for chunk_path, _ in chunk_data:
            try:
                if chunk_path.exists():
                    chunk_path.unlink()
            except Exception:
                pass
        
        # Try to remove the temp directory
        if chunk_data:
            self._cleanup_temp_dir(chunk_data[0][0].parent)
    
    def _cleanup_temp_dir(self, temp_dir: Path):
        """Clean up temporary directory."""
        try:
            if temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
    
    def transcribe_audio(
        self, 
        audio_file: Path, 
        language: Optional[str] = None,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """Transcribe audio file using OpenAI Whisper API.
        
        Automatically handles large files by splitting into chunks.
        
        Args:
            audio_file: Path to audio file
            language: Language code (optional, will auto-detect if not provided)
            progress_callback: Optional callback for progress updates (receives status messages)
            
        Returns:
            Dictionary containing transcription text and metadata
        """
        def log(msg: str):
            print(msg)
            if progress_callback:
                progress_callback(msg)
        
        selected_language = language or self.default_language

        log(f"\n🎙️  Starting transcription...")
        log(f"   File: {audio_file.name}")
        log(f"   Model: {self.model}")
        log(f"   Language: {selected_language}")
        
        if not audio_file.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file}")
        
        file_size = self._get_file_size(audio_file)
        file_size_mb = file_size / (1024 * 1024)
        log(f"   File size: {file_size_mb:.2f} MB")
        
        try:
            start_time = time.time()
            
            # Check if chunking is needed
            if self._needs_chunking(audio_file):
                log(f"⚠️  File exceeds 24MB limit. Splitting into chunks...")
                
                # Split audio into chunks (returns list of (path, offset_ms) tuples)
                chunk_data = self._split_audio_into_chunks(audio_file, progress_callback)
                num_chunks = len(chunk_data)
                log(f"   Created {num_chunks} chunks")
                
                # Extract chunk paths and offsets
                chunk_paths = [path for path, _ in chunk_data]
                chunk_offsets_ms = [offset for _, offset in chunk_data]
                
                transcripts = []
                
                try:
                    # Transcribe each chunk
                    for i, chunk_path in enumerate(chunk_paths):
                        log(f"📝 Processing chunk {i + 1} of {num_chunks}...")
                        
                        transcript = self._transcribe_single_chunk(chunk_path, selected_language)
                        transcripts.append(transcript)
                        
                        log(f"   ✅ Chunk {i + 1} complete")
                    
                    # Merge all transcripts
                    log(f"🔗 Merging transcripts...")
                    result = self._merge_transcripts(transcripts, chunk_offsets_ms)
                    
                finally:
                    # Clean up temporary files
                    self._cleanup_chunks(chunk_data)
                    log(f"🧹 Cleaned up temporary files")
            else:
                # File is small enough, process directly
                result = self._transcribe_single_chunk(audio_file, selected_language)
            
            elapsed_time = time.time() - start_time
            
            log(f"✅ Transcription completed in {elapsed_time:.2f} seconds")
            log(f"   Detected language: {result.get('language') or 'N/A'}")
            if result.get('duration'):
                log(f"   Duration: {result['duration']:.2f} seconds")
            
            return result
            
        except FFmpegError as e:
            log(f"❌ FFmpeg error: {e}")
            raise
        except Exception as e:
            error_msg = str(e)
            if "413" in error_msg or "Maximum content size" in error_msg:
                log(f"❌ File too large error despite chunking. Please try a shorter recording.")
            else:
                log(f"❌ Transcription error: {e}")
            raise
    
    def transcribe_with_retry(
        self, 
        audio_file: Path, 
        max_retries: int = 3,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """Transcribe with automatic retry on failure.
        
        Falls back to local faster-whisper if all OpenAI API attempts fail.
        
        Args:
            audio_file: Path to audio file
            max_retries: Maximum number of retry attempts
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary containing transcription results
        """
        def log(msg: str):
            print(msg)
            if progress_callback:
                progress_callback(msg)

        for attempt in range(max_retries):
            try:
                return self.transcribe_audio(audio_file, progress_callback=progress_callback)
            except FFmpegError:
                # Don't retry for FFmpeg errors (likely configuration issue)
                raise
            except Exception as e:
                error_msg = str(e)
                # Don't retry for file-too-large errors
                if "413" in error_msg or "Maximum content size" in error_msg:
                    raise

                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    log(f"⚠️  Attempt {attempt + 1} failed. Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    log(f"⚠️  OpenAI transcription unavailable: {e}")
                    log(f"🔄 Falling back to local Whisper model...")
                    try:
                        local = LocalTranscriber(self.local_model_size)
                        return local.transcribe_audio(
                            audio_file,
                            language=self.default_language,
                            progress_callback=progress_callback
                        )
                    except Exception as local_err:
                        log(f"❌ Local transcription also failed: {local_err}")
                        raise

    def transcribe_audio_files_with_retry(
        self,
        audio_files: List[Path],
        max_retries: int = 3,
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """Transcribe multiple audio files and merge into one timeline.

        This is useful for long recordings that are saved as partial WAV files.
        """
        if not audio_files:
            raise ValueError("No audio files provided for transcription")

        ordered_files = sorted(audio_files)
        transcripts: List[Dict[str, Any]] = []
        chunk_offsets_ms: List[float] = []
        cumulative_offset_seconds = 0.0

        def log(msg: str):
            print(msg)
            if progress_callback:
                progress_callback(msg)

        for idx, part_file in enumerate(ordered_files, start=1):
            if not part_file.exists() or part_file.stat().st_size == 0:
                log(f"⚠️  Skipping empty or missing part: {part_file}")
                continue

            log(f"🎧 Transcribing part {idx}/{len(ordered_files)}: {part_file.name}")
            chunk_offsets_ms.append(cumulative_offset_seconds * 1000.0)
            part_result = self.transcribe_with_retry(
                part_file,
                max_retries=max_retries,
                progress_callback=progress_callback
            )
            transcripts.append(part_result)

            part_duration = part_result.get('duration')
            if not part_duration:
                try:
                    part_duration = get_audio_duration(part_file)
                except Exception:
                    part_duration = 0
            cumulative_offset_seconds += float(part_duration or 0)

        if not transcripts:
            raise ValueError("No valid audio parts were transcribed")

        if len(transcripts) == 1:
            return transcripts[0]

        return self._merge_transcripts(transcripts, chunk_offsets_ms)
    
    def format_transcript(self, transcription_result: Dict[str, Any]) -> str:
        """Format transcription result into readable text.
        
        Args:
            transcription_result: Transcription result dictionary
            
        Returns:
            Formatted transcript string
        """
        output = []
        output.append("=" * 80)
        output.append("MEETING TRANSCRIPT")
        output.append("=" * 80)
        output.append("")
        
        if transcription_result.get('language'):
            output.append(f"Language: {transcription_result['language'].upper()}")
        if transcription_result.get('duration'):
            duration_mins = transcription_result['duration'] / 60
            output.append(f"Duration: {duration_mins:.2f} minutes")
        output.append("")
        output.append("-" * 80)
        output.append("")
        
        # Add segments with timestamps if available
        segments = transcription_result.get('segments', [])
        if segments:
            for segment in segments:
                start_time = segment.get('start', 0)
                end_time = segment.get('end', 0)
                text = segment.get('text', '')
                
                # Format timestamp as MM:SS
                start_mm_ss = f"{int(start_time // 60):02d}:{int(start_time % 60):02d}"
                end_mm_ss = f"{int(end_time // 60):02d}:{int(end_time % 60):02d}"
                
                output.append(f"[{start_mm_ss} - {end_mm_ss}] {text.strip()}")
            output.append("")
        else:
            # Fallback to full text if no segments
            output.append(transcription_result.get('text', ''))
            output.append("")
        
        output.append("-" * 80)
        output.append(f"End of Transcript")
        output.append("=" * 80)
        
        return "\n".join(output)

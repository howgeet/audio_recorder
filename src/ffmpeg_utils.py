"""FFmpeg utility functions for audio processing.

This module provides Python 3.13+ compatible audio processing using ffmpeg
subprocess calls, replacing the pydub dependency that relies on the deprecated
audioop module.
"""

import subprocess
import tempfile
import shutil
import json
from pathlib import Path
from typing import Optional, List, Tuple


class FFmpegError(Exception):
    """Exception raised for ffmpeg-related errors."""
    pass


def check_ffmpeg_installed() -> bool:
    """Check if ffmpeg is installed and accessible."""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_ffmpeg_error_message() -> str:
    """Get a helpful error message for missing ffmpeg."""
    return (
        "FFmpeg is not installed or not found in PATH.\n\n"
        "FFmpeg is REQUIRED for this application to work.\n\n"
        "Installation instructions:\n"
        "  Windows: Download from https://ffmpeg.org/download.html\n"
        "           or use: winget install ffmpeg\n"
        "           or use: choco install ffmpeg\n\n"
        "  macOS:   brew install ffmpeg\n\n"
        "  Linux:   sudo apt install ffmpeg\n"
        "           or: sudo dnf install ffmpeg\n\n"
        "After installation, restart your terminal/application."
    )


def get_audio_duration(audio_file: Path) -> float:
    """Get audio duration in seconds using ffprobe.
    
    Args:
        audio_file: Path to audio file
        
    Returns:
        Duration in seconds
        
    Raises:
        FFmpegError: If ffprobe fails or duration cannot be determined
    """
    if not check_ffmpeg_installed():
        raise FFmpegError(get_ffmpeg_error_message())
    
    try:
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'quiet',
                '-show_entries', 'format=duration',
                '-of', 'json',
                str(audio_file)
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            raise FFmpegError(f"ffprobe failed: {result.stderr}")
        
        data = json.loads(result.stdout)
        duration = float(data['format']['duration'])
        return duration
        
    except (json.JSONDecodeError, KeyError) as e:
        raise FFmpegError(f"Failed to parse ffprobe output: {e}")
    except subprocess.TimeoutExpired:
        raise FFmpegError("ffprobe timed out")


def get_audio_info(audio_file: Path) -> dict:
    """Get audio file information using ffprobe.
    
    Args:
        audio_file: Path to audio file
        
    Returns:
        Dictionary with duration, bitrate, sample_rate, channels
    """
    if not check_ffmpeg_installed():
        raise FFmpegError(get_ffmpeg_error_message())
    
    try:
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'quiet',
                '-show_entries', 'format=duration,bit_rate:stream=sample_rate,channels',
                '-of', 'json',
                str(audio_file)
            ],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            raise FFmpegError(f"ffprobe failed: {result.stderr}")
        
        data = json.loads(result.stdout)
        
        info = {
            'duration': float(data.get('format', {}).get('duration', 0)),
            'bitrate': int(data.get('format', {}).get('bit_rate', 0)),
        }
        
        # Get stream info if available
        streams = data.get('streams', [])
        if streams:
            info['sample_rate'] = int(streams[0].get('sample_rate', 44100))
            info['channels'] = int(streams[0].get('channels', 2))
        else:
            info['sample_rate'] = 44100
            info['channels'] = 2
        
        return info
        
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise FFmpegError(f"Failed to parse ffprobe output: {e}")


def split_audio_file(
    audio_file: Path,
    output_dir: Path,
    chunk_duration_seconds: float,
    output_format: str = 'wav'
) -> List[Tuple[Path, float]]:
    """Split audio file into chunks of specified duration.
    
    Args:
        audio_file: Path to input audio file
        output_dir: Directory to save chunks
        chunk_duration_seconds: Duration of each chunk in seconds
        output_format: Output format for chunks (wav, mp3, etc.)
        
    Returns:
        List of tuples: (chunk_path, start_time_ms)
        
    Raises:
        FFmpegError: If ffmpeg fails
    """
    if not check_ffmpeg_installed():
        raise FFmpegError(get_ffmpeg_error_message())
    
    # Get total duration
    total_duration = get_audio_duration(audio_file)
    
    chunks = []
    chunk_num = 0
    current_time = 0.0
    
    while current_time < total_duration:
        chunk_num += 1
        chunk_path = output_dir / f"chunk_{chunk_num:03d}.{output_format}"
        
        # Calculate actual chunk duration (may be shorter for last chunk)
        actual_duration = min(chunk_duration_seconds, total_duration - current_time)
        
        # Build ffmpeg command
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output
            '-i', str(audio_file),
            '-ss', str(current_time),  # Start time
            '-t', str(actual_duration),  # Duration
            '-vn',  # No video
            '-acodec', 'pcm_s16le' if output_format == 'wav' else 'copy',
            '-ar', '16000',  # Sample rate (good for speech)
            '-ac', '1',  # Mono
            str(chunk_path)
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per chunk
            )
            
            if result.returncode != 0:
                raise FFmpegError(f"ffmpeg failed to create chunk: {result.stderr}")
            
            if not chunk_path.exists() or chunk_path.stat().st_size == 0:
                raise FFmpegError(f"Chunk file was not created: {chunk_path}")
            
            # Store chunk path and start time in milliseconds
            chunks.append((chunk_path, current_time * 1000))
            
        except subprocess.TimeoutExpired:
            raise FFmpegError(f"ffmpeg timed out while creating chunk {chunk_num}")
        
        current_time += actual_duration
    
    return chunks


def extract_audio_from_video(
    video_file: Path,
    output_file: Path,
    output_format: str = 'wav'
) -> Path:
    """Extract audio track from video file.
    
    Args:
        video_file: Path to input video file
        output_file: Path for output audio file
        output_format: Output format (wav, mp3, etc.)
        
    Returns:
        Path to extracted audio file
        
    Raises:
        FFmpegError: If ffmpeg fails
    """
    if not check_ffmpeg_installed():
        raise FFmpegError(get_ffmpeg_error_message())
    
    # Build codec settings based on format
    if output_format == 'wav':
        codec_args = ['-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1']
    elif output_format == 'mp3':
        codec_args = ['-acodec', 'libmp3lame', '-q:a', '2']
    else:
        codec_args = ['-acodec', 'copy']
    
    cmd = [
        'ffmpeg',
        '-y',  # Overwrite output
        '-i', str(video_file),
        '-vn',  # No video
        *codec_args,
        str(output_file)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=1800  # 30 minute timeout for long videos
        )
        
        if result.returncode != 0:
            raise FFmpegError(f"ffmpeg failed to extract audio: {result.stderr}")
        
        if not output_file.exists() or output_file.stat().st_size == 0:
            raise FFmpegError("Audio extraction produced empty file")
        
        return output_file
        
    except subprocess.TimeoutExpired:
        raise FFmpegError("ffmpeg timed out during audio extraction")


def convert_audio_format(
    input_file: Path,
    output_file: Path,
    output_format: str = 'wav'
) -> Path:
    """Convert audio file to different format.
    
    Args:
        input_file: Path to input audio file
        output_file: Path for output file
        output_format: Target format
        
    Returns:
        Path to converted file
        
    Raises:
        FFmpegError: If conversion fails
    """
    if not check_ffmpeg_installed():
        raise FFmpegError(get_ffmpeg_error_message())
    
    # Build codec settings based on format
    if output_format == 'wav':
        codec_args = ['-acodec', 'pcm_s16le', '-ar', '16000', '-ac', '1']
    elif output_format == 'mp3':
        codec_args = ['-acodec', 'libmp3lame', '-q:a', '2']
    else:
        codec_args = []
    
    cmd = [
        'ffmpeg',
        '-y',
        '-i', str(input_file),
        '-vn',
        *codec_args,
        str(output_file)
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minute timeout
        )
        
        if result.returncode != 0:
            raise FFmpegError(f"ffmpeg failed to convert audio: {result.stderr}")
        
        if not output_file.exists() or output_file.stat().st_size == 0:
            raise FFmpegError("Audio conversion produced empty file")
        
        return output_file
        
    except subprocess.TimeoutExpired:
        raise FFmpegError("ffmpeg timed out during audio conversion")


def calculate_chunk_duration_for_size(
    audio_file: Path,
    target_size_bytes: int
) -> float:
    """Calculate chunk duration to achieve target file size.
    
    Args:
        audio_file: Path to audio file
        target_size_bytes: Target size per chunk in bytes
        
    Returns:
        Recommended chunk duration in seconds
    """
    file_size = audio_file.stat().st_size
    duration = get_audio_duration(audio_file)
    
    if duration <= 0:
        return 300.0  # Default to 5 minutes
    
    # Calculate bytes per second
    bytes_per_second = file_size / duration
    
    # Calculate duration for target size
    chunk_duration = target_size_bytes / bytes_per_second
    
    # Ensure minimum 30 seconds, maximum 10 minutes
    chunk_duration = max(30.0, min(chunk_duration, 600.0))
    
    return chunk_duration

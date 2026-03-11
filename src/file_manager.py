"""File management module for saving transcripts and summaries."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from src.config import config

class FileManager:
    """Handles file operations for saving meeting data."""
    
    def __init__(self, meeting_id: Optional[str] = None):
        """Initialize file manager.
        
        Args:
            meeting_id: Optional custom meeting ID, otherwise uses timestamp
        """
        self.output_dir = config.output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate meeting ID based on timestamp
        if meeting_id:
            self.meeting_id = meeting_id
        else:
            self.meeting_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create meeting-specific directory
        self.meeting_dir = self.output_dir / f"meeting_{self.meeting_id}"
        self.meeting_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\n📁 Meeting files will be saved to: {self.meeting_dir}")
    
    def get_audio_file_path(self) -> Path:
        """Get path for audio file.
        
        Returns:
            Path for audio file
        """
        return self.meeting_dir / f"audio_{self.meeting_id}.wav"
    
    def save_transcript(self, transcript: str, filename: Optional[str] = None) -> Path:
        """Save transcript to file.
        
        Args:
            transcript: Transcript text
            filename: Optional custom filename
            
        Returns:
            Path to saved file
        """
        if not filename:
            filename = f"transcript_{self.meeting_id}.txt"
        
        filepath = self.meeting_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(transcript)
        
        print(f"📝 Transcript saved: {filepath.name}")
        return filepath
    
    def save_diarized_transcript(self, transcript: str, filename: Optional[str] = None) -> Path:
        """Save diarized transcript to file.
        
        Args:
            transcript: Diarized transcript text
            filename: Optional custom filename
            
        Returns:
            Path to saved file
        """
        if not filename:
            filename = f"transcript_diarized_{self.meeting_id}.md"
        
        filepath = self.meeting_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(transcript)
        
        print(f"👥 Diarized transcript saved: {filepath.name}")
        return filepath
    
    def save_summary(self, summary: str, filename: Optional[str] = None) -> Path:
        """Save meeting summary to file.
        
        Args:
            summary: Summary text
            filename: Optional custom filename
            
        Returns:
            Path to saved file
        """
        if not filename:
            filename = f"summary_{self.meeting_id}.md"
        
        filepath = self.meeting_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(summary)
        
        print(f"📝 Summary saved: {filepath.name}")
        return filepath
    
    def save_metadata(self, metadata: Dict[str, Any], filename: Optional[str] = None) -> Path:
        """Save meeting metadata to JSON file.
        
        Args:
            metadata: Metadata dictionary
            filename: Optional custom filename
            
        Returns:
            Path to saved file
        """
        if not filename:
            filename = f"metadata_{self.meeting_id}.json"
        
        filepath = self.meeting_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Metadata saved: {filepath.name}")
        return filepath
    
    def save_raw_data(self, data: Dict[str, Any], filename: str) -> Path:
        """Save raw data to JSON file.
        
        Args:
            data: Data to save
            filename: Filename
            
        Returns:
            Path to saved file
        """
        filepath = self.meeting_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def generate_report(self, metadata: Dict[str, Any]) -> str:
        """Generate a summary report of all files.
        
        Args:
            metadata: Meeting metadata
            
        Returns:
            Report text
        """
        report = []
        report.append("=" * 80)
        report.append("MEETING RECORDING REPORT")
        report.append("=" * 80)
        report.append("")
        report.append(f"Meeting ID: {self.meeting_id}")
        report.append(f"Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Output Directory: {self.meeting_dir}")
        report.append("")
        report.append("-" * 80)
        report.append("FILES GENERATED:")
        report.append("-" * 80)
        report.append("")
        
        # List all files in meeting directory
        files = sorted(self.meeting_dir.glob("*"))
        for i, file in enumerate(files, 1):
            size_kb = file.stat().st_size / 1024
            report.append(f"{i}. {file.name} ({size_kb:.2f} KB)")
        
        report.append("")
        report.append("-" * 80)
        report.append("MEETING STATISTICS:")
        report.append("-" * 80)
        report.append("")
        
        if 'duration' in metadata:
            duration_mins = metadata['duration'] / 60
            report.append(f"Duration: {duration_mins:.2f} minutes")
        
        if 'language' in metadata:
            report.append(f"Language: {metadata['language'].upper()}")
        
        if 'speakers_count' in metadata:
            report.append(f"Speakers Detected: {metadata['speakers_count']}")
        
        if 'transcription_time' in metadata:
            report.append(f"Transcription Time: {metadata['transcription_time']:.2f} seconds")
        
        if 'summary_time' in metadata:
            report.append(f"Summarization Time: {metadata['summary_time']:.2f} seconds")
        
        report.append("")
        report.append("-" * 80)
        report.append("=" * 80)
        
        return "\n".join(report)

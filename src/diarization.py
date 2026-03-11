"""Speaker diarization module."""

import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests
import json

from src.config import config

class SpeakerDiarizer:
    """Handles speaker diarization using various methods."""
    
    def __init__(self):
        """Initialize the diarizer."""
        self.min_speakers = config.min_speakers
        self.max_speakers = config.max_speakers
    
    def perform_diarization(self, audio_file: Path, transcription_result: Dict[str, Any]) -> Dict[str, Any]:
        """Perform speaker diarization.
        
        Args:
            audio_file: Path to audio file
            transcription_result: Transcription result with segments
            
        Returns:
            Dictionary containing diarization results
        """
        print(f"\n👥 Starting speaker diarization...")
        
        # For now, we'll use a simplified approach using OpenAI's capabilities
        # In production, you might want to use pyannote.audio or similar
        
        try:
            # Simple heuristic: assign speakers based on pauses
            segments = transcription_result.get('segments', [])
            
            if not segments:
                print("⚠️  No segments available for diarization")
                return {
                    'segments': [],
                    'speakers': []
                }
            
            diarized_segments = self._simple_diarization(segments)
            
            # Count unique speakers
            speakers = set(seg['speaker'] for seg in diarized_segments)
            
            print(f"✅ Diarization completed")
            print(f"   Detected {len(speakers)} speakers")
            
            return {
                'segments': diarized_segments,
                'speakers': list(speakers)
            }
            
        except Exception as e:
            print(f"❌ Diarization error: {e}")
            # Return original segments without speaker labels
            return {
                'segments': transcription_result.get('segments', []),
                'speakers': ['Speaker 1']
            }
    
    def _simple_diarization(self, segments: List[Dict]) -> List[Dict]:
        """Simple diarization based on pauses between segments.
        
        This is a simplified approach. For production, consider using:
        - pyannote.audio
        - AssemblyAI's speaker diarization
        - Rev.ai
        
        Args:
            segments: List of transcript segments
            
        Returns:
            List of segments with speaker labels
        """
        if not segments:
            return []
        
        diarized = []
        current_speaker = 1
        pause_threshold = 2.0  # seconds
        
        for i, segment in enumerate(segments):
            # Check for long pause indicating speaker change
            if i > 0:
                prev_end = segments[i-1].get('end', 0)
                curr_start = segment.get('start', 0)
                pause = curr_start - prev_end
                
                # Change speaker if there's a significant pause
                if pause > pause_threshold:
                    current_speaker = (current_speaker % self.max_speakers) + 1
            
            segment_copy = segment.copy()
            segment_copy['speaker'] = f"Speaker {current_speaker}"
            diarized.append(segment_copy)
        
        return diarized
    
    def format_diarized_transcript(self, diarization_result: Dict[str, Any], 
                                   transcription_result: Dict[str, Any]) -> str:
        """Format diarized transcript with speaker labels.
        
        Args:
            diarization_result: Diarization results
            transcription_result: Original transcription
            
        Returns:
            Formatted transcript with speaker labels
        """
        output = []
        output.append("=" * 80)
        output.append("MEETING TRANSCRIPT WITH SPEAKER LABELS")
        output.append("=" * 80)
        output.append("")
        
        if transcription_result.get('language'):
            output.append(f"Language: {transcription_result['language'].upper()}")
        if transcription_result.get('duration'):
            duration_mins = transcription_result['duration'] / 60
            output.append(f"Duration: {duration_mins:.2f} minutes")
        
        speakers = diarization_result.get('speakers', [])
        output.append(f"Speakers Detected: {len(speakers)}")
        output.append("")
        output.append("-" * 80)
        output.append("")
        
        # Add diarized segments
        segments = diarization_result.get('segments', [])
        current_speaker = None
        
        for segment in segments:
            start_time = segment.get('start', 0)
            text = segment.get('text', '').strip()
            speaker = segment.get('speaker', 'Unknown')
            
            # Format timestamp
            start_mm_ss = f"{int(start_time // 60):02d}:{int(start_time % 60):02d}"
            
            # Add speaker label when speaker changes
            if speaker != current_speaker:
                output.append("")
                output.append(f"**{speaker}** [{start_mm_ss}]")
                current_speaker = speaker
            else:
                output.append(f"[{start_mm_ss}] {text}")
                continue
            
            output.append(f"[{start_mm_ss}] {text}")
        
        output.append("")
        output.append("-" * 80)
        output.append("End of Transcript")
        output.append("=" * 80)
        
        return "\n".join(output)

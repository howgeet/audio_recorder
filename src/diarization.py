"""Speaker diarization module."""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.config import config


logger = logging.getLogger(__name__)

class SpeakerDiarizer:
    """Handles speaker diarization using various methods."""
    
    def __init__(self):
        """Initialize the diarizer."""
        self.min_speakers = config.min_speakers
        self.max_speakers = config.max_speakers
        self.use_pyannote = config.use_pyannote_diarization
        self.pyannote_model = config.pyannote_model
        self.hf_token = config.huggingface_token
    
    def perform_diarization(self, audio_file: Path, transcription_result: Dict[str, Any]) -> Dict[str, Any]:
        """Perform speaker diarization.
        
        Args:
            audio_file: Path to audio file
            transcription_result: Transcription result with segments
            
        Returns:
            Dictionary containing diarization results
        """
        print(f"\n👥 Starting speaker diarization...")
        
        try:
            segments = transcription_result.get('segments', [])
            
            if not segments:
                print("⚠️  No segments available for diarization")
                logger.warning("No transcription segments available for diarization")
                return {
                    'segments': [],
                    'speakers': []
                }

            # Preferred path: pyannote diarization + segment alignment
            if self.use_pyannote:
                try:
                    turns = self._run_pyannote_diarization(audio_file)
                    if turns:
                        diarized_segments = self._assign_speakers_from_turns(segments, turns)
                        speakers = sorted({seg['speaker'] for seg in diarized_segments})
                        print("✅ Diarization completed with pyannote")
                        print(f"   Detected {len(speakers)} speakers")
                        logger.info(
                            "pyannote diarization complete. file=%s turns=%d speakers=%d",
                            audio_file,
                            len(turns),
                            len(speakers),
                        )
                        return {
                            'segments': diarized_segments,
                            'speakers': speakers,
                            'method': 'pyannote'
                        }

                    logger.warning("pyannote produced no turns; falling back to heuristic diarization")
                except Exception as pyannote_error:
                    logger.exception("pyannote diarization failed; falling back to heuristic")
                    print(f"⚠️  Advanced diarization unavailable: {pyannote_error}")
            
            # Fallback path: simple heuristic based on pauses
            diarized_segments = self._simple_diarization(segments)
            
            # Count unique speakers
            speakers = set(seg['speaker'] for seg in diarized_segments)
            
            print(f"✅ Diarization completed (heuristic fallback)")
            print(f"   Detected {len(speakers)} speakers")
            logger.info("heuristic diarization complete. file=%s speakers=%d", audio_file, len(speakers))
            
            return {
                'segments': diarized_segments,
                'speakers': sorted(list(speakers)),
                'method': 'heuristic'
            }
            
        except Exception as e:
            print(f"❌ Diarization error: {e}")
            logger.exception("Diarization failed entirely")
            # Return original segments without speaker labels
            return {
                'segments': transcription_result.get('segments', []),
                'speakers': ['Speaker 1']
            }

    def _run_pyannote_diarization(self, audio_file: Path) -> List[Dict[str, Any]]:
        """Run pyannote diarization and return time turns with raw speaker labels."""
        try:
            import torch
            from pyannote.audio import Pipeline
        except Exception as import_error:
            raise RuntimeError(
                "pyannote diarization is unavailable. Install dependencies: pip install pyannote.audio"
            ) from import_error

        pipeline_kwargs = {}
        if self.hf_token:
            pipeline_kwargs["use_auth_token"] = self.hf_token

        pipeline = Pipeline.from_pretrained(self.pyannote_model, **pipeline_kwargs)

        if hasattr(pipeline, "to"):
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            pipeline.to(device)
            logger.info("pyannote pipeline device=%s", device)

        diarization = pipeline(
            str(audio_file),
            min_speakers=self.min_speakers,
            max_speakers=self.max_speakers,
        )

        turns: List[Dict[str, Any]] = []
        for turn, _, label in diarization.itertracks(yield_label=True):
            turns.append({
                "start": float(turn.start),
                "end": float(turn.end),
                "speaker": str(label),
            })

        turns.sort(key=lambda t: (t["start"], t["end"]))
        return turns

    def _assign_speakers_from_turns(
        self,
        segments: List[Dict[str, Any]],
        turns: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Assign a speaker to each Whisper segment using maximum overlap with diarization turns."""
        diarized: List[Dict[str, Any]] = []
        speaker_map: Dict[str, str] = {}
        next_speaker_idx = 1

        for segment in segments:
            seg_start = float(segment.get("start", 0.0) or 0.0)
            seg_end = float(segment.get("end", seg_start) or seg_start)

            best_label = None
            best_overlap = 0.0

            for turn in turns:
                overlap = max(0.0, min(seg_end, turn["end"]) - max(seg_start, turn["start"]))
                if overlap > best_overlap:
                    best_overlap = overlap
                    best_label = turn["speaker"]

            # If no overlap, use nearest diarization turn center by distance
            if best_label is None and turns:
                seg_mid = (seg_start + seg_end) / 2.0
                nearest = min(
                    turns,
                    key=lambda t: abs(seg_mid - ((t["start"] + t["end"]) / 2.0)),
                )
                best_label = nearest["speaker"]

            if best_label is None:
                best_label = "unknown"

            if best_label not in speaker_map:
                speaker_map[best_label] = f"Speaker {next_speaker_idx}"
                next_speaker_idx += 1

            seg_copy = segment.copy()
            seg_copy["speaker"] = speaker_map[best_label]
            diarized.append(seg_copy)

        return diarized
    
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

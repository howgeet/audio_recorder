"""Main application for Meeting Transcriber."""

import sys
import time
import signal
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from src.config import config
from src.audio_capture import AudioCapture, SimpleAudioCapture
from src.transcription import Transcriber
from src.diarization import SpeakerDiarizer
from src.summarization import MeetingSummarizer
from src.file_manager import FileManager

class MeetingTranscriber:
    """Main application class for meeting transcription."""
    
    def __init__(self, simple_mode: bool = False):
        """Initialize the meeting transcriber.
        
        Args:
            simple_mode: Use simplified audio capture (microphone only)
        """
        self.simple_mode = simple_mode
        self.file_manager: Optional[FileManager] = None
        self.audio_capture = None
        self.is_recording = False
        
        # Initialize components
        print("\n" + "=" * 80)
        print("MEETING TRANSCRIBER - Windows Compatible")
        print("=" * 80)
        print("")
        
        # Validate configuration
        is_valid, errors = config.validate()
        if not is_valid:
            print("❌ Configuration errors:")
            for error in errors:
                print(f"   - {error}")
            sys.exit(1)
        
        print("✅ Configuration validated")
        print(config)
        
    def start_recording(self):
        """Start recording a meeting."""
        try:
            print("\n" + "=" * 80)
            print("STARTING NEW MEETING RECORDING")
            print("=" * 80)
            
            # Initialize file manager
            self.file_manager = FileManager()
            audio_file = self.file_manager.get_audio_file_path()
            
            # Initialize audio capture
            if self.simple_mode:
                print("\n🔊 Using SIMPLE mode (microphone only)")
                self.audio_capture = SimpleAudioCapture(audio_file)
            else:
                print("\n🔊 Using FULL mode (microphone + system audio)")
                try:
                    self.audio_capture = AudioCapture(audio_file)
                except Exception as e:
                    print(f"\n⚠️  Failed to initialize full audio capture: {e}")
                    print("🔄 Falling back to SIMPLE mode (microphone only)")
                    self.audio_capture = SimpleAudioCapture(audio_file)
                    self.simple_mode = True
            
            # Start recording
            self.audio_capture.start_recording()
            self.is_recording = True
            
            print("\n" + "=" * 80)
            print("⏺ RECORDING IN PROGRESS")
            print("=" * 80)
            print("\nPress Ctrl+C or type 'stop' to end recording...\n")
            
        except Exception as e:
            print(f"\n❌ Error starting recording: {e}")
            raise
    
    def stop_recording(self):
        """Stop recording and process the meeting."""
        if not self.is_recording:
            print("⚠️  No recording in progress.")
            return
        
        try:
            print("\n" + "=" * 80)
            print("⏹️ STOPPING RECORDING")
            print("=" * 80)
            
            # Stop audio capture
            audio_file = self.audio_capture.stop_recording()
            audio_files: List[Path] = []
            if hasattr(self.audio_capture, 'get_recorded_files'):
                audio_files = [p for p in self.audio_capture.get_recorded_files() if p.exists() and p.stat().st_size > 0]

            self.is_recording = False

            if audio_files:
                print(f"\n✅ Audio parts saved: {len(audio_files)}")
                for part in audio_files:
                    print(f"   - {part.name} ({part.stat().st_size / (1024*1024):.2f} MB)")
            elif not audio_file.exists() or audio_file.stat().st_size == 0:
                print("❌ No audio recorded. Exiting.")
                return

            if not audio_files:
                print(f"\n✅ Audio file saved: {audio_file}")
                print(f"   Size: {audio_file.stat().st_size / (1024*1024):.2f} MB")
            
            # Process the recording
            self.process_meeting(audio_file, audio_files=audio_files)
            
        except Exception as e:
            print(f"\n❌ Error stopping recording: {e}")
            raise
    
    def process_meeting(self, audio_file: Path, audio_files: Optional[List[Path]] = None):
        """Process the recorded meeting.
        
        Args:
            audio_file: Path to recorded audio file (or first segment)
            audio_files: Optional list of recorded audio segments
        """
        print("\n" + "=" * 80)
        print("🛠️ PROCESSING MEETING")
        print("=" * 80)
        
        metadata = {
            'recording_date': datetime.now().isoformat(),
            'audio_file': str(audio_file),
            'mode': 'simple' if self.simple_mode else 'full'
        }
        
        try:
            # Step 1: Transcribe audio
            print("\n[1/4] Transcribing audio...")
            transcriber = Transcriber()
            start_time = time.time()
            valid_audio_files = [p for p in (audio_files or []) if p.exists() and p.stat().st_size > 0]
            if len(valid_audio_files) > 1:
                transcription_result = transcriber.transcribe_audio_files_with_retry(valid_audio_files)
                metadata['audio_parts'] = [str(p) for p in valid_audio_files]
            else:
                transcription_result = transcriber.transcribe_with_retry(audio_file)
            transcription_time = time.time() - start_time
            
            metadata['transcription_time'] = transcription_time
            metadata['language'] = transcription_result.get('language')
            metadata['duration'] = transcription_result.get('duration')
            
            # Save basic transcript
            transcript_text = transcriber.format_transcript(transcription_result)
            self.file_manager.save_transcript(transcript_text)
            
            # Step 2: Perform speaker diarization
            print("\n[2/4] Performing speaker diarization...")
            diarizer = SpeakerDiarizer()
            diarization_result = diarizer.perform_diarization(audio_file, transcription_result)
            
            metadata['speakers_count'] = len(diarization_result.get('speakers', []))
            
            # Save diarized transcript
            diarized_text = diarizer.format_diarized_transcript(diarization_result, transcription_result)
            self.file_manager.save_diarized_transcript(diarized_text)
            
            # Step 3: Generate summary
            print("\n[3/4] Generating meeting summary...")
            summarizer = MeetingSummarizer()
            start_time = time.time()
            summary_result = summarizer.generate_summary(
                transcription_result['text'],
                transcription_result.get('language', 'en')
            )
            summary_time = time.time() - start_time
            
            metadata['summary_time'] = summary_time
            
            # Save summary
            summary_text = summarizer.format_summary(summary_result)
            self.file_manager.save_summary(summary_text)
            
            # Step 4: Save metadata and generate report
            print("\n[4/4] Saving metadata and generating report...")
            self.file_manager.save_metadata(metadata)
            
            # Save raw data for future reference
            self.file_manager.save_raw_data(transcription_result, 'transcription_raw.json')
            self.file_manager.save_raw_data(diarization_result, 'diarization_raw.json')
            
            # Generate and display final report
            report = self.file_manager.generate_report(metadata)
            print("\n" + report)
            
            print("\n✅ Meeting processing completed successfully!")
            print(f"\n📂 All files saved to: {self.file_manager.meeting_dir}")
            
        except Exception as e:
            print(f"\n❌ Error processing meeting: {e}")
            import traceback
            traceback.print_exc()
            raise

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print("\n\n⏸️  Interrupt received. Stopping recording...")
    sys.exit(0)

def main():
    """Main entry point."""
    # Register signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Parse command-line arguments
    simple_mode = '--simple' in sys.argv or '-s' in sys.argv
    list_devices = '--list-devices' in sys.argv or '-l' in sys.argv
    
    if list_devices:
        print("\nListing available audio devices...\n")
        import sounddevice as sd
        print(sd.query_devices())
        return
    
    # Create transcriber instance
    app = MeetingTranscriber(simple_mode=simple_mode)
    
    try:
        # Start recording
        app.start_recording()
        
        # Wait for user input to stop
        while True:
            user_input = input("Type 'stop' and press Enter to end recording: ").strip().lower()
            if user_input == 'stop':
                break
            elif user_input:
                print("⚠️  Type 'stop' to end the recording.")
        
        # Stop recording and process
        app.stop_recording()
        
    except KeyboardInterrupt:
        print("\n\n⏸️  Stopping recording...")
        if app.is_recording:
            app.stop_recording()
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

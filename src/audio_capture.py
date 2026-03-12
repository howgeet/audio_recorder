"""Audio capture module for Windows - captures both microphone and system audio."""

import os
import wave
import threading
import time
from pathlib import Path
from typing import List
import numpy as np

try:
    import sounddevice as sd
    import soundcard as sc
except ImportError as e:
    print(f"Error importing audio libraries: {e}")
    print("Please install required packages: pip install sounddevice soundcard")
    raise

from src.config import config

class AudioCapture:
    """Handles audio capture from both microphone and system audio on Windows."""
    
    def __init__(self, output_file: Path):
        """Initialize audio capture.
        
        Args:
            output_file: Path to save the recorded audio
        """
        self.output_file = output_file
        self.sample_rate = config.sample_rate
        self.channels = config.channels
        self.is_recording = False
        self.mic_audio_data = []
        self.system_audio_data = []
        self.mic_samples_buffered = 0
        self.system_samples_buffered = 0
        self.segment_files: List[Path] = []
        self.segment_index = 1
        self.segment_duration_seconds = int(os.getenv("RECORDING_SEGMENT_SECONDS", "300"))
        self.segment_samples_target = max(1, self.segment_duration_seconds * self.sample_rate)
        self.lock = threading.Lock()
        
        # Get default devices
        self.mic_device = None
        self.system_device = None
        
    def list_devices(self):
        """List all available audio devices."""
        print("\n=== Available Audio Devices ===")
        print(sd.query_devices())
        
        print("\n=== Available Speakers/Loopback Devices ===")
        try:
            speakers = sc.all_speakers()
            for i, speaker in enumerate(speakers):
                print(f"{i}: {speaker.name}")
        except Exception as e:
            print(f"Error listing speakers: {e}")
    
    def start_recording(self):
        """Start recording audio from both microphone and system audio."""
        self.is_recording = True
        self.mic_audio_data = []
        self.system_audio_data = []
        self.mic_samples_buffered = 0
        self.system_samples_buffered = 0
        self.segment_files = []
        self.segment_index = 1
        
        print("\n🎤 Starting audio capture...")
        print(f"   Sample Rate: {self.sample_rate} Hz")
        print(f"   Channels: {self.channels}")
        
        # Start two threads: one for microphone, one for system audio
        self.mic_thread = threading.Thread(target=self._record_microphone, daemon=True)
        self.system_thread = threading.Thread(target=self._record_system_audio, daemon=True)
        
        self.mic_thread.start()
        self.system_thread.start()
        
        print("✅ Recording started successfully!")
    
    def _record_microphone(self):
        """Record from microphone."""
        try:
            def callback(indata, frames, time_info, status):
                if status:
                    print(f"Microphone status: {status}")
                if self.is_recording:
                    with self.lock:
                        mic_chunk = indata.copy()
                        self.mic_audio_data.append(mic_chunk)
                        self.mic_samples_buffered += len(mic_chunk)
                        while self._flush_next_segment_locked(force=False):
                            pass
            
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                callback=callback,
                dtype='float32'
            ):
                while self.is_recording:
                    time.sleep(0.1)
        except Exception as e:
            print(f"❌ Error recording microphone: {e}")
    
    def _record_system_audio(self):
        """Record system audio (loopback) on Windows using WASAPI loopback."""
        try:
            # On Windows, we need to get the loopback microphone for the default speaker
            # The soundcard library provides loopback devices as microphones with include_loopback=True
            default_speaker = sc.default_speaker()
            print(f"   🔊 Default speaker: {default_speaker.name}")
            
            # Get the loopback microphone for this speaker
            # Method 1: Try to get loopback mic directly from speaker ID
            loopback_mic = None
            try:
                loopback_mic = sc.get_microphone(id=str(default_speaker.id), include_loopback=True)
            except Exception:
                pass
            
            # Method 2: Search for loopback mic in all microphones
            if loopback_mic is None:
                all_mics = sc.all_microphones(include_loopback=True)
                # Look for a loopback device that matches the default speaker
                for mic in all_mics:
                    if hasattr(mic, 'isloopback') and mic.isloopback:
                        loopback_mic = mic
                        break
                # Fallback: find any mic with 'loopback' in name
                if loopback_mic is None:
                    for mic in all_mics:
                        if 'loopback' in mic.name.lower():
                            loopback_mic = mic
                            break
            
            if loopback_mic is None:
                print("❌ Could not find loopback device for system audio recording.")
                print("   Tip: On Windows, ensure 'Stereo Mix' or similar loopback device is enabled.")
                return
            
            print(f"   🔁 Using loopback device: {loopback_mic.name}")
            
            # Record from the loopback microphone
            with loopback_mic.recorder(samplerate=self.sample_rate, channels=self.channels) as recorder:
                print("   ✅ System audio capture initialized")
                while self.is_recording:
                    try:
                        # Record in small chunks (100ms)
                        data = recorder.record(numframes=int(self.sample_rate * 0.1))
                        if self.is_recording and data is not None and len(data) > 0:
                            with self.lock:
                                # Add system audio data to the recording
                                # Convert to float32 if needed and add to audio buffer
                                system_audio = data.astype(np.float32) if data.dtype != np.float32 else data
                                # Ensure correct shape (samples, channels)
                                if len(system_audio.shape) == 1:
                                    system_audio = system_audio.reshape(-1, 1)
                                if system_audio.shape[1] != self.channels:
                                    # Convert mono to stereo or vice versa
                                    if self.channels == 1 and system_audio.shape[1] > 1:
                                        system_audio = np.mean(system_audio, axis=1, keepdims=True)
                                    elif self.channels == 2 and system_audio.shape[1] == 1:
                                        system_audio = np.repeat(system_audio, 2, axis=1)
                                self.system_audio_data.append(system_audio)
                                self.system_samples_buffered += len(system_audio)
                                while self._flush_next_segment_locked(force=False):
                                    pass
                    except Exception as e:
                        if self.is_recording:
                            print(f"⚠️  System audio recording error: {e}")
                        break
        except Exception as e:
            print(f"❌ Error setting up system audio recording: {e}")
            print("   Note: System audio recording requires Windows with WASAPI loopback support.")
            print("   Tip: Make sure you have the 'soundcard' package installed: pip install soundcard")
    
    def stop_recording(self) -> Path:
        """Stop recording and save to file.
        
        Returns:
            Path to the saved audio file
        """
        print("\n🛑 Stopping recording...")
        self.is_recording = False
        
        # Wait for threads to finish
        if hasattr(self, 'mic_thread'):
            self.mic_thread.join(timeout=2)
        if hasattr(self, 'system_thread'):
            self.system_thread.join(timeout=2)

        with self.lock:
            while self._flush_next_segment_locked(force=False):
                pass
            self._flush_next_segment_locked(force=True)
        
        # Save audio data
        if self.segment_files:
            print(f"💾 Audio parts saved in: {self.output_file.parent}")
            print(f"✅ Audio saved successfully! ({len(self.segment_files)} wav parts)")
        else:
            print("⚠️  No audio data recorded!")
        
        return self.segment_files[0] if self.segment_files else self.output_file

    def get_recorded_files(self) -> List[Path]:
        """Return sorted list of recorded WAV part files."""
        return sorted(self.segment_files)
    
    def _available_samples_locked(self) -> int:
        """Get number of samples currently available for the next output segment."""
        if self.mic_audio_data and self.system_audio_data:
            return min(self.mic_samples_buffered, self.system_samples_buffered)
        if self.mic_audio_data:
            return self.mic_samples_buffered
        if self.system_audio_data:
            return self.system_samples_buffered
        return 0

    @staticmethod
    def _consume_samples(chunks: list, samples_needed: int) -> np.ndarray:
        """Consume a fixed number of samples from chunk list (in-place)."""
        consumed = []
        remaining = samples_needed
        while remaining > 0 and chunks:
            chunk = chunks[0]
            take = min(remaining, len(chunk))
            consumed.append(chunk[:take])
            if take == len(chunk):
                chunks.pop(0)
            else:
                chunks[0] = chunk[take:]
            remaining -= take

        if remaining > 0:
            raise ValueError("Not enough buffered samples to consume")

        return np.concatenate(consumed, axis=0) if consumed else np.empty((0, 1), dtype=np.float32)

    def _flush_next_segment_locked(self, force: bool) -> bool:
        """Flush one WAV segment from buffered samples.

        Returns True if a segment was written.
        """
        available = self._available_samples_locked()
        if available <= 0:
            return False

        if not force and available < self.segment_samples_target:
            return False

        segment_samples = available if force else self.segment_samples_target

        if self.mic_audio_data and self.system_audio_data:
            mic_array = self._consume_samples(self.mic_audio_data, segment_samples)
            system_array = self._consume_samples(self.system_audio_data, segment_samples)
            self.mic_samples_buffered -= segment_samples
            self.system_samples_buffered -= segment_samples
            audio_array = 0.5 * mic_array + 0.5 * system_array
        elif self.mic_audio_data:
            audio_array = self._consume_samples(self.mic_audio_data, segment_samples)
            self.mic_samples_buffered -= segment_samples
        else:
            audio_array = self._consume_samples(self.system_audio_data, segment_samples)
            self.system_samples_buffered -= segment_samples

        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        segment_path = self.output_file.with_name(
            f"{self.output_file.stem}_part{self.segment_index:03d}.wav"
        )
        self.segment_index += 1

        audio_clipped = np.clip(audio_array, -1.0, 1.0)
        audio_int16 = (audio_clipped * 32767).astype(np.int16)

        with wave.open(str(segment_path), 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_int16.tobytes())

        self.segment_files.append(segment_path)
        return True

class SimpleAudioCapture:
    """Simplified audio capture using only microphone (fallback option)."""
    
    def __init__(self, output_file: Path):
        """Initialize simple audio capture.
        
        Args:
            output_file: Path to save the recorded audio
        """
        self.output_file = output_file
        self.sample_rate = config.sample_rate
        self.channels = 1  # Mono for simplicity
        self.is_recording = False
        self.audio_data = []
        self.samples_buffered = 0
        self.segment_files: List[Path] = []
        self.segment_index = 1
        self.segment_duration_seconds = int(os.getenv("RECORDING_SEGMENT_SECONDS", "300"))
        self.segment_samples_target = max(1, self.segment_duration_seconds * self.sample_rate)
        self.lock = threading.Lock()
        
    def start_recording(self):
        """Start recording audio from microphone only."""
        self.is_recording = True
        self.audio_data = []
        self.samples_buffered = 0
        self.segment_files = []
        self.segment_index = 1
        
        print("\n🎤 Starting microphone recording (simplified mode)...")
        print(f"   Sample Rate: {self.sample_rate} Hz")
        
        def callback(indata, frames, time_info, status):
            if status:
                print(f"Status: {status}")
            if self.is_recording:
                with self.lock:
                    chunk = indata.copy()
                    self.audio_data.append(chunk)
                    self.samples_buffered += len(chunk)
                    while self._flush_next_segment_locked(force=False):
                        pass
        
        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            callback=callback,
            dtype='float32'
        )
        self.stream.start()
        print("✅ Recording started!")
    
    def stop_recording(self) -> Path:
        """Stop recording and save to file."""
        print("\n🛑 Stopping recording...")
        self.is_recording = False
        
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()

        with self.lock:
            while self._flush_next_segment_locked(force=False):
                pass
            self._flush_next_segment_locked(force=True)
        
        if self.segment_files:
            print(f"💾 Audio parts saved in: {self.output_file.parent}")
            print(f"✅ Audio saved! ({len(self.segment_files)} wav parts)")
        else:
            print("⚠️  No audio data recorded!")
        
        return self.segment_files[0] if self.segment_files else self.output_file

    def get_recorded_files(self) -> List[Path]:
        """Return sorted list of recorded WAV part files."""
        return sorted(self.segment_files)
    
    @staticmethod
    def _consume_samples(chunks: list, samples_needed: int) -> np.ndarray:
        consumed = []
        remaining = samples_needed
        while remaining > 0 and chunks:
            chunk = chunks[0]
            take = min(remaining, len(chunk))
            consumed.append(chunk[:take])
            if take == len(chunk):
                chunks.pop(0)
            else:
                chunks[0] = chunk[take:]
            remaining -= take

        if remaining > 0:
            raise ValueError("Not enough buffered samples to consume")

        return np.concatenate(consumed, axis=0) if consumed else np.empty((0, 1), dtype=np.float32)

    def _flush_next_segment_locked(self, force: bool) -> bool:
        if self.samples_buffered <= 0:
            return False
        if not force and self.samples_buffered < self.segment_samples_target:
            return False

        segment_samples = self.samples_buffered if force else self.segment_samples_target
        audio_array = self._consume_samples(self.audio_data, segment_samples)
        self.samples_buffered -= segment_samples

        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        segment_path = self.output_file.with_name(
            f"{self.output_file.stem}_part{self.segment_index:03d}.wav"
        )
        self.segment_index += 1

        audio_clipped = np.clip(audio_array, -1.0, 1.0)
        audio_int16 = (audio_clipped * 32767).astype(np.int16)

        with wave.open(str(segment_path), 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio_int16.tobytes())

        self.segment_files.append(segment_path)
        return True

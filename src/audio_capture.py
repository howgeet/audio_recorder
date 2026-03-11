"""Audio capture module for Windows - captures both microphone and system audio."""

import wave
import threading
import time
from pathlib import Path
from typing import Optional
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
        self.audio_data = []
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
        self.audio_data = []
        
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
                        self.audio_data.append(indata.copy())
            
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
                                self.audio_data.append(system_audio)
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
        
        # Save audio data
        if self.audio_data:
            print(f"💾 Saving audio to: {self.output_file}")
            self._save_audio()
            print(f"✅ Audio saved successfully! ({len(self.audio_data)} chunks)")
        else:
            print("⚠️  No audio data recorded!")
        
        return self.output_file
    
    def _save_audio(self):
        """Save recorded audio data to WAV file."""
        try:
            # Concatenate all audio chunks
            with self.lock:
                audio_array = np.concatenate(self.audio_data, axis=0)
            
            # Ensure output directory exists
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save as WAV file
            with wave.open(str(self.output_file), 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(self.sample_rate)
                
                # Convert float32 to int16
                audio_int16 = (audio_array * 32767).astype(np.int16)
                wf.writeframes(audio_int16.tobytes())
                
        except Exception as e:
            print(f"❌ Error saving audio file: {e}")
            raise

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
        
    def start_recording(self):
        """Start recording audio from microphone only."""
        self.is_recording = True
        self.audio_data = []
        
        print("\n🎤 Starting microphone recording (simplified mode)...")
        print(f"   Sample Rate: {self.sample_rate} Hz")
        
        def callback(indata, frames, time_info, status):
            if status:
                print(f"Status: {status}")
            if self.is_recording:
                self.audio_data.append(indata.copy())
        
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
        
        if self.audio_data:
            print(f"💾 Saving audio to: {self.output_file}")
            self._save_audio()
            print(f"✅ Audio saved! ({len(self.audio_data)} chunks)")
        else:
            print("⚠️  No audio data recorded!")
        
        return self.output_file
    
    def _save_audio(self):
        """Save recorded audio data to WAV file."""
        try:
            audio_array = np.concatenate(self.audio_data, axis=0)
            self.output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with wave.open(str(self.output_file), 'wb') as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                audio_int16 = (audio_array * 32767).astype(np.int16)
                wf.writeframes(audio_int16.tobytes())
        except Exception as e:
            print(f"❌ Error saving audio: {e}")
            raise

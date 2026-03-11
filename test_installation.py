#!/usr/bin/env python3
"""Test script to verify installation and configuration."""

import sys
import os
from pathlib import Path

def test_python_version():
    """Test Python version."""
    print("Testing Python version...", end=" ")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor} (Need 3.8+)")
        return False

def test_imports():
    """Test required imports."""
    print("\nTesting required packages:")
    
    packages = {
        'openai': 'OpenAI API client',
        'dotenv': 'Environment variables',
        'sounddevice': 'Audio recording',
        'soundcard': 'System audio (optional)',
        'numpy': 'Audio processing',
        'wave': 'WAV file support'
    }
    
    all_ok = True
    for package, description in packages.items():
        try:
            __import__(package)
            print(f"  ✅ {package:20s} - {description}")
        except ImportError:
            if package == 'soundcard':
                print(f"  ⚠️  {package:20s} - {description} (optional - use simple mode)")
            else:
                print(f"  ❌ {package:20s} - {description}")
                all_ok = False
    
    return all_ok

def test_project_structure():
    """Test project structure."""
    print("\nTesting project structure:")
    
    required_files = [
        'src/__init__.py',
        'src/main.py',
        'src/config.py',
        'src/audio_capture.py',
        'src/transcription.py',
        'src/diarization.py',
        'src/summarization.py',
        'src/file_manager.py',
        'requirements.txt',
        '.env.example',
        'README.md'
    ]
    
    all_ok = True
    for file in required_files:
        path = Path(file)
        if path.exists():
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - MISSING")
            all_ok = False
    
    return all_ok

def test_configuration():
    """Test configuration."""
    print("\nTesting configuration:")
    
    # Check if .env exists
    if not Path('.env').exists():
        print("  ⚠️  .env file not found")
        print("     Please copy .env.example to .env and configure your API keys")
        return False
    
    print("  ✅ .env file exists")
    
    # Try to load configuration
    try:
        from src.config import config
        print("  ✅ Configuration loaded")
        
        # Check API key
        if config.openai_api_key and config.openai_api_key != "your_openai_api_key_here":
            print("  ✅ OpenAI API key configured")
            return True
        else:
            print("  ⚠️  OpenAI API key not configured")
            print("     Please edit .env and add your OPENAI_API_KEY")
            return False
            
    except Exception as e:
        print(f"  ❌ Error loading configuration: {e}")
        return False

def test_audio_devices():
    """Test audio devices."""
    print("\nTesting audio devices:")
    
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        
        # Count input devices
        input_devices = [d for d in devices if d['max_input_channels'] > 0]
        
        if input_devices:
            print(f"  ✅ Found {len(input_devices)} input device(s)")
            print(f"\nDefault input device:")
            default_input = sd.query_devices(kind='input')
            print(f"    {default_input['name']}")
            return True
        else:
            print("  ⚠️  No input devices found")
            print("     Please check your microphone connection")
            return False
            
    except Exception as e:
        print(f"  ❌ Error checking audio devices: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 80)
    print("Meeting Transcriber - Installation Test")
    print("=" * 80)
    print()
    
    results = []
    
    # Run tests
    results.append(("Python Version", test_python_version()))
    results.append(("Required Packages", test_imports()))
    results.append(("Project Structure", test_project_structure()))
    results.append(("Configuration", test_configuration()))
    results.append(("Audio Devices", test_audio_devices()))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print()
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:10s} {test_name}")
    
    print()
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("🎉 All tests passed! Your installation is ready.")
        print("\nTo run the application:")
        print("  - Windows: Double-click run.bat or run_simple.bat")
        print("  - Command line: python -m src.main")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("  - Run: setup.bat (Windows)")
        print("  - Copy .env.example to .env and configure your API key")
        print("  - Install missing packages: pip install -r requirements.txt")
    
    print("\n" + "=" * 80)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

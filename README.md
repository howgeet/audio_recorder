# Meeting Transcriber

A comprehensive Windows-compatible application for automatically transcribing, diarizing, and summarizing meetings with support for Turkish and English languages.

## 🎯 Features

- **🖥️ Modern GUI Interface** (Recommended): Professional graphical interface with intuitive controls, real-time status, and tabbed results display
- **🎤 Audio Capture**: Records both microphone input and system audio simultaneously on Windows
- **📁 Process Existing Files**: Import and transcribe existing audio/video files (MP3, MP4, WAV, M4A, AVI, MOV, and more)
- **📝 Real-time Transcription**: Uses OpenAI Whisper API for accurate speech-to-text conversion
- **👥 Speaker Diarization**: Identifies and labels different speakers in the conversation
- **📊 AI-Powered Summarization**: Generates comprehensive summaries with key points, decisions, and action items
- **🌍 Multi-language Support**: Handles both Turkish and English (auto-detects language)
- **💾 Organized File Management**: Saves transcripts, summaries, and metadata with timestamps
- **📟 CLI Interface**: Command-line interface available for automation and scripting

## 📋 Requirements

- **Windows 10/11** (Primary platform)
- **Python 3.8 - 3.13** (Python 3.13+ fully supported!)
- **FFmpeg** ⚠️ **REQUIRED** (for audio/video processing)
- **OpenAI API Key** (for transcription and summarization)
- **Microphone** (for audio input)
- **Internet connection** (for API calls)

### ⚠️ FFmpeg Installation (Required)

FFmpeg is **required** for audio processing (chunking large files, video-to-audio conversion).

**Windows** (choose one):
```bash
# Option 1: Using winget (recommended)
winget install ffmpeg

# Option 2: Using Chocolatey
choco install ffmpeg

# Option 3: Manual download from https://ffmpeg.org/download.html
```

**macOS**:
```bash
brew install ffmpeg
```

**Linux**:
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# Fedora/CentOS
sudo dnf install ffmpeg
```

After installation, verify with: `ffmpeg -version`

## 🚀 Quick Start (GUI - Recommended)

### The easiest way to get started is with the GUI:

```
1. Double-click: setup.bat          (First time only)
2. Configure your OpenAI API key in .env
3. Double-click: run_gui.bat        ← Start here!
```

That's it! The GUI will guide you through the rest.

---

## 📦 Installation

### Option A: Automated Setup (Recommended)

1. Download or clone this repository
2. Double-click `setup.bat` to run the automated setup
3. Follow the on-screen instructions

### Option B: Manual Setup

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate.bat

# Install dependencies (includes GUI dependencies)
pip install -r requirements.txt

# Copy environment template
copy .env.example .env
```

### GUI Dependencies

The GUI requires `PySide6` which is automatically installed via `requirements.txt`:
```
PySide6>=6.6.0
```

---

## ⚙️ Configuration

1. **Get your OpenAI API Key**:
   - Visit [OpenAI Platform](https://platform.openai.com/api-keys)
   - Create a new API key
   - Copy the key

2. **Configure the application**:
   - Open the `.env` file in a text editor
   - Replace `your_openai_api_key_here` with your actual API key
   - Adjust other settings if needed

Example `.env` configuration:
```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
WHISPER_MODEL=whisper-1
LLM_MODEL=gpt-4o-mini
OUTPUT_DIR=outputs
```

> 💡 **Tip**: You can also configure the API key directly in the GUI via the Settings button!

---

## 🖥️ Using the GUI (Recommended)

### Starting the GUI

**Double-click `run_gui.bat`** - This is the recommended way to use Meeting Transcriber!

Or from command line:
```bash
python -m src.gui_app
```

### GUI Features at a Glance

| Feature | Description |
|---------|-------------|
| 🟢 **Start Recording** | Click to begin recording your meeting |
| 🔴 **Stop Recording** | Click to stop and automatically process |
| 📁 **Process File** | Import and transcribe existing audio/video files |
| ⏱️ **Timer** | Real-time display of recording duration |
| 📊 **Status Indicator** | Visual feedback (Idle/Recording/Processing/Complete) |
| 🎯 **Mode Indicator** | Shows current mode (Live Recording vs File Processing) |
| 📈 **Audio Level Meter** | See your microphone input levels |
| 📝 **Transcript Tab** | View full transcript with timestamps |
| 📋 **Summary Tab** | AI-generated meeting summary |
| 📌 **Notes Tab** | Speaker-labeled transcript (diarized) |
| 📊 **Activity Log** | Real-time processing updates |
| ⚙️ **Settings** | Configure API keys, output directory, and model |
| 💾 **Save Buttons** | Export results to files |

### Step-by-Step GUI Usage

1. **Launch**: Double-click `run_gui.bat`
2. **Configure** (first time): Click ⚙️ Settings to enter your API key
3. **Start Recording**: Click the green "Start Recording" button
4. **Conduct your meeting**: The GUI shows recording status and timer
5. **Stop Recording**: Click the red "Stop Recording" button
6. **Wait for Processing**: Watch the progress bar and activity log
7. **Review Results**: Browse through the Transcript, Summary, and Notes tabs
8. **Save**: Click save buttons to export results to files

### GUI Settings Dialog

Access settings by clicking the ⚙️ button:

- **OpenAI API Key**: Your API key for transcription and summarization
- **Output Directory**: Where to save meeting files
- **LLM Model**: Choose between gpt-4o-mini (default), gpt-4o, or gpt-3.5-turbo
- **Local Whisper Model**: Choose offline fallback model size (tiny / base / small / medium / large-v2 / large-v3)

---

## 📁 Processing Existing Audio/Video Files

In addition to live recording, you can process existing audio and video files:

### Supported Formats

| Type | Formats |
|------|---------|
| **Audio** | `.mp3`, `.wav`, `.m4a`, `.flac`, `.ogg`, `.webm`, `.aac`, `.wma` |
| **Video** | `.mp4`, `.avi`, `.mov`, `.mkv`, `.wmv`, `.flv`, `.webm` |

### How to Process an Existing File

1. **Click "Process File"** button in the GUI
2. **Select your file** using the file browser
3. **Confirm processing** - you'll see file info (name, size, format)
4. **Wait for processing**:
   - For video files, audio will be extracted first
   - Then transcription, diarization, and summarization
5. **Review results** in the Transcript, Summary, and Notes tabs

### Important Notes

- **Video files**: Audio is automatically extracted using FFmpeg
- **Large files**: Files over 24MB are automatically chunked for transcription using FFmpeg
- **Mode indicator**: Shows whether you're in "Live Recording" or "File Processing" mode
- **FFmpeg requirement**: FFmpeg is **REQUIRED** for all audio/video processing (see Requirements section above)

---

## 📟 Alternative: Command Line Interface (CLI)

For advanced users, automation, or scripting, CLI options are available:

### CLI Launcher Scripts

| Script | Description | When to Use |
|--------|-------------|-------------|
| `run.bat` | Full mode (mic + system audio) | Advanced: Capture all meeting audio |
| `run_simple.bat` | Simple mode (microphone only) | Fallback: If system audio fails |

### CLI Commands

```bash
# Activate virtual environment
venv\Scripts\activate.bat

# Run full mode
python -m src.main

# Run simple mode (microphone only)
python -m src.main --simple

# List audio devices
python -m src.main --list-devices
```

### When to Use CLI vs GUI

| Use Case | Recommended |
|----------|-------------|
| Daily meeting recording | 🖥️ GUI |
| First-time users | 🖥️ GUI |
| Batch processing | 📟 CLI |
| Automation/scripting | 📟 CLI |
| Server environments | 📟 CLI |
| Troubleshooting audio | 📟 CLI (--list-devices) |

---

## 📁 Output Files

Each meeting creates a dedicated folder with the following files:

```
outputs/meeting_20260311_143022/
├── audio_20260311_143022.wav           # Original audio recording
├── transcript_20260311_143022.txt      # Basic transcript with timestamps
├── transcript_diarized_20260311_143022.md  # Transcript with speaker labels
├── summary_20260311_143022.md          # AI-generated meeting summary
├── metadata_20260311_143022.json       # Meeting metadata
├── transcription_raw.json              # Raw transcription data
└── diarization_raw.json                # Raw diarization data
```

### File Descriptions

1. **Audio File** (`.wav`): Raw audio recording of the meeting
2. **Basic Transcript** (`.txt`): Timestamped transcription without speaker labels
3. **Diarized Transcript** (`.md`): Transcript with speaker identification
4. **Summary** (`.md`): Comprehensive summary including:
   - Executive summary
   - Key discussion points
   - Decisions made
   - Action items with responsible parties
   - Next steps
5. **Metadata** (`.json`): Technical details about the recording
6. **Raw Data** (`.json`): Complete API responses for advanced analysis

---

## ⚙️ Configuration Options

Edit the `.env` file to customize behavior:

### API Settings

```env
# Required
OPENAI_API_KEY=your_key_here

# Optional (for advanced diarization)
HUGGINGFACE_TOKEN=your_token_here
```

### Audio Settings

```env
SAMPLE_RATE=16000      # Audio sample rate (Hz)
CHANNELS=2             # 1 for mono, 2 for stereo
CHUNK_SIZE=1024        # Audio buffer size
```

### Transcription Settings

```env
WHISPER_MODEL=whisper-1      # OpenAI Whisper model
LOCAL_WHISPER_MODEL=base     # Offline fallback model (tiny/base/small/medium/large-v2/large-v3)
```

### Summarization Settings

```env
LLM_MODEL=gpt-4o-mini    # Options: gpt-4o-mini, gpt-4o, gpt-3.5-turbo
TEMPERATURE=0.3          # Lower = more focused, Higher = more creative

# Hugging Face transformers fallback (used if OpenAI summarization fails)
HF_SUMMARY_MODEL=facebook/bart-large-cnn
HF_SUMMARY_MAX_CHARS=12000
```

### Logging Settings

```env
# Persistent diagnostic log file (relative paths are resolved from project root)
LOG_FILE=logs/audio_recorder.log
```

### Output Settings

```env
OUTPUT_DIR=outputs       # Directory for saving files
```

### Diarization Settings

```env
MIN_SPEAKERS=2          # Minimum expected speakers
MAX_SPEAKERS=10         # Maximum expected speakers

# Advanced diarization (recommended)
USE_PYANNOTE_DIARIZATION=true
PYANNOTE_MODEL=pyannote/speaker-diarization-3.1
```

---

## 🔧 Troubleshooting

### GUI-Specific Issues

#### Issue: GUI window doesn't appear

**Solutions**:
1. Ensure `PySide6` is installed:
   ```bash
   pip install PySide6>=6.6.0
   ```
2. Run setup.bat again to reinstall dependencies
3. Try running from command line to see error messages:
   ```bash
   python -m src.gui_app
   ```

#### Issue: GUI freezes during processing

**Explanation**: This shouldn't happen as processing runs in background threads. If it does:
1. Wait - processing can take several minutes for long meetings
2. Check the Activity Log tab for progress updates
3. Restart the application if completely frozen

#### Issue: Settings not saving

**Solution**: 
- Ensure you have write permissions to the `.env` file
- Check that the output directory exists or can be created

### FFmpeg Issues

#### Issue: "FFmpeg is not installed" or "ffmpeg not found"

**Solution**: FFmpeg must be installed separately (it's not a Python package).

**Windows**:
```bash
# Using winget (recommended)
winget install ffmpeg

# Or using Chocolatey
choco install ffmpeg

# Or download manually from https://ffmpeg.org/download.html
# and add to your system PATH
```

**macOS**:
```bash
brew install ffmpeg
```

**Linux**:
```bash
sudo apt install ffmpeg  # Ubuntu/Debian
sudo dnf install ffmpeg  # Fedora
```

After installation, restart your terminal/application and verify with:
```bash
ffmpeg -version
```

#### Issue: "Error code 413 - Maximum content size limit exceeded"

**Explanation**: This error occurs when audio files are too large for the API.

**Solution**: This should be handled automatically by the app's chunking feature. If you still see this error:
1. Ensure FFmpeg is installed correctly
2. Check the Activity Log for more details
3. Try processing a smaller audio file first

### General Issues

#### Issue: OpenAI summarization fails (timeout/network/API error)

**Behavior**:
- The app first tries OpenAI ChatGPT summarization.
- If that fails, it automatically falls back to **Hugging Face transformers** using the Whisper transcript text.

If both fail, check the log file for full stack traces.

#### Issue: Need diagnostic logs

The app writes logs to:

```text
logs/audio_recorder.log
```

You can override the path using `LOG_FILE` in `.env`.

#### Issue: "OpenAI API key is not configured"

**Solution**: 
- Use the GUI Settings dialog to enter your API key, or
- Edit the `.env` file manually
- Verify there are no extra spaces or quotes

#### Issue: System audio not recording

**Possible causes**:
- System audio recording requires additional permissions on Windows
- Some audio configurations may not support loopback recording

**Solutions**:
1. Use `run_simple.bat` (CLI) or just use microphone input
2. Check Windows audio settings:
   - Ensure "Stereo Mix" or similar loopback device is enabled
   - Right-click speaker icon → Sounds → Recording tab
   - Enable "Show Disabled Devices"

3. Use virtual audio cable software:
   - Install [VB-Audio Virtual Cable](https://vb-audio.com/Cable/)
   - Configure Windows to route audio through virtual cable

#### Issue: Speaker separation is weak / incorrect

**Current behavior**:
- The app now tries **pyannote.audio** diarization first (voice-based speaker turns).
- If pyannote is unavailable or fails, it falls back to pause-based heuristic diarization.

**How to improve results**:
1. Install dependencies: `pip install -r requirements.txt`
2. Set `HUGGINGFACE_TOKEN` in `.env` (required for gated pyannote models)
3. Ensure your token has accepted the model terms on Hugging Face
4. Keep `USE_PYANNOTE_DIARIZATION=true`

#### Issue: "No module named 'sounddevice'" or similar

**Solution**:
```bash
# Activate virtual environment
venv\Scripts\activate.bat

# Reinstall dependencies
pip install -r requirements.txt
```

#### Issue: Poor transcription quality

**Solutions**:
1. Use a good quality microphone
2. Minimize background noise
3. Ensure clear audio input
4. Check the audio level meter in the GUI

#### Issue: Processing is slow

**Explanation**: Processing time depends on:
- Meeting length
- Internet speed
- OpenAI API response times

**Typical times**:
- 30-minute meeting: 2-5 minutes processing
- 60-minute meeting: 4-10 minutes processing

**Tips**:
- Watch the progress bar and activity log in the GUI
- Don't interrupt the process
- Ensure stable internet connection

---

## 🎓 Advanced Usage

### Using Different LLM Models

Configure in GUI Settings or edit `.env`:

```env
# Budget-friendly (default)
LLM_MODEL=gpt-4o-mini

# Better quality
LLM_MODEL=gpt-4o

# Fastest
LLM_MODEL=gpt-3.5-turbo
```

### Custom Output Directory

Configure in GUI Settings or edit `.env`:

```env
OUTPUT_DIR=C:\Users\YourName\Documents\Meetings
```

### Adjusting Summary Detail

```env
# More focused summaries (0.0 - 0.5)
TEMPERATURE=0.2

# More comprehensive summaries (0.5 - 1.0)
TEMPERATURE=0.7
```

---

## 🏗️ Project Structure

```
meeting_transcriber/
├── src/
│   ├── __init__.py              # Package initialization
│   ├── main.py                  # CLI application entry point
│   ├── gui_app.py               # GUI application (PySide6)
│   ├── config.py                # Configuration management
│   ├── audio_capture.py         # Audio recording module
│   ├── transcription.py         # Whisper API transcription
│   ├── diarization.py           # Speaker diarization
│   ├── summarization.py         # LLM-based summarization
│   ├── file_manager.py          # File operations
│   └── ffmpeg_utils.py          # FFmpeg wrapper functions
├── outputs/                     # Generated meeting files
├── tests/                       # Unit tests (future)
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment template
├── .gitignore                   # Git ignore rules
├── setup.bat                    # Windows setup script
├── run_gui.bat                  # GUI launcher (RECOMMENDED)
├── run.bat                      # CLI full mode launcher
├── run_simple.bat               # CLI simple mode launcher
└── README.md                    # This file
```

---

## 🔐 Security & Privacy

- **API Keys**: Never commit `.env` file to version control
- **Audio Files**: Stored locally, never uploaded except to OpenAI API
- **Data Privacy**: OpenAI's data usage policy applies to transcriptions
- **Local Storage**: All output files remain on your computer

---

## 💰 Cost Estimate

| Meeting Length | Estimated Cost |
|----------------|----------------|
| 30 minutes | ~$0.20 |
| 60 minutes | ~$0.40 |
| 90 minutes | ~$0.60 |

Very affordable for professional use!

---

## 📝 License

This project is provided as-is for personal and commercial use.

---

## 🤝 Contributing

Contributions are welcome! Areas for improvement:
- Advanced speaker diarization integration
- Real-time transcription display
- Support for additional languages
- Cloud storage integration
- Export to different formats (DOCX, PDF)

---

## 📞 Support

For issues and questions:
1. Check the Troubleshooting section above
2. Review the configuration in `.env` or GUI Settings
3. Check OpenAI API status: https://status.openai.com/

---

## 📈 Roadmap

- [x] GUI interface (PySide6) ✅
- [x] Settings dialog for easy configuration ✅
- [x] Real-time status indicators ✅
- [x] Tabbed interface for results ✅
- [x] Process existing audio/video files ✅
- [x] Audio extraction from video files ✅
- [ ] Real-time transcription display
- [ ] Advanced speaker diarization (pyannote.audio integration)
- [ ] Multi-file batch processing
- [ ] Export to different formats (DOCX, PDF)
- [ ] Cloud storage integration (Google Drive, OneDrive)
- [ ] Meeting analytics dashboard
- [ ] Custom vocabulary support
- [ ] Timestamp-based navigation

---

## 🔄 Version History

### Version 2.0.0 (Current)
- **Changed**: Replaced CustomTkinter GUI with PySide6 — removed all tkinter dependencies
- **New**: Local offline transcription fallback using `faster-whisper` (no API key required)
- **New**: Configurable local Whisper model size (tiny → large-v3) in Settings dialog
- **New**: Graceful degradation — summarization skipped (not aborted) when OpenAI is unavailable
- **Fixed**: API key can now be fully cleared from the Settings dialog
- **Improved**: Dark-themed PySide6 UI with QSS stylesheet; no external theme files needed

### Version 1.3.0
- **Fixed**: Python 3.13 compatibility (removed pydub dependency)
- **Changed**: Replaced pydub with direct FFmpeg subprocess calls
- **Improved**: Better cross-platform audio processing
- **Note**: FFmpeg is now a **required** external dependency

### Version 1.2.0
- **New**: Process existing audio/video files feature
- **New**: Support for multiple formats (MP3, MP4, WAV, M4A, AVI, MOV, FLAC, OGG, WebM, etc.)
- **New**: Audio extraction from video files using FFmpeg
- **New**: Mode indicator showing Live Recording vs File Processing
- **New**: File info display (name, size, format)
- **Improved**: Better button state management during recording/processing

### Version 1.1.0
- **New**: Modern GUI interface (originally CustomTkinter)
- **New**: `run_gui.bat` launcher for easy GUI access
- **New**: Settings dialog for API key and model configuration
- **New**: Real-time status indicators and activity log
- **New**: Tabbed interface for transcript, summary, and notes
- **New**: Audio level meter
- **New**: Progress bar for processing

### Version 1.0.0
- Initial release
- Basic audio capture (microphone + system audio)
- Whisper API transcription
- Simple speaker diarization
- LLM-based summarization
- File management system
- CLI interface

---

**Made with ❤️ for productive meetings**

For the latest updates and documentation, visit the project repository.

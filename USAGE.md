# Usage Guide

## 🖥️ GUI Mode (Recommended)

The graphical interface is the easiest and most intuitive way to use Meeting Transcriber.

### Starting the GUI

```
Double-click: run_gui.bat
```

Or from command line:
```bash
python -m src.gui_app
```

---

## GUI Interface Overview

### Main Window Layout

```
┌─────────────────────────────────────────────────────────┐
│  Meeting Transcriber                           [⚙️]     │
├─────────────────────────────────────────────────────────┤
│  [🟢 Start]  [🔴 Stop]  │  [📁 Process File]            │
│                                                         │
│  Status: ● Idle        Timer: 00:00:00                 │
│                                                         │
│  Mode: 🎤 Live Recording Mode                          │
│  Audio Level: [▓▓▓▓▓░░░░░░░░░░░░░░░░░░░]               │
├─────────────────────────────────────────────────────────┤
│  [Transcript] [Summary] [Notes] [Activity Log]          │
│  ┌─────────────────────────────────────────────────┐   │
│  │                                                 │   │
│  │    (Content displays here based on tab)        │   │
│  │                                                 │   │
│  └─────────────────────────────────────────────────┘   │
│                                         [💾 Save]       │
├─────────────────────────────────────────────────────────┤
│  Processing: [▓▓▓▓▓▓▓▓▓░░░░░░░░░░] 45%                 │
└─────────────────────────────────────────────────────────┘
```

### Control Panel

| Element | Description |
|---------|-------------|
| **Start Recording** | Green button - begins live audio capture |
| **Stop Recording** | Red button - stops recording and starts processing |
| **Process File** | Blue button - import existing audio/video file for processing |
| **Status Indicator** | Shows current state: Idle, Recording, Processing, Complete |
| **Mode Indicator** | Shows "Live Recording Mode" or "File Processing: filename" |
| **Timer** | Displays recording duration in HH:MM:SS format |
| **Audio Level Meter** | Real-time visualization of microphone input |
| **Settings Button (⚙️)** | Opens configuration dialog |

### Tabs

| Tab | Content |
|-----|---------|
| **Transcript** | Full transcription with timestamps |
| **Summary** | AI-generated meeting summary with key points, decisions, action items |
| **Notes** | Speaker-diarized transcript (who said what) |
| **Activity Log** | Real-time processing updates and status messages |

### Progress Bar

Shows processing progress during transcription and summarization.

---

## Step-by-Step Guide

### 1. First-Time Setup

1. **Open Settings** (⚙️ button)
2. **Enter your OpenAI API Key**
3. **Set Output Directory** (optional, defaults to `outputs`)
4. **Choose LLM Model** (optional, defaults to `gpt-4o-mini`)
5. **Click Save**

### 2. Recording a Meeting

1. **Click "Start Recording"**
   - Status changes to "Recording" (with blinking indicator)
   - Timer starts counting
   - Audio level meter shows input

2. **Conduct your meeting**
   - Join Teams/Zoom/Meet as normal
   - Speak clearly into microphone
   - The app records in the background

3. **Click "Stop Recording"**
   - Status changes to "Processing"
   - Progress bar appears

### 3. Processing

After stopping, the app automatically:
- ✓ Saves audio file
- ✓ Transcribes using Whisper API
- ✓ Identifies speakers (diarization)
- ✓ Generates AI summary

Watch the **Activity Log** tab for real-time updates.

### 4. Reviewing Results

Switch between tabs to view:

- **Transcript Tab**: Full text with timestamps
  ```
  [00:00:15] Hello everyone, welcome to today's meeting.
  [00:00:22] Let's start with the agenda...
  ```

- **Summary Tab**: Structured summary
  ```markdown
  ## Executive Summary
  Meeting discussed Q1 results and Q2 planning...
  
  ## Key Points
  - Revenue increased 15%
  - New product launch scheduled for April
  
  ## Action Items
  - [ ] John: Prepare Q2 budget (Due: March 20)
  ```

- **Notes Tab**: Speaker-labeled transcript
  ```
  Speaker 1: Hello everyone, welcome to today's meeting.
  Speaker 2: Thank you. Let's start with the agenda.
  ```

### 5. Saving Files

Click the **Save** button in each tab to export:
- Transcript → `transcript_YYYYMMDD_HHMMSS.txt`
- Summary → `summary_YYYYMMDD_HHMMSS.md`
- Notes → `transcript_diarized_YYYYMMDD_HHMMSS.md`

Files save to: `outputs/meeting_YYYYMMDD_HHMMSS/`

---

## Processing Existing Files

Instead of live recording, you can process existing audio or video files.

### Supported Formats

| Type | Extensions |
|------|------------|
| **Audio** | `.mp3`, `.wav`, `.m4a`, `.flac`, `.ogg`, `.webm`, `.aac`, `.wma` |
| **Video** | `.mp4`, `.avi`, `.mov`, `.mkv`, `.wmv`, `.flv`, `.webm` |

### How to Process a File

1. **Click "Process File"** (blue button)
2. **Browse and select** your audio/video file
3. **Review file info** in the confirmation dialog:
   - File name
   - File size
   - Format type
4. **Click Yes** to start processing
5. **Watch Activity Log** for progress:
   - For video: "Extracting audio from video..."
   - "Converting to WAV format..."
   - "Starting transcription..."
   - "Processing chunk 1 of 2..." (for large files)
   - "Generating summary..."
6. **Review results** in the tabs

### Processing Steps

For **audio files**:
1. File converted to WAV if needed
2. Transcribed using Whisper API
3. Speaker diarization applied
4. Summary generated

For **video files**:
1. Audio extracted from video (requires FFmpeg)
2. Converted to WAV
3. Same processing as audio files

### Mode Indicator

The mode indicator shows which mode is active:
- `🎤 Live Recording Mode` - Normal recording mode
- `📁 File Processing: meeting.mp4` - Currently processing a file

### Important Notes

- **Large files** (>24MB) are automatically split into chunks
- **Video files** require FFmpeg to be installed
- **Processing time** depends on file length and internet speed
- **Both modes** use the same output format and tabs

---

## Settings Dialog

Access via the ⚙️ button.

### Available Settings

| Setting | Description | Default |
|---------|-------------|---------|
| **OpenAI API Key** | Required for transcription and summarization | (none) |
| **Output Directory** | Where meeting files are saved | `outputs` |
| **LLM Model** | Model for summarization | `gpt-4o-mini` |

### LLM Model Options

| Model | Speed | Quality | Cost |
|-------|-------|---------|------|
| `gpt-4o-mini` | Fast | Good | $ |
| `gpt-4o` | Medium | Best | $$$ |
| `gpt-3.5-turbo` | Fastest | Basic | $ |

---

## Tips for Best Results

### Audio Quality
- ✓ Use a good quality microphone
- ✓ Minimize background noise
- ✓ Speak clearly and at normal pace
- ✓ Position microphone appropriately

### During Recording
- ✓ Watch the audio level meter - ensure it's responding
- ✓ Keep the GUI open (minimize if needed)
- ✓ Don't close the application during recording

### Processing
- ✓ Wait for processing to complete
- ✓ Watch the progress bar and activity log
- ✓ Typical times: 2-5 min for 30-min meeting

---

## GUI Troubleshooting

### GUI doesn't start

1. **Run setup.bat again** to reinstall dependencies
2. **Check Python installation**: `python --version`
3. **Run from command line** to see errors:
   ```bash
   python -m src.gui_app
   ```

### GUI window is blank or frozen

1. **Wait** - initialization can take a moment
2. **Check antivirus** - may be blocking the app
3. **Restart** the application

### Audio level meter not moving

1. **Check Windows microphone settings**
2. **Select correct microphone** as default device
3. **Test microphone** in Windows Sound settings

### Settings not saving

1. **Check write permissions** for project folder
2. **Run as Administrator** if needed
3. **Manually edit** `.env` file

### Processing seems stuck

1. **Check Activity Log tab** for status
2. **Check internet connection**
3. **Wait longer** - large meetings take time
4. **Check OpenAI API status**: https://status.openai.com/

---

## 📟 Alternative: Command Line Interface

For advanced users, automation, and scripting.

### CLI Launch Methods

```bash
# Using batch files
Double-click: run.bat         # Full mode
Double-click: run_simple.bat  # Simple mode (mic only)

# Using command line
venv\Scripts\activate.bat
python -m src.main            # Full mode
python -m src.main --simple   # Simple mode
python -m src.main --list-devices  # List audio devices
```

### CLI Workflow

1. **Start**: Run the command
2. **Record**: Application runs in terminal
3. **Stop**: Type `stop` and press Enter (or Ctrl+C)
4. **Wait**: Processing happens automatically
5. **Find files**: Check `outputs/` folder

### When to Use CLI

| Scenario | Recommendation |
|----------|----------------|
| Daily meetings | GUI |
| Automation scripts | CLI |
| Batch processing | CLI |
| Headless servers | CLI |
| Debugging audio | CLI (--list-devices) |

---

## Finding Your Files

All output files are saved to:
```
outputs/meeting_YYYYMMDD_HHMMSS/
```

Example: `outputs/meeting_20260311_143022/`

### File Types

| File | Description |
|------|-------------|
| `audio_*.wav` | Original audio recording |
| `transcript_*.txt` | Basic transcript with timestamps |
| `transcript_diarized_*.md` | Speaker-labeled transcript |
| `summary_*.md` | AI-generated summary |
| `metadata_*.json` | Recording metadata |
| `transcription_raw.json` | Raw API response |
| `diarization_raw.json` | Raw diarization data |

---

## Cost Estimate

| Meeting Length | Estimated Cost |
|----------------|----------------|
| 15 minutes | ~$0.10 |
| 30 minutes | ~$0.20 |
| 60 minutes | ~$0.40 |
| 90 minutes | ~$0.60 |

---

## Need More Help?

- **Full documentation**: See `README.md`
- **Configuration details**: Check `.env` file options
- **Troubleshooting**: See README.md troubleshooting section

---

**Remember**: For the best experience, use the GUI by running `run_gui.bat`

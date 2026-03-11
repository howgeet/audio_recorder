# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Setup (2 minutes)

1. **Run setup**:
   ```
   Double-click: setup.bat
   ```
   Wait for installation to complete.

2. **Get OpenAI API Key**:
   - Visit: https://platform.openai.com/api-keys
   - Click "Create new secret key"
   - Copy the key (you'll enter it in the GUI)

### Step 2: Launch the GUI (Recommended)

```
Double-click: run_gui.bat
```

That's it! The graphical interface will open.

### Step 3: Configure API Key (Optional)

1. Click the **⚙️ Settings** button in the GUI
2. Enter your **OpenAI API Key**
3. Optionally select a **Local Whisper Model** for offline fallback
4. Click **Save**

> 💡 **No API key?** The app will use the local `faster-whisper` model for transcription (slower, no summary). Choose model size in Settings.

### Step 4: Your First Recording

1. **Click "🟢 Start Recording"**
   - Status changes to "Recording"
   - Timer starts counting

2. **Speak for 30 seconds**
   - Test your microphone
   - Say: "This is a test meeting to verify the transcription system is working properly."

3. **Click "🔴 Stop Recording"**
   - Processing begins automatically
   - Watch the progress bar

4. **Review Results**
   - **Transcript tab**: See what you said
   - **Summary tab**: AI-generated summary
   - **Notes tab**: Speaker-labeled transcript

5. **Save Your Files** (optional)
   - Click save buttons in each tab
   - Files saved to `outputs/meeting_YYYYMMDD_HHMMSS/`

### ✅ Success!

You're ready to record real meetings!

---

## 📱 Recording a Real Meeting

### With the GUI (Easiest)

1. **Before the meeting**:
   - Double-click `run_gui.bat`
   - Verify status shows "Idle"

2. **Start recording**:
   - Click "Start Recording"
   - Join your Teams/Zoom/Google Meet call

3. **During the meeting**:
   - Watch the timer and audio level meter
   - The GUI runs in the background

4. **After the meeting**:
   - Leave the call
   - Click "Stop Recording" in the GUI
   - Wait for processing (watch progress bar)

5. **Review**:
   - Browse Transcript, Summary, Notes tabs
   - Save files as needed

### Works with:
- Microsoft Teams
- Zoom
- Google Meet
- Webex
- In-person meetings
- Phone calls (on speaker)

---

## 💡 GUI Tips

| Tip | Description |
|-----|-------------|
| 📊 Audio Level | Watch the meter to ensure your mic is working |
| ⏱️ Timer | Keep track of recording duration |
| 📋 Activity Log | See real-time processing updates |
| 💾 Save Buttons | Export results to files anytime |

---

## ⚡ Alternative: Command Line Interface

For advanced users who prefer CLI:

```bash
# Simple mode (microphone only) - easiest CLI option
Double-click: run_simple.bat

# Full mode (microphone + system audio)
Double-click: run.bat

# Type 'stop' + Enter to end recording
```

### When to use CLI:
- Automation and scripting
- Batch processing
- Server environments
- Troubleshooting audio devices

---

## 🆘 Quick Troubleshooting

| Problem | Solution |
|---------|----------|
| GUI doesn't open | Run `setup.bat` again; ensure `PySide6` is installed |
| "API key not configured" | Click Settings ⚙️ and enter your key (or use local Whisper) |
| "No audio recorded" | Check microphone permissions in Windows |
| Audio level meter not moving | Select correct microphone in Windows settings |
| Processing is slow | Normal - wait patiently (2-5 min for 30-min meeting) |
| "Module not found" error | Run `pip install -r requirements.txt` |

---

## 💰 Cost

| Meeting Length | Cost |
|----------------|------|
| 30 minutes | ~$0.20 |
| 60 minutes | ~$0.40 |

Very affordable for professional use!

---

## 📚 Next Steps

- Read `USAGE.md` for detailed GUI instructions
- Read `README.md` for complete documentation
- Explore Settings ⚙️ for model and output configuration

---

**Happy transcribing! 🎉**

> **Remember**: For the best experience, use the GUI with `run_gui.bat`
>
> **No API key needed**: The app works offline using the local `faster-whisper` model — just select your preferred model size in ⚙️ Settings.

"""Modern GUI Application for Meeting Transcriber using PySide6."""

import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional
import queue
import sys
import os
import shutil

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QTabWidget, QProgressBar,
    QDialog, QLineEdit, QComboBox, QFileDialog, QMessageBox,
    QFrame, QSizePolicy, QStatusBar
)
from PySide6.QtCore import Qt, QTimer, Signal, QObject, QThread
from PySide6.QtGui import QFont, QColor, QPalette, QTextCursor

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.config import config, Config
from src.audio_capture import AudioCapture, SimpleAudioCapture
from src.transcription import Transcriber
from src.diarization import SpeakerDiarizer
from src.summarization import MeetingSummarizer
from src.file_manager import FileManager
from src.ffmpeg_utils import (
    check_ffmpeg_installed,
    get_ffmpeg_error_message,
    extract_audio_from_video,
    convert_audio_format,
    FFmpegError
)

# Supported file formats
SUPPORTED_AUDIO_FORMATS = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.webm', '.aac', '.wma'}
SUPPORTED_VIDEO_FORMATS = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'}
SUPPORTED_FORMATS = SUPPORTED_AUDIO_FORMATS | SUPPORTED_VIDEO_FORMATS

DARK_BG       = "#111827"
CARD_BG       = "#1f2937"
BORDER_COLOR  = "#374151"
TEXT_PRIMARY  = "#f9fafb"
TEXT_MUTED    = "#9ca3af"
GREEN         = "#22c55e"
GREEN_HOVER   = "#16a34a"
RED           = "#ef4444"
RED_HOVER     = "#dc2626"
BLUE          = "#3b82f6"
BLUE_HOVER    = "#2563eb"
GRAY          = "#6b7280"
AMBER         = "#f59e0b"

STYLESHEET = f"""
QMainWindow, QWidget {{ background-color: {DARK_BG}; color: {TEXT_PRIMARY}; }}
QDialog {{ background-color: {DARK_BG}; color: {TEXT_PRIMARY}; }}

QPushButton {{
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: bold;
    color: {TEXT_PRIMARY};
    background-color: {BORDER_COLOR};
    border: none;
}}
QPushButton:hover {{ background-color: #4b5563; }}
QPushButton:disabled {{ background-color: #1f2937; color: #4b5563; }}

QPushButton#btn_start  {{ background-color: {GREEN};  }}
QPushButton#btn_start:hover  {{ background-color: {GREEN_HOVER}; }}
QPushButton#btn_stop   {{ background-color: {RED};    }}
QPushButton#btn_stop:hover   {{ background-color: {RED_HOVER};   }}
QPushButton#btn_file   {{ background-color: {BLUE};   }}
QPushButton#btn_file:hover   {{ background-color: {BLUE_HOVER};  }}
QPushButton#btn_save   {{ background-color: {GRAY};   }}
QPushButton#btn_ok     {{ background-color: {GREEN};  }}
QPushButton#btn_ok:hover     {{ background-color: {GREEN_HOVER}; }}

QTextEdit {{
    background-color: {CARD_BG};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 8px;
    font-family: "Segoe UI";
    font-size: 13px;
}}

QTabWidget::pane {{
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    background-color: {CARD_BG};
}}
QTabBar::tab {{
    background-color: {DARK_BG};
    color: {TEXT_MUTED};
    padding: 8px 18px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    margin-right: 2px;
}}
QTabBar::tab:selected {{
    background-color: {CARD_BG};
    color: {TEXT_PRIMARY};
    font-weight: bold;
}}

QLineEdit, QComboBox {{
    background-color: {CARD_BG};
    color: {TEXT_PRIMARY};
    border: 1px solid {BORDER_COLOR};
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 13px;
}}
QComboBox QAbstractItemView {{
    background-color: {CARD_BG};
    color: {TEXT_PRIMARY};
    selection-background-color: {BORDER_COLOR};
}}

QProgressBar {{
    background-color: {CARD_BG};
    border: 1px solid {BORDER_COLOR};
    border-radius: 4px;
    height: 10px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{
    background-color: {BLUE};
    border-radius: 4px;
}}

QStatusBar {{ background-color: {CARD_BG}; color: {TEXT_MUTED}; font-size: 12px; }}
QLabel {{ color: {TEXT_PRIMARY}; }}
QFrame#separator {{ background-color: {BORDER_COLOR}; }}
"""


class StatusIndicator(QWidget):
    """Custom status indicator widget."""

    STATUS_COLORS = {
        "idle":       "#6b7280",
        "recording":  "#ef4444",
        "processing": "#f59e0b",
        "complete":   "#22c55e",
        "error":      "#dc2626",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._dot = QLabel()
        self._dot.setFixedSize(14, 14)
        self._dot.setStyleSheet(f"background:{self.STATUS_COLORS['idle']}; border-radius:7px;")
        layout.addWidget(self._dot)

        self._label = QLabel("Idle")
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        self._label.setFont(font)
        layout.addWidget(self._label)

        self._blink_timer = QTimer(self)
        self._blink_timer.timeout.connect(self._blink)
        self._blink_state = True
        self._current_status = "idle"

    def set_status(self, status: str, text: str = None):
        self._current_status = status
        color = self.STATUS_COLORS.get(status, self.STATUS_COLORS["idle"])
        self._dot.setStyleSheet(f"background:{color}; border-radius:7px;")
        self._label.setText(text or status.title())
        self._blink_timer.stop()
        if status == "recording":
            self._blink_timer.start(500)

    def _blink(self):
        color = self.STATUS_COLORS["recording"] if self._blink_state else "#7f1d1d"
        self._dot.setStyleSheet(f"background:{color}; border-radius:7px;")
        self._blink_state = not self._blink_state


class ModeIndicator(QLabel):
    """Widget to show current mode."""

    def __init__(self, parent=None):
        super().__init__("🎤 Live Recording Mode", parent)
        font = QFont()
        font.setBold(True)
        font.setPointSize(10)
        self.setFont(font)
        self.setStyleSheet(f"color: {GREEN}; background: {CARD_BG}; border-radius:6px; padding: 4px 10px;")
        self._current_mode = "live"

    def set_mode(self, mode: str, file_name: str = None):
        self._current_mode = mode
        if mode == "live":
            self.setText("🎤 Live Recording Mode")
            self.setStyleSheet(f"color: {GREEN}; background: {CARD_BG}; border-radius:6px; padding: 4px 10px;")
        elif mode == "file":
            display = (file_name[:30] + "...") if file_name and len(file_name) > 30 else file_name
            self.setText(f"📁 File Processing: {display}" if file_name else "📁 File Processing Mode")
            self.setStyleSheet(f"color: {BLUE}; background: {CARD_BG}; border-radius:6px; padding: 4px 10px;")

    def get_mode(self):
        return self._current_mode


class SettingsDialog(QDialog):
    """Settings dialog for configuring API keys and output directory."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setFixedSize(520, 420)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(24, 20, 24, 20)

        title = QLabel("⚙️ Settings")
        f = QFont(); f.setBold(True); f.setPointSize(16)
        title.setFont(f)
        layout.addWidget(title)

        # API Key
        layout.addWidget(QLabel("OpenAI API Key:"))
        key_row = QHBoxLayout()
        self.api_key_entry = QLineEdit()
        self.api_key_entry.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_entry.setPlaceholderText("sk-...")
        if config.openai_api_key:
            self.api_key_entry.setText(config.openai_api_key)
        key_row.addWidget(self.api_key_entry)
        self.toggle_btn = QPushButton("👁 Show")
        self.toggle_btn.setFixedWidth(80)
        self.toggle_btn.clicked.connect(self._toggle_show_key)
        key_row.addWidget(self.toggle_btn)
        layout.addLayout(key_row)

        # Output directory
        layout.addSpacing(8)
        layout.addWidget(QLabel("Output Directory:"))
        out_row = QHBoxLayout()
        self.output_entry = QLineEdit(str(config.output_dir))
        out_row.addWidget(self.output_entry)
        browse_btn = QPushButton("📁 Browse")
        browse_btn.setFixedWidth(90)
        browse_btn.clicked.connect(self._browse_output)
        out_row.addWidget(browse_btn)
        layout.addLayout(out_row)

        # LLM Model
        layout.addSpacing(8)
        layout.addWidget(QLabel("LLM Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"])
        self.model_combo.setCurrentText(config.llm_model)
        layout.addWidget(self.model_combo)

        # Local Whisper Model
        layout.addSpacing(8)
        layout.addWidget(QLabel("Local Whisper Model (offline fallback):"))
        self.whisper_combo = QComboBox()
        self.whisper_combo.addItems(["tiny", "base", "small", "medium", "large-v2", "large-v3"])
        self.whisper_combo.setCurrentText(config.local_whisper_model)
        layout.addWidget(self.whisper_combo)

        layout.addStretch()

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedWidth(100)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        save_btn = QPushButton("💾 Save")
        save_btn.setObjectName("btn_ok")
        save_btn.setFixedWidth(100)
        save_btn.clicked.connect(self._save_settings)
        btn_row.addWidget(save_btn)
        layout.addLayout(btn_row)

    def _toggle_show_key(self):
        if self.api_key_entry.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_entry.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_btn.setText("👁 Hide")
        else:
            self.api_key_entry.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_btn.setText("👁 Show")

    def _browse_output(self):
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory", str(config.output_dir))
        if directory:
            self.output_entry.setText(directory)

    def _save_settings(self):
        api_key = self.api_key_entry.text().strip()
        output_dir = self.output_entry.text().strip()

        config.openai_api_key = api_key if api_key else None
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key
        elif "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]

        if output_dir:
            config.output_dir = Path(output_dir)
            config.output_dir.mkdir(parents=True, exist_ok=True)

        config.llm_model = self.model_combo.currentText()
        config.local_whisper_model = self.whisper_combo.currentText()

        QMessageBox.information(self, "Settings", "Settings saved successfully!")
        self.accept()


class MeetingTranscriberGUI(QMainWindow):
    """Main GUI application for Meeting Transcriber."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Meeting Transcriber Pro")
        self.resize(1200, 800)
        self.setMinimumSize(900, 600)

        self.is_recording = False
        self.is_processing = False
        self.recording_start_time = None
        self.audio_capture = None
        self.file_manager = None
        self.message_queue = queue.Queue()
        self.selected_file_path = None

        self.transcript_text = ""
        self.summary_text = ""
        self.diarized_text = ""

        self._build_ui()

        self._queue_timer = QTimer(self)
        self._queue_timer.timeout.connect(self._process_message_queue)
        self._queue_timer.start(100)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_timer)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 10, 20, 4)
        root.setSpacing(6)

        root.addLayout(self._build_header())
        root.addWidget(self._build_tabs(), stretch=1)

        self._build_status_bar()

    def _build_header(self) -> QVBoxLayout:
        vbox = QVBoxLayout()
        vbox.setSpacing(10)

        # Title row
        title_row = QHBoxLayout()
        title_lbl = QLabel("🎙️ Meeting Transcriber Pro")
        f = QFont(); f.setBold(True); f.setPointSize(18)
        title_lbl.setFont(f)
        title_row.addWidget(title_lbl)
        title_row.addStretch()
        settings_btn = QPushButton("⚙️")
        settings_btn.setFixedSize(40, 40)
        settings_btn.clicked.connect(self._open_settings)
        title_row.addWidget(settings_btn)
        vbox.addLayout(title_row)

        # Controls row
        ctrl_row = QHBoxLayout()
        ctrl_row.setSpacing(8)

        self.start_btn = QPushButton("🎤 START RECORDING")
        self.start_btn.setObjectName("btn_start")
        self.start_btn.setMinimumHeight(46)
        self.start_btn.setMinimumWidth(180)
        f2 = QFont(); f2.setBold(True); f2.setPointSize(11)
        self.start_btn.setFont(f2)
        self.start_btn.clicked.connect(self._start_recording)
        ctrl_row.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹️ STOP RECORDING")
        self.stop_btn.setObjectName("btn_stop")
        self.stop_btn.setMinimumHeight(46)
        self.stop_btn.setMinimumWidth(180)
        self.stop_btn.setFont(f2)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_recording)
        ctrl_row.addWidget(self.stop_btn)

        sep = QFrame()
        sep.setObjectName("separator")
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setFixedWidth(2)
        ctrl_row.addWidget(sep)

        self.process_file_btn = QPushButton("📁 PROCESS AUDIO")
        self.process_file_btn.setObjectName("btn_file")
        self.process_file_btn.setMinimumHeight(46)
        self.process_file_btn.setMinimumWidth(180)
        self.process_file_btn.setFont(f2)
        self.process_file_btn.clicked.connect(self._select_and_process_file)
        ctrl_row.addWidget(self.process_file_btn)

        ctrl_row.addSpacing(10)
        self.status_indicator = StatusIndicator()
        ctrl_row.addWidget(self.status_indicator)

        ctrl_row.addSpacing(10)
        timer_frame = QFrame()
        timer_frame.setStyleSheet(f"background:{CARD_BG}; border-radius:8px;")
        tf_layout = QHBoxLayout(timer_frame)
        tf_layout.setContentsMargins(12, 6, 12, 6)
        tf_layout.addWidget(QLabel("⏱️"))
        self.timer_label = QLabel("00:00:00")
        tf = QFont("Consolas"); tf.setBold(True); tf.setPointSize(14)
        self.timer_label.setFont(tf)
        tf_layout.addWidget(self.timer_label)
        ctrl_row.addWidget(timer_frame)

        self.level_bar = QProgressBar()
        self.level_bar.setFixedSize(100, 18)
        self.level_bar.setRange(0, 100)
        self.level_bar.setValue(0)
        self.level_bar.setTextVisible(False)
        ctrl_row.addWidget(self.level_bar)

        ctrl_row.addStretch()
        vbox.addLayout(ctrl_row)

        # Mode row
        mode_row = QHBoxLayout()
        self.mode_indicator = ModeIndicator()
        mode_row.addWidget(self.mode_indicator)
        self.file_info_label = QLabel("")
        self.file_info_label.setStyleSheet(f"color:{TEXT_MUTED}; font-size:11px;")
        mode_row.addWidget(self.file_info_label)
        mode_row.addStretch()
        vbox.addLayout(mode_row)

        return vbox

    def _build_tabs(self) -> QTabWidget:
        self.tabs = QTabWidget()

        self.transcript_edit = self._make_text_edit(
            "Transcript will appear here after recording and processing...")
        self.summary_edit = self._make_text_edit(
            "Summary will appear here after processing...")
        self.notes_edit = self._make_text_edit(
            "Speaker-labeled notes will appear here after processing...")
        self.log_edit = QTextEdit()
        self.log_edit.setReadOnly(True)
        self.log_edit.setFont(QFont("Consolas", 10))

        self.tabs.addTab(self._tab_with_save(self.transcript_edit, "Full Meeting Transcript", "transcript"),
                         "📝 Transcript")
        self.tabs.addTab(self._tab_with_save(self.summary_edit, "Meeting Summary & Key Points", "summary"),
                         "📋 Summary")
        self.tabs.addTab(self._tab_with_save(self.notes_edit, "Speaker-labeled Transcript", "notes"),
                         "📌 Meeting Notes")
        self.tabs.addTab(self._tab_with_clear(self.log_edit, "Activity Log"),
                         "📊 Activity Log")

        self._log_message("Application started. Ready to record.")
        return self.tabs

    def _make_text_edit(self, placeholder: str) -> QTextEdit:
        w = QTextEdit()
        w.setReadOnly(True)
        w.setPlainText(placeholder)
        w.setFont(QFont("Segoe UI", 11))
        return w

    def _tab_with_save(self, edit: QTextEdit, title_text: str, content_type: str) -> QWidget:
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(8, 8, 8, 8)
        hdr = QHBoxLayout()
        lbl = QLabel(title_text)
        f = QFont(); f.setBold(True); f.setPointSize(13)
        lbl.setFont(f)
        hdr.addWidget(lbl)
        hdr.addStretch()
        save_btn = QPushButton("💾 Save")
        save_btn.setObjectName("btn_save")
        save_btn.setFixedWidth(80)
        save_btn.clicked.connect(lambda: self._save_content(content_type))
        hdr.addWidget(save_btn)
        vbox.addLayout(hdr)
        vbox.addWidget(edit, stretch=1)
        return w

    def _tab_with_clear(self, edit: QTextEdit, title_text: str) -> QWidget:
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(8, 8, 8, 8)
        hdr = QHBoxLayout()
        lbl = QLabel(title_text)
        f = QFont(); f.setBold(True); f.setPointSize(13)
        lbl.setFont(f)
        hdr.addWidget(lbl)
        hdr.addStretch()
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.setObjectName("btn_save")
        clear_btn.setFixedWidth(80)
        clear_btn.clicked.connect(self._clear_log)
        hdr.addWidget(clear_btn)
        vbox.addLayout(hdr)
        vbox.addWidget(edit, stretch=1)
        return w

    def _build_status_bar(self):
        bar = QStatusBar()
        self.setStatusBar(bar)

        self.output_status_label = QLabel(f"📁 Output: {config.output_dir}")
        bar.addWidget(self.output_status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(300)
        self.progress_bar.setMaximum(1000)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        bar.addPermanentWidget(self.progress_bar)

        api_status = "✅ API Connected" if config.openai_api_key else "❌ API Key Missing"
        self.api_label = QLabel(api_status)
        bar.addPermanentWidget(self.api_label)

    def _open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()
        api_status = "✅ API Connected" if config.openai_api_key else "❌ API Key Missing"
        self.api_label.setText(api_status)

    def _log_message(self, message: str, level: str = "info"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        icons = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌", "progress": "🔄"}
        icon = icons.get(level, "ℹ️")
        self.log_edit.append(f"[{timestamp}] {icon} {message}")
        self.log_edit.moveCursor(QTextCursor.MoveOperation.End)

    def _clear_log(self):
        self.log_edit.clear()
        self._log_message("Log cleared.")

    def _update_timer(self):
        if self.is_recording and self.recording_start_time:
            elapsed = time.time() - self.recording_start_time
            h = int(elapsed // 3600)
            m = int((elapsed % 3600) // 60)
            s = int(elapsed % 60)
            self.timer_label.setText(f"{h:02d}:{m:02d}:{s:02d}")
            import random
            self.level_bar.setValue(random.randint(20, 90))

    def _ask_proceed_without_key(self) -> bool:
        reply = QMessageBox.question(
            self, "No API Key",
            "OpenAI API key is not set.\n\n"
            "Transcription will use the local Whisper model (slower, no summary).\n\n"
            "Continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes

    def _start_recording(self):
        if not config.openai_api_key:
            if not self._ask_proceed_without_key():
                return

        self.is_recording = True
        self.recording_start_time = time.time()
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.process_file_btn.setEnabled(False)
        self.status_indicator.set_status("recording", "Recording...")
        self.mode_indicator.set_mode("live")
        self.file_info_label.setText("")

        self._set_text(self.transcript_edit, "Recording in progress...")
        self._set_text(self.summary_edit, "Recording in progress...")
        self._set_text(self.notes_edit, "Recording in progress...")

        self._timer.start(1000)
        self._log_message("Starting recording...", "progress")
        threading.Thread(target=self._recording_thread, daemon=True).start()

    def _select_and_process_file(self):
        if not config.openai_api_key:
            if not self._ask_proceed_without_key():
                return

        audio_ext = " ".join(f"*{e}" for e in sorted(SUPPORTED_AUDIO_FORMATS))
        video_ext = " ".join(f"*{e}" for e in sorted(SUPPORTED_VIDEO_FORMATS))
        all_ext   = " ".join(f"*{e}" for e in sorted(SUPPORTED_FORMATS))
        filter_str = (
            f"All Supported Files ({all_ext});;"
            f"Audio Files ({audio_ext});;"
            f"Video Files ({video_ext});;"
            f"All Files (*.*)"
        )

        filepath, _ = QFileDialog.getOpenFileName(
            self, "Select Audio or Video File", str(Path.home()), filter_str
        )
        if not filepath:
            return

        file_path = Path(filepath)
        if not file_path.exists():
            QMessageBox.critical(self, "Error", "Selected file does not exist.")
            return

        file_ext = file_path.suffix.lower()
        if file_ext not in SUPPORTED_FORMATS:
            QMessageBox.critical(self, "Unsupported Format",
                f"File format '{file_ext}' is not supported.\n\n"
                f"Supported audio: {', '.join(sorted(SUPPORTED_AUDIO_FORMATS))}\n\n"
                f"Supported video: {', '.join(sorted(SUPPORTED_VIDEO_FORMATS))}")
            return

        file_size_mb = file_path.stat().st_size / (1024 * 1024)
        self.selected_file_path = file_path
        self.mode_indicator.set_mode("file", file_path.name)
        self.file_info_label.setText(f"Size: {file_size_mb:.1f} MB | Format: {file_ext}")

        is_video = file_ext in SUPPORTED_VIDEO_FORMATS
        extra = "Audio will be extracted from the video first." if is_video else ""
        reply = QMessageBox.question(
            self, "Confirm Processing",
            f"Process this {'video' if is_video else 'audio'} file?\n\n"
            f"📁 {file_path.name}\n"
            f"📊 Size: {file_size_mb:.1f} MB\n"
            f"🎬 Type: {file_ext}\n\n{extra}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            self._reset_mode()
            return

        self._start_file_processing()

    def _reset_mode(self):
        self.selected_file_path = None
        self.mode_indicator.set_mode("live")
        self.file_info_label.setText("")

    def _start_file_processing(self):
        self.is_processing = True
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.process_file_btn.setEnabled(False)
        self.status_indicator.set_status("processing", "Processing File...")
        self._set_text(self.transcript_edit, "Processing file...")
        self._set_text(self.summary_edit, "Processing file...")
        self._set_text(self.notes_edit, "Processing file...")
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self._log_message(f"Starting to process file: {self.selected_file_path.name}", "progress")
        threading.Thread(target=self._file_processing_thread, daemon=True).start()

    def _extract_audio_from_video(self, video_path: Path, output_path: Path) -> bool:
        try:
            self.message_queue.put(("log", (f"Extracting audio from video: {video_path.name}", "progress")))
            if not check_ffmpeg_installed():
                self.message_queue.put(("log", (get_ffmpeg_error_message(), "error")))
                return False
            self.message_queue.put(("log", ("Converting to WAV format...", "progress")))
            extract_audio_from_video(video_path, output_path, output_format='wav')
            self.message_queue.put(("log", ("Audio extraction complete!", "success")))
            return True
        except FFmpegError as e:
            self.message_queue.put(("log", (f"FFmpeg error: {e}", "error")))
            return False
        except Exception as e:
            self.message_queue.put(("log", (f"Error extracting audio: {e}", "error")))
            return False

    def _file_processing_thread(self):
        try:
            self.file_manager = FileManager()
            file_ext = self.selected_file_path.suffix.lower()
            is_video = file_ext in SUPPORTED_VIDEO_FORMATS
            self.message_queue.put(("progress", 50))

            if is_video:
                self.message_queue.put(("log", ("Preparing to extract audio from video...", "progress")))
                audio_file = self.file_manager.meeting_dir / "extracted_audio.wav"
                if not self._extract_audio_from_video(self.selected_file_path, audio_file):
                    raise Exception("Failed to extract audio from video file.")
                self.message_queue.put(("progress", 150))
            else:
                if file_ext == '.wav':
                    audio_file = self.file_manager.meeting_dir / self.selected_file_path.name
                    shutil.copy2(self.selected_file_path, audio_file)
                    self.message_queue.put(("log", ("Copied audio file to outputs", "info")))
                else:
                    self.message_queue.put(("log", (f"Converting {file_ext} to WAV format...", "progress")))
                    try:
                        if not check_ffmpeg_installed():
                            raise FFmpegError(get_ffmpeg_error_message())
                        audio_file = self.file_manager.meeting_dir / "converted_audio.wav"
                        convert_audio_format(self.selected_file_path, audio_file, output_format='wav')
                        self.message_queue.put(("log", ("Audio conversion complete!", "success")))
                    except FFmpegError as e:
                        self.message_queue.put(("log", (f"FFmpeg error: {e}", "error")))
                        raise
                    except Exception as e:
                        self.message_queue.put(("log", (f"Conversion failed, using original: {e}", "warning")))
                        audio_file = self.selected_file_path
                self.message_queue.put(("progress", 150))

            if not audio_file.exists() or audio_file.stat().st_size == 0:
                raise Exception("Audio file is empty or does not exist.")

            self.message_queue.put(("log", (f"Audio file ready: {audio_file.name}", "success")))
            self.message_queue.put(("progress", 200))
            self.message_queue.put(("log", ("Starting transcription...", "progress")))

            def transcription_progress(msg: str):
                clean = msg.strip()
                if clean and not clean.startswith("\n"):
                    self.message_queue.put(("log", (clean, "progress")))

            transcriber = Transcriber()
            transcription_result = transcriber.transcribe_with_retry(audio_file, progress_callback=transcription_progress)
            transcript_text = transcriber.format_transcript(transcription_result)
            self.file_manager.save_transcript(transcript_text)
            self.message_queue.put(("transcript", transcript_text))
            self.message_queue.put(("log", ("Transcription completed!", "success")))
            self.message_queue.put(("progress", 500))

            self.message_queue.put(("log", ("Performing speaker diarization...", "progress")))
            diarizer = SpeakerDiarizer()
            diarization_result = diarizer.perform_diarization(audio_file, transcription_result)
            diarized_text = diarizer.format_diarized_transcript(diarization_result, transcription_result)
            self.file_manager.save_diarized_transcript(diarized_text)
            self.message_queue.put(("notes", diarized_text))
            self.message_queue.put(("log", ("Speaker diarization completed!", "success")))
            self.message_queue.put(("progress", 750))

            self.message_queue.put(("log", ("Generating summary...", "progress")))
            try:
                summarizer = MeetingSummarizer()
                summary_result = summarizer.generate_summary(
                    transcription_result['text'], transcription_result.get('language', 'en'))
                summary_text = summarizer.format_summary(summary_result)
                self.file_manager.save_summary(summary_text)
                self.message_queue.put(("summary", summary_text))
                self.message_queue.put(("log", ("Summary generated!", "success")))
            except Exception as summ_err:
                self.message_queue.put(("log", (f"Summarization skipped (OpenAI unavailable): {summ_err}", "warning")))
            self.message_queue.put(("progress", 1000))
            self.message_queue.put(("log", (f"All files saved to: {self.file_manager.meeting_dir}", "success")))
            self.message_queue.put(("file_complete", str(self.file_manager.meeting_dir)))

        except Exception as e:
            import traceback; traceback.print_exc()
            self.message_queue.put(("log", (f"Processing error: {e}", "error")))
            self.message_queue.put(("error", str(e)))

    def _recording_thread(self):
        try:
            self.file_manager = FileManager()
            audio_file = self.file_manager.get_audio_file_path()
            try:
                self.message_queue.put(("log", ("Using full mode (mic + system audio)...", "info")))
                self.audio_capture = AudioCapture(audio_file)
            except Exception as e:
                self.message_queue.put(("log", (f"Falling back to simple mode: {e}", "warning")))
                self.audio_capture = SimpleAudioCapture(audio_file)
            self.audio_capture.start_recording()
            self.message_queue.put(("log", ("Recording started successfully!", "success")))
        except Exception as e:
            self.message_queue.put(("log", (f"Error starting recording: {e}", "error")))
            self.message_queue.put(("error", str(e)))

    def _stop_recording(self):
        if not self.is_recording:
            return
        self.is_recording = False
        self._timer.stop()
        self.level_bar.setValue(0)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        self.process_file_btn.setEnabled(False)
        self.status_indicator.set_status("processing", "Processing...")
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        self._log_message("Stopping recording and starting processing...", "progress")
        threading.Thread(target=self._processing_thread, daemon=True).start()

    def _processing_thread(self):
        try:
            self.message_queue.put(("progress", 100))
            audio_file = self.audio_capture.stop_recording()
            self.message_queue.put(("log", (f"Audio saved: {audio_file.name}", "success")))
            if not audio_file.exists() or audio_file.stat().st_size == 0:
                raise Exception("No audio was recorded.")

            self.message_queue.put(("progress", 200))
            self.message_queue.put(("log", ("Starting transcription...", "progress")))

            def transcription_progress(msg: str):
                clean = msg.strip()
                if clean and not clean.startswith("\n"):
                    self.message_queue.put(("log", (clean, "progress")))

            transcriber = Transcriber()
            transcription_result = transcriber.transcribe_with_retry(audio_file, progress_callback=transcription_progress)
            transcript_text = transcriber.format_transcript(transcription_result)
            self.file_manager.save_transcript(transcript_text)
            self.message_queue.put(("transcript", transcript_text))
            self.message_queue.put(("log", ("Transcription completed!", "success")))
            self.message_queue.put(("progress", 500))

            self.message_queue.put(("log", ("Performing speaker diarization...", "progress")))
            diarizer = SpeakerDiarizer()
            diarization_result = diarizer.perform_diarization(audio_file, transcription_result)
            diarized_text = diarizer.format_diarized_transcript(diarization_result, transcription_result)
            self.file_manager.save_diarized_transcript(diarized_text)
            self.message_queue.put(("notes", diarized_text))
            self.message_queue.put(("log", ("Speaker diarization completed!", "success")))
            self.message_queue.put(("progress", 750))

            self.message_queue.put(("log", ("Generating summary...", "progress")))
            try:
                summarizer = MeetingSummarizer()
                summary_result = summarizer.generate_summary(
                    transcription_result['text'], transcription_result.get('language', 'en'))
                summary_text = summarizer.format_summary(summary_result)
                self.file_manager.save_summary(summary_text)
                self.message_queue.put(("summary", summary_text))
                self.message_queue.put(("log", ("Summary generated!", "success")))
            except Exception as summ_err:
                self.message_queue.put(("log", (f"Summarization skipped (OpenAI unavailable): {summ_err}", "warning")))
            self.message_queue.put(("progress", 1000))
            self.message_queue.put(("log", (f"All files saved to: {self.file_manager.meeting_dir}", "success")))
            self.message_queue.put(("complete", str(self.file_manager.meeting_dir)))

        except Exception as e:
            import traceback; traceback.print_exc()
            self.message_queue.put(("log", (f"Processing error: {e}", "error")))
            self.message_queue.put(("error", str(e)))

    def _process_message_queue(self):
        try:
            while True:
                msg_type, data = self.message_queue.get_nowait()

                if msg_type == "log":
                    message, level = data
                    self._log_message(message, level)

                elif msg_type == "transcript":
                    self._set_text(self.transcript_edit, data)

                elif msg_type == "summary":
                    self._set_text(self.summary_edit, data)

                elif msg_type == "notes":
                    self._set_text(self.notes_edit, data)

                elif msg_type == "progress":
                    self.progress_bar.setValue(int(data))

                elif msg_type == "complete":
                    self._on_complete()
                    self.mode_indicator.set_mode("live")
                    QMessageBox.information(self, "Complete",
                        f"Meeting processing complete!\n\nFiles saved to:\n{data}")

                elif msg_type == "file_complete":
                    self.is_processing = False
                    self._on_complete()
                    src = self.selected_file_path.name if self.selected_file_path else "Unknown"
                    QMessageBox.information(self, "Complete",
                        f"File processing complete!\n\nSource: {src}\n\nFiles saved to:\n{data}")

                elif msg_type == "error":
                    self.is_processing = False
                    self.status_indicator.set_status("error", "Error")
                    self.progress_bar.hide()
                    self.start_btn.setEnabled(True)
                    self.stop_btn.setEnabled(False)
                    self.process_file_btn.setEnabled(True)
                    self._reset_mode()
                    QMessageBox.critical(self, "Error", f"An error occurred:\n{data}")

        except queue.Empty:
            pass

    def _on_complete(self):
        self.status_indicator.set_status("complete", "Complete")
        self.progress_bar.hide()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.process_file_btn.setEnabled(True)

    def _set_text(self, edit: QTextEdit, text: str):
        edit.setPlainText(text)

    def _save_content(self, content_type: str):
        mapping = {
            "transcript": (self.transcript_edit, "transcript.txt",
                           "Text files (*.txt);;All files (*.*)"),
            "summary":    (self.summary_edit,    "summary.md",
                           "Markdown files (*.md);;Text files (*.txt);;All files (*.*)"),
            "notes":      (self.notes_edit,      "meeting_notes.md",
                           "Markdown files (*.md);;Text files (*.txt);;All files (*.*)"),
        }
        if content_type not in mapping:
            return
        edit, default_name, filter_str = mapping[content_type]
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Save File",
            str(config.output_dir / default_name),
            filter_str
        )
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(edit.toPlainText())
            self._log_message(f"Saved: {filepath}", "success")
            QMessageBox.information(self, "Saved", f"File saved to:\n{filepath}")


def main():
    """Main entry point for the GUI application."""
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET)
    window = MeetingTranscriberGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

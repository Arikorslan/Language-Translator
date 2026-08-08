from __future__ import annotations

import atexit
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import googletrans
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTextEdit,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)
from pygame import mixer

from assets.xtract import ExtractImages
from backend.translate import TranslateText
from backend.voiceInput import RecogniseAudio
from backend.voiceOutput import TextToSpeech
from update import GitHubUpdater, ReleaseAsset, ReleaseInfo, UpdateError


APP_VERSION = "10.6.0"
APP_COPYRIGHT = "Copyright © Ariko 2026"
DEFAULT_GITHUB_REPO = os.getenv("LANG_TRANS_GITHUB_REPO", "owner/repo")


LIGHT_STYLE = """
QMainWindow, QWidget {
    background: #f4f7fb;
    color: #102033;
    font-family: Segoe UI;
    font-size: 12px;
}
QFrame#HeaderCard {
    background: #ffffff;
    border: 1px solid #d8e0ea;
    border-radius: 18px;
}
QGroupBox {
    background: #ffffff;
    border: 1px solid #d8e0ea;
    border-radius: 16px;
    margin-top: 16px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #17324d;
}
QTextEdit, QListWidget, QComboBox {
    background: #ffffff;
    border: 1px solid #cad6e2;
    border-radius: 12px;
    padding: 10px;
    selection-background-color: #2d6cdf;
    selection-color: white;
}
QTextEdit {
    min-height: 240px;
}
QPushButton {
    background: #17324d;
    color: white;
    border: none;
    border-radius: 12px;
    padding: 10px 14px;
    font-weight: 600;
}
QPushButton:hover {
    background: #244a6e;
}
QPushButton:pressed {
    background: #102233;
}
QPushButton#GhostButton {
    background: #edf2f7;
    color: #17324d;
    border: 1px solid #cad6e2;
}
QPushButton#GhostButton:hover {
    background: #e4ebf3;
}
QCheckBox {
    spacing: 8px;
    font-weight: 600;
}
QStatusBar {
    background: #ffffff;
    color: #4b5d73;
}
"""


DARK_STYLE = """
QMainWindow, QWidget {
    background: #101722;
    color: #edf3fb;
    font-family: Segoe UI;
    font-size: 12px;
}
QFrame#HeaderCard {
    background: #151f2d;
    border: 1px solid #253448;
    border-radius: 18px;
}
QGroupBox {
    background: #151f2d;
    border: 1px solid #253448;
    border-radius: 16px;
    margin-top: 16px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
    color: #edf3fb;
}
QTextEdit, QListWidget, QComboBox {
    background: #0d1420;
    color: #edf3fb;
    border: 1px solid #2b3b52;
    border-radius: 12px;
    padding: 10px;
    selection-background-color: #4d7dff;
    selection-color: white;
}
QTextEdit {
    min-height: 240px;
}
QPushButton {
    background: #4d7dff;
    color: white;
    border: none;
    border-radius: 12px;
    padding: 10px 14px;
    font-weight: 600;
}
QPushButton:hover {
    background: #6690ff;
}
QPushButton:pressed {
    background: #3966e0;
}
QPushButton#GhostButton {
    background: #1d2a3b;
    color: #edf3fb;
    border: 1px solid #32455d;
}
QPushButton#GhostButton:hover {
    background: #25354a;
}
QCheckBox {
    spacing: 8px;
    font-weight: 600;
}
QStatusBar {
    background: #151f2d;
    color: #c6d1de;
}
"""


@dataclass(frozen=True)
class LanguageOption:
    name: str
    code: str

    @property
    def display(self) -> str:
        return f"{self.name.title()} ({self.code})"


class VoiceInputWorker(QThread):
    recognized = pyqtSignal(str)
    failed = pyqtSignal(str)

    def run(self) -> None:
        try:
            voice = RecogniseAudio()
            result = voice.listenToAudio()
            if result:
                self.recognized.emit(result)
            else:
                self.failed.emit("No speech was recognized.")
        except Exception as exc:
            self.failed.emit(str(exc))


class UpdateCheckWorker(QThread):
    success = pyqtSignal(bool, object)
    failed = pyqtSignal(str)

    def __init__(self, repo: str, current_version: str) -> None:
        super().__init__()
        self.repo = repo
        self.current_version = current_version

    def run(self) -> None:
        try:
            updater = GitHubUpdater(self.repo)
            has_update, release = updater.check_for_update(self.current_version)
            self.success.emit(has_update, release)
        except Exception as exc:
            self.failed.emit(str(exc))


class AppLanguage(QMainWindow):
    def __init__(self, extractor: ExtractImages | None) -> None:
        super().__init__()

        self.extractor = extractor
        self.setWindowTitle("Ariko's Language App")
        self.resize(1380, 860)

        self.translator = TranslateText()
        self.tts = TextToSpeech()
        self.voice_worker: VoiceInputWorker | None = None
        self.update_worker: UpdateCheckWorker | None = None
        self.theme_mode = "dark"

        self.home = Path.home()
        self.settings_dir = self.home / ".lang-trans"
        self.settings_path = self.settings_dir / "settings.json"
        self.settings = self._load_settings()

        self.app_version = APP_VERSION
        self.github_repo = str(self.settings.get("github_repo") or DEFAULT_GITHUB_REPO)
        self.auto_check_updates_enabled = bool(self.settings.get("auto_check_updates", True))

        self.icon_path = self.home / "Pictures" / "languages.png"
        self.audio_root = self.home / "LANGUAGE_TRANSLATOR_AUDIOS"
        self.audio_root.mkdir(parents=True, exist_ok=True)

        self._build_language_options()
        self._build_ui()
        self.apply_theme(self.theme_mode)
        self.refresh_audio_list()
        self._set_status(f"Ready - v{self.app_version}")

        # Soft startup check; only prompts when a newer release is available.
        QTimer.singleShot(1200, self.auto_check_updates)

    def _build_language_options(self) -> None:
        self.language_options = [
            LanguageOption(name=name, code=code)
            for name, code in sorted(googletrans.LANGCODES.items(), key=lambda item: item[0].lower())
        ]
        self.code_to_name = {option.code: option.name for option in self.language_options}

    def _build_ui(self) -> None:
        central = QWidget(self)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(14)

        main_layout.addWidget(self._build_header())

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.addTab(self._build_translator_tab(), "Translator")
        self.tabs.addTab(self._build_audio_tab(), "Saved Audio Files")
        self.tabs.addTab(self._build_settings_tab(), "Settings")
        main_layout.addWidget(self.tabs, 1)

        self.setCentralWidget(central)
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.addPermanentWidget(QLabel(APP_COPYRIGHT))

        if self.icon_path.exists():
            self.setWindowIcon(QIcon(str(self.icon_path)))

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("HeaderCard")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(16)

        title_block = QVBoxLayout()
        title = QLabel("Ariko's Language App")
        title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        subtitle = QLabel("Translate text, speak output, manage saved audio, and get updates in-app.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #6e7f92;")

        self.mode_badge = QLabel("Dark mode")
        self.mode_badge.setStyleSheet(
            "padding: 6px 10px; border-radius: 10px; background: #17324d; color: white; font-weight: 600;"
        )

        self.version_badge = QLabel(f"Version {self.app_version}")
        self.version_badge.setStyleSheet(
            "padding: 6px 10px; border-radius: 10px; background: #4b5d73; color: white; font-weight: 600;"
        )

        title_block.addWidget(title)
        title_block.addWidget(subtitle)

        badges = QHBoxLayout()
        badges.addWidget(self.mode_badge)
        badges.addWidget(self.version_badge)
        badges.addStretch(1)
        title_block.addLayout(badges)

        logo = QLabel()
        logo.setFixedSize(64, 64)
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if self.icon_path.exists():
            pixmap = QPixmap(str(self.icon_path)).scaled(
                64,
                64,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            logo.setPixmap(pixmap)
        else:
            logo.setText("LT")
            logo.setStyleSheet(
                "border-radius: 32px; background: #4d7dff; color: white; font-size: 20px; font-weight: 700;"
            )

        self.theme_toggle = QCheckBox("Dark Mode")
        self.theme_toggle.setChecked(True)
        self.theme_toggle.toggled.connect(self.toggle_theme)

        self.check_updates_button = QPushButton("Check Updates")
        self.check_updates_button.setObjectName("GhostButton")
        self.check_updates_button.clicked.connect(self.check_updates_clicked)

        right_stack = QVBoxLayout()
        right_stack.addWidget(self.theme_toggle, 0, Qt.AlignmentFlag.AlignRight)
        right_stack.addWidget(self.check_updates_button, 0, Qt.AlignmentFlag.AlignRight)
        right_stack.addStretch(1)

        layout.addLayout(title_block, 1)
        layout.addWidget(logo)
        layout.addLayout(right_stack)
        return header

    def _build_translator_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)

        controls = QFrame()
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(10)

        self.auto_detect_checkbox = QCheckBox("Auto Detect")
        self.auto_detect_checkbox.setChecked(True)

        self.save_audio_checkbox = QCheckBox("Save Audio Output")
        self.save_audio_checkbox.setChecked(False)

        self.source_combo = QComboBox()
        self.target_combo = QComboBox()
        for option in self.language_options:
            self.source_combo.addItem(option.display, option.code)
            self.target_combo.addItem(option.display, option.code)

        self._set_combo_to_code(self.source_combo, "en")
        self._set_combo_to_code(self.target_combo, "ru")

        self.voice_button = QPushButton("Voice Input")
        self.voice_button.clicked.connect(self.start_voice_input)

        self.load_button = QPushButton("Load Text File")
        self.load_button.setObjectName("GhostButton")
        self.load_button.clicked.connect(self.load_text_file)

        self.translate_button = QPushButton("Translate Text")
        self.translate_button.clicked.connect(self.translate_text)

        controls_layout.addWidget(QLabel("Source"))
        controls_layout.addWidget(self.source_combo, 1)
        controls_layout.addWidget(QLabel("Target"))
        controls_layout.addWidget(self.target_combo, 1)
        controls_layout.addWidget(self.auto_detect_checkbox)
        controls_layout.addWidget(self.save_audio_checkbox)
        controls_layout.addWidget(self.voice_button)
        controls_layout.addWidget(self.load_button)
        controls_layout.addWidget(self.translate_button)

        layout.addWidget(controls)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        input_group = QGroupBox("Input")
        input_layout = QVBoxLayout(input_group)
        self.input_edit = QTextEdit()
        self.input_edit.setPlaceholderText("Enter or paste text to translate here...")
        self.input_edit.setFont(QFont("Segoe UI", 12))
        input_layout.addWidget(self.input_edit)

        input_actions = QHBoxLayout()
        self.clear_input_button = QPushButton("Clear Input")
        self.clear_input_button.setObjectName("GhostButton")
        self.clear_input_button.clicked.connect(self.clear_input)
        input_actions.addWidget(self.clear_input_button)
        input_actions.addStretch(1)
        input_layout.addLayout(input_actions)

        output_group = QGroupBox("Output")
        output_layout = QVBoxLayout(output_group)
        self.output_edit = QTextEdit()
        self.output_edit.setPlaceholderText("Translation output appears here...")
        self.output_edit.setFont(QFont("Segoe UI", 12))
        output_layout.addWidget(self.output_edit)

        output_actions = QHBoxLayout()
        self.clear_output_button = QPushButton("Clear Output")
        self.clear_output_button.setObjectName("GhostButton")
        self.clear_output_button.clicked.connect(self.clear_output)

        self.save_text_button = QPushButton("Save Output As Text")
        self.save_text_button.setObjectName("GhostButton")
        self.save_text_button.clicked.connect(self.save_translated_text)

        self.speak_button = QPushButton("Speak Output")
        self.speak_button.clicked.connect(self.speak_output)

        output_actions.addWidget(self.clear_output_button)
        output_actions.addWidget(self.save_text_button)
        output_actions.addWidget(self.speak_button)
        output_layout.addLayout(output_actions)

        splitter.addWidget(input_group)
        splitter.addWidget(output_group)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, 1)

        return tab

    def _build_audio_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        intro = QLabel("Select a saved audio file to play or delete it.")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.audio_list_widget = QListWidget()
        self.audio_list_widget.itemDoubleClicked.connect(lambda _: self.play_selected_audio())
        layout.addWidget(self.audio_list_widget, 1)

        actions = QHBoxLayout()
        self.play_audio_button = QPushButton("Play Selected Audio")
        self.play_audio_button.clicked.connect(self.play_selected_audio)

        self.delete_audio_button = QPushButton("Delete Selected Audio")
        self.delete_audio_button.setObjectName("GhostButton")
        self.delete_audio_button.clicked.connect(self.delete_selected_audio)

        self.refresh_audio_button = QPushButton("Refresh List")
        self.refresh_audio_button.setObjectName("GhostButton")
        self.refresh_audio_button.clicked.connect(self.refresh_audio_list)

        actions.addWidget(self.play_audio_button)
        actions.addWidget(self.delete_audio_button)
        actions.addWidget(self.refresh_audio_button)
        actions.addStretch(1)
        layout.addLayout(actions)

        self.selected_audio_label = QLabel("No file selected")
        self.selected_audio_label.setWordWrap(True)
        layout.addWidget(self.selected_audio_label)

        return tab

    def _build_settings_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(12)

        updater_group = QGroupBox("Update Settings")
        updater_layout = QVBoxLayout(updater_group)

        info = QLabel("Configure update checks against your GitHub Releases repository.")
        info.setWordWrap(True)
        updater_layout.addWidget(info)

        repo_row = QHBoxLayout()
        repo_label = QLabel("Repository (owner/repo)")
        self.repo_input = QLineEdit()
        self.repo_input.setPlaceholderText("your-org/LANG-TRANS-CODEBASE")
        self.repo_input.setText(self.github_repo)
        repo_row.addWidget(repo_label)
        repo_row.addWidget(self.repo_input, 1)
        updater_layout.addLayout(repo_row)

        self.auto_update_checkbox = QCheckBox("Auto-check updates on startup")
        self.auto_update_checkbox.setChecked(self.auto_check_updates_enabled)
        updater_layout.addWidget(self.auto_update_checkbox)

        self.repo_hint = QLabel("Tip: use 'owner/repo' style. Example: octocat/Hello-World")
        self.repo_hint.setStyleSheet("color: #6e7f92;")
        updater_layout.addWidget(self.repo_hint)

        buttons = QHBoxLayout()
        self.save_settings_button = QPushButton("Save Settings")
        self.save_settings_button.clicked.connect(self.save_settings)
        self.reset_settings_button = QPushButton("Use ENV Fallback")
        self.reset_settings_button.setObjectName("GhostButton")
        self.reset_settings_button.clicked.connect(self.reset_settings)
        self.check_now_button = QPushButton("Check Updates Now")
        self.check_now_button.setObjectName("GhostButton")
        self.check_now_button.clicked.connect(self.check_updates_clicked)
        buttons.addWidget(self.save_settings_button)
        buttons.addWidget(self.reset_settings_button)
        buttons.addWidget(self.check_now_button)
        buttons.addStretch(1)
        updater_layout.addLayout(buttons)

        app_group = QGroupBox("Application")
        app_layout = QVBoxLayout(app_group)
        app_layout.addWidget(QLabel(f"Current app version: {self.app_version}"))
        app_layout.addWidget(QLabel(APP_COPYRIGHT))
        app_layout.addWidget(QLabel("Changes are stored in ~/.lang-trans/settings.json"))

        layout.addWidget(updater_group)
        layout.addWidget(app_group)
        layout.addStretch(1)
        return tab

    def _load_settings(self) -> dict:
        default = {
            "github_repo": DEFAULT_GITHUB_REPO,
            "auto_check_updates": True,
        }

        try:
            if self.settings_path.exists():
                loaded = json.loads(self.settings_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    default.update(loaded)
        except Exception:
            pass

        return default

    def _persist_settings(self) -> None:
        self.settings_dir.mkdir(parents=True, exist_ok=True)
        self.settings_path.write_text(json.dumps(self.settings, indent=2), encoding="utf-8")

    def _is_valid_repo(self, repo: str) -> bool:
        parts = repo.split("/")
        return len(parts) == 2 and all(part.strip() for part in parts)

    def save_settings(self) -> None:
        repo = self.repo_input.text().strip()
        if repo != "owner/repo" and not self._is_valid_repo(repo):
            self._show_warning("Invalid Repository", "Use owner/repo format, for example: your-org/LANG-TRANS-CODEBASE")
            return

        if not repo:
            repo = DEFAULT_GITHUB_REPO

        self.github_repo = repo
        self.auto_check_updates_enabled = self.auto_update_checkbox.isChecked()

        self.settings["github_repo"] = self.github_repo
        self.settings["auto_check_updates"] = self.auto_check_updates_enabled

        try:
            self._persist_settings()
        except Exception as exc:
            self._show_error("Settings Error", "Could not save settings.", str(exc))
            return

        self._set_status("Settings saved")

    def reset_settings(self) -> None:
        self.github_repo = DEFAULT_GITHUB_REPO
        self.auto_check_updates_enabled = True
        self.repo_input.setText(self.github_repo)
        self.auto_update_checkbox.setChecked(self.auto_check_updates_enabled)
        self.settings["github_repo"] = self.github_repo
        self.settings["auto_check_updates"] = self.auto_check_updates_enabled

        try:
            self._persist_settings()
        except Exception as exc:
            self._show_error("Settings Error", "Could not reset settings.", str(exc))
            return

        self._set_status("Settings reset to defaults")

    def _set_status(self, message: str) -> None:
        self.status_bar.showMessage(message, 5000)

    def _show_error(self, title: str, message: str, details: str | None = None) -> None:
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Critical)
        box.setWindowTitle(title)
        box.setText(message)
        if details:
            box.setDetailedText(details)
        box.exec()

    def _show_warning(self, title: str, message: str) -> None:
        QMessageBox.warning(self, title, message)

    def _set_combo_to_code(self, combo: QComboBox, code: str) -> None:
        index = combo.findData(code)
        if index >= 0:
            combo.setCurrentIndex(index)

    def apply_theme(self, mode: str) -> None:
        app = QApplication.instance()
        if app is None:
            return

        if mode == "dark":
            app.setStyleSheet(DARK_STYLE)
            self.mode_badge.setText("Dark mode")
        else:
            app.setStyleSheet(LIGHT_STYLE)
            self.mode_badge.setText("Light mode")

    def toggle_theme(self, checked: bool) -> None:
        self.theme_mode = "dark" if checked else "light"
        self.apply_theme(self.theme_mode)

    def clear_input(self) -> None:
        self.input_edit.clear()

    def clear_output(self) -> None:
        self.output_edit.clear()

    def load_text_file(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Text File",
            str(Path.home()),
            "Text files (*.txt);;All files (*)",
        )
        if not file_path:
            return

        try:
            content = Path(file_path).read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            self._show_error("File Error", "Unable to read the selected file.", str(exc))
            return

        self.input_edit.setPlainText(content)
        self._set_status(f"Loaded {Path(file_path).name}")

    def translate_text(self) -> None:
        text = self.input_edit.toPlainText().strip()
        if not text:
            self._show_warning("No text", "Please enter or load text to translate.")
            return

        source_code = self.source_combo.currentData()
        target_code = self.target_combo.currentData()

        try:
            if self.auto_detect_checkbox.isChecked():
                detected_code = self.translator.auto_detectText(text)
                if detected_code:
                    source_code = detected_code
                    self._set_combo_to_code(self.source_combo, detected_code)

            translated = self.translator.translate_text(text, source_code, target_code)
        except Exception as exc:
            self._show_error("Translation Error", "Translation failed.", str(exc))
            return

        self.output_edit.setPlainText(translated)
        source_name = self.code_to_name.get(source_code, source_code)
        target_name = self.code_to_name.get(target_code, target_code)
        self._set_status(f"Translated from {source_name} to {target_name}")

    def save_translated_text(self) -> None:
        content = self.output_edit.toPlainText().strip()
        if not content:
            self._show_warning("No output", "There is no translated text to save.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Translated Text",
            str(Path.home()),
            "Text files (*.txt);;All files (*)",
        )
        if not file_path:
            return

        try:
            Path(file_path).write_text(content, encoding="utf-8")
        except Exception as exc:
            self._show_error("Save Error", "Unable to save the translated text.", str(exc))
            return

        self._set_status(f"Saved text to {Path(file_path).name}")

    def start_voice_input(self) -> None:
        if self.voice_worker and self.voice_worker.isRunning():
            self._show_warning("Voice Input", "Voice input is already running.")
            return

        self.voice_button.setEnabled(False)
        self._set_status("Listening for speech...")
        self.voice_worker = VoiceInputWorker()
        self.voice_worker.recognized.connect(self._handle_voice_result)
        self.voice_worker.failed.connect(self._handle_voice_error)
        self.voice_worker.finished.connect(self._voice_worker_finished)
        self.voice_worker.start()

    def _handle_voice_result(self, text: str) -> None:
        self.input_edit.setPlainText(text)
        self.translate_text()

    def _handle_voice_error(self, message: str) -> None:
        self._show_error("Voice Input Error", "Could not process microphone input.", message)

    def _voice_worker_finished(self) -> None:
        self.voice_button.setEnabled(True)
        self._set_status("Ready")

    def speak_output(self) -> None:
        text = self.output_edit.toPlainText().strip()
        if not text:
            self._show_warning("No output", "There is no translated text to speak.")
            return

        target_code = self.target_combo.currentData()
        target_name = self.target_combo.currentText()

        try:
            if self.save_audio_checkbox.isChecked():
                saved_path = self.tts.say_Savetext(text, target_code, target_name)
                self.refresh_audio_list()
                self._set_status(f"Saved audio to {saved_path}")

            self.tts.say_text(text, target_code)
        except Exception as exc:
            self._show_error(
                "Audio Not Supported",
                f"There is no audio support for {target_name}.",
                str(exc),
            )
            return

        self._set_status(f"Spoken output in {target_name}")

    def refresh_audio_list(self) -> None:
        self.audio_list_widget.clear()

        if not self.audio_root.exists():
            self.selected_audio_label.setText("No saved audio folder found yet.")
            return

        audio_files = sorted(
            (path for path in self.audio_root.rglob("*.mp3") if path.is_file()),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )

        if not audio_files:
            self.selected_audio_label.setText("No saved audio files found.")
            return

        for path in audio_files:
            item = QListWidgetItem(str(path.relative_to(self.audio_root)))
            item.setData(Qt.ItemDataRole.UserRole, str(path))
            self.audio_list_widget.addItem(item)

        self.selected_audio_label.setText(f"{len(audio_files)} saved audio file(s) available")

    def _selected_audio_path(self) -> Path | None:
        item = self.audio_list_widget.currentItem()
        if item is None:
            return None
        return Path(item.data(Qt.ItemDataRole.UserRole))

    def play_selected_audio(self) -> None:
        path = self._selected_audio_path()
        if path is None:
            self._show_warning("No selection", "Please select an audio file to play.")
            return

        if not path.exists():
            self._show_error("File Missing", "The selected audio file no longer exists.")
            self.refresh_audio_list()
            return

        try:
            sound = mixer.Sound(str(path))
            sound.play()
        except Exception as exc:
            self._show_error("Playback Error", "Unable to play the selected audio file.", str(exc))
            return

        self.selected_audio_label.setText(str(path))
        self._set_status(f"Playing {path.name}")

    def delete_selected_audio(self) -> None:
        path = self._selected_audio_path()
        if path is None:
            self._show_warning("No selection", "Please select an audio file to delete.")
            return

        response = QMessageBox.question(
            self,
            "Delete Audio",
            f"Delete {path.name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if response != QMessageBox.StandardButton.Yes:
            return

        try:
            path.unlink(missing_ok=True)
        except Exception as exc:
            self._show_error("Delete Error", "Unable to delete the selected file.", str(exc))
            return

        self.refresh_audio_list()
        self._set_status(f"Deleted {path.name}")

    def auto_check_updates(self) -> None:
        if not self.auto_check_updates_enabled:
            return
        if self.github_repo == "owner/repo":
            return
        self._start_update_check(silent_if_none=True)

    def check_updates_clicked(self) -> None:
        if self.github_repo == "owner/repo":
            self._show_warning(
                "Configure Repository",
                "Open the Settings tab and set a real GitHub repository in owner/repo format.",
            )
            return
        self._start_update_check(silent_if_none=False)

    def _start_update_check(self, silent_if_none: bool) -> None:
        if self.update_worker and self.update_worker.isRunning():
            return

        self.check_updates_button.setEnabled(False)
        self._set_status("Checking for updates...")
        self.update_worker = UpdateCheckWorker(self.github_repo, self.app_version)
        self.update_worker.success.connect(lambda has_update, release: self._handle_update_check_result(has_update, release, silent_if_none))
        self.update_worker.failed.connect(lambda message: self._handle_update_check_error(message, silent_if_none))
        self.update_worker.finished.connect(lambda: self.check_updates_button.setEnabled(True))
        self.update_worker.start()

    def _handle_update_check_error(self, message: str, silent: bool) -> None:
        if silent:
            self._set_status("Unable to auto-check updates")
            return
        self._show_error("Update Check Failed", "Could not check for updates.", message)
        self._set_status("Update check failed")

    def _handle_update_check_result(self, has_update: bool, release: ReleaseInfo, silent_if_none: bool) -> None:
        if not has_update:
            self._set_status(f"Up to date (v{self.app_version})")
            if not silent_if_none:
                QMessageBox.information(self, "No Updates", f"You are running the latest version (v{self.app_version}).")
            return

        message = (
            f"A new version is available.\n\n"
            f"Current: v{self.app_version}\n"
            f"Latest: {release.tag}\n\n"
            f"Download now?"
        )
        response = QMessageBox.question(
            self,
            "Update Available",
            message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes,
        )
        if response != QMessageBox.StandardButton.Yes:
            self._set_status("Update available")
            return

        self._download_release_asset(release)

    def _choose_release_asset(self, release: ReleaseInfo) -> ReleaseAsset | None:
        if not release.assets:
            return None
        preferred = (".exe", ".msi", ".zip")
        for ext in preferred:
            for asset in release.assets:
                if asset.name.lower().endswith(ext):
                    return asset
        return release.assets[0]

    def _download_release_asset(self, release: ReleaseInfo) -> None:
        asset = self._choose_release_asset(release)
        if asset is None:
            self._show_warning("No Asset", "No downloadable file was attached to the latest release.")
            return

        default_path = str(self.home / "Downloads" / asset.name)
        target_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Update As",
            default_path,
            "All files (*)",
        )
        if not target_path:
            return

        try:
            updater = GitHubUpdater(self.github_repo)
            saved = updater.download_asset(asset, Path(target_path))
        except UpdateError as exc:
            self._show_error("Download Failed", "Could not download the update asset.", str(exc))
            return

        QMessageBox.information(
            self,
            "Download Complete",
            f"Update downloaded to:\n{saved}\n\nInstall it when ready.",
        )
        self._set_status(f"Downloaded update asset: {asset.name}")

    def closeEvent(self, event) -> None:
        if self.update_worker and self.update_worker.isRunning():
            self.update_worker.quit()
            self.update_worker.wait(800)

        if self.voice_worker and self.voice_worker.isRunning():
            self.voice_worker.quit()
            self.voice_worker.wait(800)

        if self.extractor is not None:
            try:
                self.extractor.delete_images()
            except Exception:
                pass

        super().closeEvent(event)


def main() -> int:
    extractor: ExtractImages | None = None
    try:
        extractor = ExtractImages()
        extractor.xtract_images()
        atexit.register(extractor.delete_images)
    except Exception as exc:
        print(f"Asset extraction failed: {exc}")

    app = QApplication(sys.argv)
    QApplication.setStyle("Fusion")

    window = AppLanguage(extractor)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

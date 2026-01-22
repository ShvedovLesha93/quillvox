from __future__ import annotations
from typing import TYPE_CHECKING

from app.models.stt_config import STTConfig
from app.view_model.audio_player_vm import AudioPlayerViewModel
from app.view_model.file_selector_vm import FileSelectorViewModel
from app.translator import language_manager
from app.view_model.settings_vm import SettingsViewModel
from app.view_model.stt_runner_vm import STTRunnerViewModel
from app.view_model.transcript_vm import TranscriptViewModel
from app.view_model.waveform_vm import WaveformViewModel

if TYPE_CHECKING:
    from app.theme_manager import ThemeManager
    from PySide6.QtWidgets import QApplication
    from app.models.main_model import MainModel


class MainViewModel:
    def __init__(
        self, app: QApplication, main_model: MainModel, theme_manager: ThemeManager
    ):
        self.app = app
        self.main_model = main_model
        self.theme_manager = theme_manager
        self.waveform_vm = WaveformViewModel()
        self.audio_player_vm = AudioPlayerViewModel(self.waveform_vm)
        self.file_selector_vm = FileSelectorViewModel(
            main_model=self.main_model,
            audio_player_vm=self.audio_player_vm,
        )
        self.stt_config = STTConfig()
        self.settings_vm = SettingsViewModel(self.stt_config, self.theme_manager)
        self.stt_runner_vm = STTRunnerViewModel(
            stt_config=self.stt_config, main_model=self.main_model
        )
        self.transcript_vm = TranscriptViewModel(self.stt_runner_vm)

        self._connect_signals()

    def _connect_signals(self) -> None:
        self.settings_vm.general_settings_vm.language_changed.connect(
            self.change_app_language
        )

    def change_app_language(self, lang_code: str) -> None:
        language_manager.set_language(lang_code)

from __future__ import annotations
from typing import TYPE_CHECKING

from app.models.stt_config import STTConfig
from app.view_model.audio_player_vm import AudioPlayerVM
from app.view_model.file_selector import FileSelectorVM
from app.view_model.settings_vm import SettingsVM
from app.translator import language_manager
from app.view_model.stt_vm import STTViewModel
from app.view_model.transcript_vm import TranscriptVM

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
        self.audio_player_vm = AudioPlayerVM()
        self.file_selector_vm = FileSelectorVM(
            main_model=self.main_model,
            audio_player_vm=self.audio_player_vm,
        )
        self.settings_vm = SettingsVM(self.theme_manager)
        self.stt_vm = STTViewModel(stt_config=STTConfig(), main_model=self.main_model)
        self.transcript_vm = TranscriptVM(self.stt_vm)

        self._connect_signals()

    def _connect_signals(self) -> None:
        self.settings_vm.language_changed.connect(self.change_app_language)

    def change_app_language(self, lang_code: str) -> None:
        language_manager.set_language(lang_code)

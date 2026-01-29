from __future__ import annotations
from re import NOFLAG
from typing import TYPE_CHECKING

from PySide6.QtCore import Slot

from app.config.stt_config import STTConfig
from app.view_model.audio_player_vm import AudioPlayerViewModel
from app.view_model.file_selector_vm import FileSelectorViewModel
from app.view_model.settings_vm import SettingsViewModel
from app.view_model.stt_worker_vm import STTWorkerViewModel
from app.view_model.transcript_vm import TranscriptViewModel
from app.view_model.waveform_vm import WaveformViewModel

if TYPE_CHECKING:
    from app.config.general_config import GeneralConfig
    from app.theme_manager import ThemeManager
    from PySide6.QtWidgets import QApplication
    from app.models.main_model import MainModel


class MainViewModel:
    def __init__(
        self,
        app: QApplication,
        general_config: GeneralConfig,
        main_model: MainModel,
        theme_manager: ThemeManager,
    ):
        self.app = app
        self.main_model = main_model
        self.theme_manager = theme_manager

        self.stt_config = STTConfig()
        self.general_config = general_config
        self.transcript = self.main_model.stt_transcript

        self.waveform_vm = WaveformViewModel()
        self.audio_player_vm = AudioPlayerViewModel(self.waveform_vm)
        self.file_selector_vm = FileSelectorViewModel(
            stt_config=self.stt_config,
            main_model=self.main_model,
            audio_player_vm=self.audio_player_vm,
        )
        self.settings_vm = SettingsViewModel(
            general_config=self.general_config,
            stt_config=self.stt_config,
            theme_manager=self.theme_manager,
        )
        self.transcript_vm = TranscriptViewModel(
            main_vm=self, transcript=self.transcript, stt_config=self.stt_config
        )

        self.stt_worker_vm = STTWorkerViewModel(
            stt_config=self.stt_config, transcript_vm=self.transcript_vm
        )

    @Slot()
    def stop_transcript(self) -> None:
        self.stt_worker_vm.terminate_process()

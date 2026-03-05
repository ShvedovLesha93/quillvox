from __future__ import annotations
import subprocess
import sys
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal, Slot


from app.config import config_manager
from app.config.stt_config import STTConfig
from app.transcript import Transcript
from app.update_checker import UpdateChecker, UpdateStatus
from app.user_message import user_msg, MessageLevel
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

import logging

logger = logging.getLogger(__name__)


class MainViewModel(QObject):
    export_request = Signal(object)

    def __init__(
        self,
        app: QApplication,
        general_config: GeneralConfig,
        theme_manager: ThemeManager,
        log_queue,
    ):
        super().__init__()
        self.app = app
        self.theme_manager = theme_manager

        self.update_checker = UpdateChecker()
        self.update_checker.check_for_updates()
        self.update_checker.message.connect(self.check_for_updates)

        stt_config_json = config_manager.load_stt_config()
        if stt_config_json:
            self.stt_config = STTConfig().from_dict(stt_config_json) or STTConfig()
        else:
            self.stt_config = STTConfig()

        self.general_config = general_config
        self.transcript = Transcript()

        self.waveform_vm = WaveformViewModel()
        self.audio_player_vm = AudioPlayerViewModel(self.waveform_vm)
        self.file_selector_vm = FileSelectorViewModel(
            stt_config=self.stt_config,
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
            stt_config=self.stt_config,
            transcript_vm=self.transcript_vm,
            log_queue=log_queue,
        )

    @Slot(UpdateStatus, str)
    def check_for_updates(self, status: UpdateStatus, message: str) -> None:
        match status:
            case UpdateStatus.UPDATE_AVAILABLE:
                user_msg.info(message)
            case UpdateStatus.NO_UPDATE:
                user_msg.info(message)
            case UpdateStatus.ERROR:
                user_msg.error(message)

    def stop_transcript(self) -> None:
        self.stt_worker_vm.terminate_process()

    def has_transcript(self) -> bool:
        return True if self.transcript.segments else False

    def restart_application(self):
        logger.info("Restarting...")
        subprocess.Popen([sys.executable] + sys.argv)
        self.app.quit()

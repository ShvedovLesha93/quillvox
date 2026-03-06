from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING
from PySide6.QtCore import QObject, Signal
from pathlib import Path

from app.translator import language_manager, _
from app.user_message import user_msg

if TYPE_CHECKING:
    from app.config.stt_config import STTConfig
    from app.view_model.audio_player_vm import AudioPlayerViewModel

import logging

logger = logging.getLogger(__name__)


@dataclass
class SupportedFormats:
    audio: list[str] = field(
        default_factory=lambda: [
            "*.mp3",
            "*.wav",
            "*.ogg",
            "*.flac",
            "*.m4a",
        ]
    )
    video: list[str] = field(
        default_factory=lambda: [
            "*.mp4",
            "*.mkv",
            "*.avi",
            "*.mov",
            "*.flv",
            "*.webm",
            "*.wmv",
            "*.m4v",
        ]
    )


class FileSelectorViewModel(QObject):
    file_opened = Signal()

    def __init__(
        self,
        audio_player_vm: AudioPlayerViewModel,
        stt_config: STTConfig,
    ):
        super().__init__()
        self.audio_player_vm = audio_player_vm
        self.stt_config = stt_config

        self.file_formats = SupportedFormats()
        self.audio_formats = self.file_formats.audio
        # self.video_formats = self.file_formats.video

        self.last_dir = Path.home()
        self.last_filter = ""
        self.filter = ""

        self.retranslate()
        language_manager.language_changed.connect(self.retranslate)

    def generate_filter(self):
        def fmt(label: str, formats: list[str]) -> str:
            return f"{label} ({' '.join(formats)})"

        self.filter = ";;".join(
            [
                fmt(_("Audio Files"), self.audio_formats),
                # fmt(_("Video Files"), self.video_formats),
                # fmt(_("All Media Files"), self.audio_formats + self.video_formats),
            ]
        )

    def retranslate(self) -> None:
        self.generate_filter()

    def _validate(self, path: Path) -> bool:
        if not path.exists():
            user_msg.error(_("File '{file}' not found").format(file=path.name))
            logger.error("File not found: %s", path)
            return False

        if path == self.stt_config.audio:
            user_msg.warning(_("File '{file}' already opened").format(file=path.name))
            logger.warning("File '%s' already opened", path)
            return False

        return True

    def open_selected_file(self, file: Path | str, filter: str | None = None) -> None:
        if not isinstance(file, Path):
            file = Path(file)

        if self._validate(file):
            self.stt_config.audio = file
            self.last_dir = file.parent
            self.audio_player_vm.load(file)
            self.file_opened.emit()
            if filter:
                self.last_filter = filter

            logger.info("Audio file opened: %s", file.name)
            logger.info("Last directory: %s", self.last_dir)
            logger.debug("Media file stored in memory: %s", file)

            user_msg.info(_("File '{file}' has been opened").format(file=file.name))

    def get_open_file_kwargs(self) -> dict:
        return {
            "filter": self.filter,
            "selectedFilter": self.last_filter,
            "dir": str(self.last_dir),
        }

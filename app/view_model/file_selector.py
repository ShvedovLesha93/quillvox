from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6.QtCore import QObject
from pathlib import Path


if TYPE_CHECKING:
    from app.models.main_model import MainModel
    from app.view_model.audio_player_vm import AudioPlayerVM

import logging

logger = logging.getLogger(__name__)


class FileSelectorVM(QObject):

    def __init__(
        self,
        main_model: MainModel,
        audio_player_vm: AudioPlayerVM,
    ):
        super().__init__()
        self.main_model = main_model
        self.audio_player_vm = audio_player_vm
        self.media_file_model = self.main_model.media_file
        self.file_formats = self.main_model.file_formats

        self.audio_formats = self.file_formats.audio
        self.video_formats = self.file_formats.video
        self._last_directory = Path.home()
        self._last_filter = ""

    @property
    def filter(self) -> str:
        def fmt(label: str, formats: list[str]) -> str:
            return f"{label} ({' '.join(formats)})"

        return ";;".join(
            [
                fmt("Audio Files", self.audio_formats),
                fmt("Video Files", self.video_formats),
                fmt("All Media Files", self.audio_formats + self.video_formats),
            ]
        )

    def _validate(self, path: Path) -> tuple[bool, str]:
        if not path.exists():
            return False, "File not found"

        return True, ""

    def on_file_selected(self, file: Path):
        status, msg = self._validate(file)

        if status:
            self.media_file_model.path = file
            self.last_dir = file.parent
            self.audio_player_vm.load(file)

            logger.info("Audio file opened: %s", repr(file.name))
            logger.debug("Media file stored in memory: %s", file)

        else:
            logger.error(msg)

    @property
    def last_dir(self) -> Path:
        return self._last_directory

    @last_dir.setter
    def last_dir(self, path: Path):
        self._last_directory = path

    @property
    def last_filter(self) -> str:
        return self._last_filter

    @last_filter.setter
    def last_filter(self, filter: str):
        self._last_filter = filter

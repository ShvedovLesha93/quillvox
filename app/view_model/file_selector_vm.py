from __future__ import annotations
from typing import TYPE_CHECKING
from PySide6.QtCore import QObject, Signal
from pathlib import Path

from app.translator import language_manager, _
from app.user_message import user_msg


if TYPE_CHECKING:
    from app.models.main_model import MainModel
    from app.view_model.audio_player_vm import AudioPlayerViewModel

import logging

logger = logging.getLogger(__name__)


class FileSelectorViewModel(QObject):
    file_opened = Signal()

    def __init__(
        self,
        main_model: MainModel,
        audio_player_vm: AudioPlayerViewModel,
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
        self.filter = ""

        self.retranslate()
        language_manager.language_changed.connect(self.retranslate)

    def generate_filter(self):
        def fmt(label: str, formats: list[str]) -> str:
            return f"{label} ({' '.join(formats)})"

        self.filter = ";;".join(
            [
                fmt(_("Audio Files"), self.audio_formats),
                fmt(_("Video Files"), self.video_formats),
                fmt(_("All Media Files"), self.audio_formats + self.video_formats),
            ]
        )

    def retranslate(self) -> None:
        self.generate_filter()

    def _validate(self, path: Path) -> tuple[bool, str]:
        if not path.exists():
            return False, _("File not found")

        return True, ""

    def on_file_selected(self, opened_file: tuple[str, str] | None):
        if opened_file:
            file, filter = opened_file
            file_path = Path(file)

            status, msg = self._validate(file_path)

            if status:
                self.media_file_model.path = file_path
                self.last_dir = file_path.parent
                self.last_filter = filter
                self.audio_player_vm.load(file_path)
                self.file_opened.emit()

                logger.info("Audio file opened: %s", file_path.name)
                logger.info("Last directory: %s", self.last_dir)
                logger.debug("Media file stored in memory: %s", file_path)

                user_msg.info(
                    _("File '{file}' has been opened").format(file=file_path.name)
                )

            else:
                logger.error(msg)
                user_msg.error(msg)

        else:
            logger.info("No selected file")
            user_msg.warning(_("No selected file"))

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

from PySide6.QtCore import QObject
from pathlib import Path

from app.models.file_data import SupportedFormats


class FileSelectorVM(QObject):

    def __init__(self):
        super().__init__()
        self.formats = SupportedFormats()
        self.audio_formats = self.formats.audio
        self.video_formats = self.formats.video
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
            self.last_dir = file.parent
            print(msg)

    @property
    def last_dir(self) -> Path:
        return self._last_directory

    @last_dir.setter
    def last_dir(self, path: Path):
        self._last_directory = path.parent

    @property
    def last_filter(self) -> str:
        return self._last_filter

    @last_filter.setter
    def last_filter(self, filter: str):
        self._last_filter = filter

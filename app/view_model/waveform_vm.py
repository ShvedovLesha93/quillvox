from pathlib import Path
import shutil
from PySide6.QtCore import QObject, QThread, Signal
import logging

from app.waveform_loader_worker import WaveformLoaderWorker

logger = logging.getLogger(__name__)


def check_ffmpeg_installed() -> bool:
    ffmpeg_found = shutil.which("ffmpeg") is not None
    ffprobe_found = shutil.which("ffprobe") is not None
    return ffmpeg_found and ffprobe_found


class WaveformViewModel(QObject):
    waveform_loaded = Signal(object, object)
    changed_selected_segment = Signal(
        int, float, float
    )  # start (seconds), end (seconds)
    start_selection_changed = Signal(int, float)  # index, seconds
    end_selection_changed = Signal(int, float)  # index, seconds

    def __init__(self) -> None:
        super().__init__()
        self._thread: QThread | None = None
        self._worker: WaveformLoaderWorker | None = None

    def load_waveform_file(self, audio: Path) -> bool:
        if check_ffmpeg_installed():
            # Clean up previous thread if exists
            if self._thread is not None and self._thread.isRunning():
                self._thread.quit()
                self._thread.wait()

            self._thread = QThread()
            self._worker = WaveformLoaderWorker(audio)
            self._worker.moveToThread(self._thread)

            self._thread.started.connect(self._worker.run)
            self._worker.finished.connect(self.waveform_loaded.emit)
            # self._worker.error.connect(self._on_loading_error)
            self._worker.finished.connect(self._thread.quit)
            self._worker.error.connect(self._thread.quit)

            # Start loading
            self._thread.start()
            return True
        else:
            logger.error("ffmpeg and/or ffprobe not found on system")
            return False

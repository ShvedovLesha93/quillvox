from pathlib import Path
from PySide6.QtCore import QObject, QThread, Signal

from app.waveform_loader_worker import WaveformLoaderWorker


class WaveformViewModel(QObject):
    waveform_loaded = Signal(object, object)

    def __init__(self) -> None:
        super().__init__()
        self._thread: QThread | None = None
        self._worker: WaveformLoaderWorker | None = None

    def load_waveform_file(self, audio: Path) -> None:
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

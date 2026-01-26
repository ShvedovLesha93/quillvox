from __future__ import annotations
from dataclasses import asdict
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QThread, Signal, Slot
from app.stt_worker import Level, STTWorker
from app.user_message import user_msg
from app.config.stt_run_config import STTRunConfig
from app.models.stt_transcript import STTSegment
from app.translator import _

import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from faster_whisper.transcribe import Segment
    from app.config.stt_config import STTConfig
    from app.models.main_model import MainModel
    from app.stt_worker import WorkerMessage


class STTRunnerViewModel(QObject):
    segment_sent = Signal(str)
    finished = Signal()
    process_active = Signal()

    def __init__(self, stt_config: STTConfig, main_model: MainModel):
        super().__init__()
        self.main_model = main_model
        self.transcript = self.main_model.stt_transcript
        self.stt_config = stt_config

        self._thread: QThread | None = None
        self._worker: STTWorker | None = None

    def run_stt(self) -> None:
        if self._thread and self._thread.isRunning():
            logger.warning("STT thread already running")
            return

        self.transcript.segments.clear()

        cfg = self.build_run_config()

        self._thread = QThread()
        self._worker = STTWorker(cfg)

        self._worker.moveToThread(self._thread)

        # lifecycle
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._cleanup_thread)

        # data
        self._worker.segment_ready.connect(self._on_segment)
        self._worker.message.connect(self.send_message)
        self._worker.error_message.connect(logger.info)

        # ui
        self._thread.finished.connect(self._on_finished)

        self._thread.start()
        self.process_active.emit()

    @Slot(object)
    def send_message(self, msg: WorkerMessage) -> None:
        if msg.params:
            text = _(msg.message).format(**msg.params)
        else:
            text = _(msg.message)

        match msg.level:
            case Level.INFO:
                user_msg.info(text)
            case Level.ERROR:
                user_msg.error(text)

    def _on_segment(self, seg: Segment):
        self.transcript.segments.append(
            STTSegment(
                id=seg.id,
                start=seg.start,
                end=seg.end,
                text=seg.text,
            )
        )
        self.segment_sent.emit(seg.text)

    def _on_finished(self):
        logger.info("STT thread completed")
        logger.debug("Created transcript: %d segments", len(self.transcript.segments))

        self.finished.emit()

    def build_run_config(self) -> STTRunConfig:
        file = self.main_model.media_file.path

        if file:
            cfg = self.stt_config
            file = str(file.absolute())

            result = STTRunConfig(
                model=cfg.model,
                device=cfg.device,
                batch_size=cfg.batch_size,
                compute_type=cfg.compute_type,
                language=cfg.language,
                audio=file,
            )

            logger.info("Builded configs for stt: %s", asdict(result))

            return result
        else:
            raise FileNotFoundError

    def _cleanup_thread(self) -> None:
        self._thread = None
        self._worker = None

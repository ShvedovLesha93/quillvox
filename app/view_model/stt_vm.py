from __future__ import annotations
from dataclasses import asdict
import logging
from multiprocessing import Event, Process, Queue
from queue import Empty
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer, Signal

from app.models.stt_transcript import STTSegment
from app.stt_run_config import STTRunConfig
from app.stt_worker import stt_worker

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from faster_whisper.transcribe import Segment
    from app.models.stt_config import STTConfig
    from app.models.main_model import MainModel


class STTViewModel(QObject):
    segment_sent = Signal(str)
    finished = Signal()
    process_active = Signal()

    def __init__(self, stt_config: STTConfig, main_model: MainModel):
        super().__init__()
        self.main_model = main_model
        self.transcript = self.main_model.stt_transcript
        self.stt_config = stt_config
        self.process: Process | None = None

    def run_stt(self) -> None:
        if self.process is not None and self.process.is_alive():
            logger.warning("STT Process is already running")
            return

        cfg = self.build_run_config()

        self.result_queue = Queue()
        self.message_queue = Queue()
        self.terminate_event = Event()
        self.is_working = Event()

        self.process = Process(
            target=stt_worker,
            args=(
                cfg,
                self.result_queue,
                self.message_queue,
                self.terminate_event,
                self.is_working,
            ),
        )
        self.process.start()

        self.timer = QTimer()
        self.timer.timeout.connect(self._check_result)
        self.timer.start(500)
        self.process_active.emit()  # Emit signal to show process is still active

    def _check_result(self):
        # Check if process is still running
        if not self.process.is_alive():
            self.timer.stop()
            self.process.join()
            self.finished.emit()
            logger.info("STT process completed")
            logger.debug("Created transcript: %s", asdict(self.transcript))
            return

        # Process results
        try:
            while True:
                seg: Segment = self.result_queue.get_nowait()
                self.transcript.segments.append(
                    STTSegment(
                        id=seg.id,
                        start=seg.start,
                        end=seg.end,
                        text=seg.text,
                    )
                )
                self.segment_sent.emit(seg.text)
                print(seg)
        except Empty:
            pass

        # Process messages
        try:
            while True:
                message = self.message_queue.get_nowait()
                print(message)
        except Empty:
            pass

    def build_run_config(self) -> STTRunConfig:
        file = self.main_model.media_file.path

        if file:
            cfg = self.stt_config
            file = str(file.absolute())

            result = STTRunConfig(
                model=cfg.model.current,
                device=cfg.device.current,
                batch_size=cfg.batch_size.current,
                compute_type=cfg.compute_type.current,
                language=cfg.language.current,
                audio=file,
            )

            logger.info("Builded configs for stt: %s", asdict(result))

            return result
        else:
            raise FileNotFoundError

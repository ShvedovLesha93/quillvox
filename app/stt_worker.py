from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from gettext import gettext as _  # It is used for parsing only, not for translation
import time
from typing import Any, Mapping

from faster_whisper import WhisperModel
from PySide6.QtCore import QObject, Signal
import torch

from app.config.stt_run_config import STTRunConfig

logger = logging.getLogger(__name__)


class Level(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class WorkerMessage:
    level: Level
    message: str
    params: Mapping[str, Any] | None = None


class STTWorker(QObject):
    segment_ready = Signal(object)  # Segment
    error_message = Signal(str)
    message = Signal(object)
    finished = Signal()

    def __init__(self, cfg: STTRunConfig):
        super().__init__()
        self.cfg = cfg
        self._abort = False

    def run(self):
        model: WhisperModel | None = None
        try:
            model_name = self.cfg.model
            device = self.cfg.device
            batch_size = self.cfg.batch_size
            compute_type = self.cfg.compute_type
            language = self.cfg.language
            audio = self.cfg.audio

            if device == "cuda":
                if not torch.cuda.is_available():
                    self.message.emit(
                        WorkerMessage(
                            level=Level.ERROR,
                            message=_("CUDA is not installed on your device"),
                        )
                    )
                    return

            model = WhisperModel(
                model_size_or_path=model_name, device=device, compute_type=compute_type
            )

            self.message.emit(
                WorkerMessage(
                    level=Level.INFO,
                    message=_('"{model_name}" model has been loaded'),
                    params={"model_name": model_name},
                )
            )

            start = time.perf_counter()

            segments, info = model.transcribe(
                audio=audio,
                language="ru",
                # log_progress=True,
            )

            for seg in segments:
                if self._abort:
                    break
                self.segment_ready.emit(seg)

            end = time.perf_counter()
            duration = self.format_duration(end - start)

            self.message.emit(
                WorkerMessage(
                    level=Level.INFO,
                    message=_("Transcription completed in {duration}"),
                    params={"duration": duration},
                )
            )
        except Exception as e:
            self.error_message.emit(str(e))

        finally:
            if model is not None:
                del model

            import gc

            gc.collect()

            self.finished.emit()

    @staticmethod
    def format_duration(seconds: float) -> str:
        total_seconds = int(seconds)

        minutes, sec = divmod(total_seconds, 60)
        hours, minutes = divmod(minutes, 60)

        return f"{hours:02d}:{minutes:02d}:{sec:02d}"

    def stop(self):
        self._abort = True

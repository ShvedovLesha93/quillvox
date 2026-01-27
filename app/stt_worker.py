from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from gettext import gettext as _  # It is used for parsing only, not for translation
from multiprocessing import Queue
import time
from typing import Any, Mapping

from faster_whisper import WhisperModel
import torch

from app.config.stt_run_config import STTRunConfig


class Level(Enum):
    INFO = "info"
    DEBUG = "debug"
    WARNING = "warning"
    ERROR = "error"


@dataclass(frozen=True, slots=True)
class WorkerUserMessage:
    level: Level
    message: str
    params: Mapping[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class WorkerLogMessage:
    level: Level
    message: str
    params: Mapping[str, Any] | None = None


def stt_worker(
    cfg: STTRunConfig,
    result_queue: Queue,
    message_queue: Queue,
    terminate_event,
    is_working,
):
    is_working.set()

    model: WhisperModel | None = None
    model_name = cfg.model
    device = cfg.device
    batch_size = cfg.batch_size
    compute_type = cfg.compute_type
    language = cfg.language
    audio = cfg.audio

    message_queue.put(
        WorkerLogMessage(
            level=Level.INFO,
            message="Loaded parameters to STT worker: %s",
            params=asdict(cfg),
        )
    )

    if language == "auto":
        language = None

    if device == "cuda":
        if not torch.cuda.is_available():
            message_queue.put(
                WorkerUserMessage(
                    level=Level.ERROR,
                    message=_("CUDA is not installed on your device"),
                )
            )
            return

    try:
        # Load transcription model
        if terminate_event.is_set():
            return  # Exit early if termination requested

        model = WhisperModel(
            model_size_or_path=model_name, device=device, compute_type=compute_type
        )

        message_queue.put(
            WorkerUserMessage(
                level=Level.INFO,
                message=_('"{model_name}" model has been loaded'),
                params={"model_name": model_name},
            )
        )

        start = time.perf_counter()

        segments, info = model.transcribe(
            audio=audio,
            language=language,
            # log_progress=True,
        )

        message_queue.put(
            WorkerUserMessage(level=Level.INFO, message=_("Transcription in progress"))
        )

        for seg in segments:
            if terminate_event.is_set():
                return  # Exit early if termination requested
            result_queue.put(seg)

        end = time.perf_counter()
        duration = format_duration(end - start)

        message_queue.put(
            WorkerUserMessage(
                level=Level.INFO,
                message=_("Transcription completed in {duration}"),
                params={"duration": duration},
            )
        )
    except Exception as e:
        message_queue.put(
            WorkerUserMessage(
                level=Level.INFO,
                message=_("Error occurred during transcription: {e}"),
                params={"e": str(e)},
            )
        )

    finally:
        print("Finally from worker is done")
        is_working.clear()
        # Clean up GPU memory
        if device == "cuda":
            torch.cuda.empty_cache()


def format_duration(seconds: float) -> str:
    total_seconds = int(seconds)

    minutes, sec = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)

    return f"{hours:02d}:{minutes:02d}:{sec:02d}"

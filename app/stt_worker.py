from __future__ import annotations

from dataclasses import asdict, dataclass
from gettext import gettext as _  # It is used for parsing only, not for translation
import logging
from logging.handlers import QueueHandler
from multiprocessing import Queue
import time
from typing import TYPE_CHECKING, Any, Mapping

from faster_whisper import WhisperModel
import torch

from app.user_message import MessageLevel

if TYPE_CHECKING:
    from app.config.stt_config import STTConfig


@dataclass(frozen=True, slots=True)
class STTUserMessage:
    """Message intended for end users.

    Used to display human-readable information in the UI.
    Supports named parameters for safe formatting and localization.
    """

    level: MessageLevel
    message: str
    params: Mapping[str, Any] | None = None


def stt_worker(
    cfg: STTConfig,
    info_queue: Queue,
    segment_queue: Queue,
    segment_started_event,
    message_queue: Queue,
    terminate_event,
    log_queue: Queue | None,
):

    if log_queue:
        queue_handler = QueueHandler(log_queue)
        root = logging.getLogger()
        root.setLevel(logging.DEBUG)
        root.addHandler(queue_handler)

    logger = logging.getLogger(__name__)

    logger.info("Starting STT (speech-to-text) worker")

    model: WhisperModel | None = None
    model_name = cfg.model
    device = cfg.device
    batch_size = cfg.batch_size
    compute_type = cfg.compute_type
    language = cfg.language

    if cfg.audio:
        audio = str(cfg.audio.absolute())
    else:
        logger.error("Failed to upload file: %s", cfg.audio)

        raise FileNotFoundError("Audio doesn't exist")

    logger.info("Loaded parameters to STT worker: %s", asdict((cfg)))

    if language == "auto":
        language = None

    if device == "cuda":
        if not torch.cuda.is_available():
            message_queue.put(
                STTUserMessage(
                    level=MessageLevel.ERROR,
                    message=_(
                        "Unable to use GPU acceleration. Please install CUDA drivers for NVIDIA GPUs."
                    ),
                )
            )

            logger.error("CUDA not available")
            return

    try:
        if terminate_event.is_set():
            return  # Exit early if termination requested

        logger.info("Starting load model: %s", model_name)

        message_queue.put(
            STTUserMessage(
                level=MessageLevel.INFO,
                message=_("Starting load model: {model_name}"),
                params={"model_name": model_name},
            )
        )

        start_load = time.perf_counter()

        model = WhisperModel(
            model_size_or_path=model_name,
            device=device,
            compute_type=compute_type,
        )

        end_load = time.perf_counter()
        duration_load = format_duration(end_load - start_load)

        message_queue.put(
            STTUserMessage(
                level=MessageLevel.INFO,
                message=_("Successfully loaded {model_name}"),
                params={"model_name": model_name},
            )
        )

        logger.info(
            "model load successful: name=%s, load_time=%s", model_name, duration_load
        )

        logger.info("Starting transcription")

        segments, info = model.transcribe(
            audio=audio,
            language=language,
            vad_filter=True,
            log_progress=True,
        )

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("Transcription info: %s", asdict(info))
            logger.debug(
                "Transcription options initialized: %s",
                asdict(info.transcription_options),
            )
            logger.debug(
                "Vad options initialized: %s",
                asdict(info.vad_options),
            )

        info_queue.put(info)

        message_queue.put(
            STTUserMessage(
                level=MessageLevel.INFO,
                message=_("Transcription in process..."),
            )
        )

        segment_started_event.set()
        start = time.perf_counter()

        for seg in segments:
            if terminate_event.is_set():
                return
            segment_queue.put(seg)

        end = time.perf_counter()
        duration = format_duration(end - start)

        message_queue.put(
            STTUserMessage(
                level=MessageLevel.INFO,
                message=_("Transcription completed in {duration}"),
                params={"duration": duration},
            )
        )

        logger.info("Transcription completed in %s", duration)

    except Exception as e:
        logger.error("Error occurred during transcription: %s", e)
        message_queue.put(
            STTUserMessage(
                level=MessageLevel.ERROR,
                message=_("Error occurred during transcription: "),
            )
        )

    finally:
        # Clean up GPU memory
        if device == "cuda":
            try:
                if torch.cuda.is_available():

                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(
                            "GPU memory stats before cleanup: %s",
                            torch.cuda.memory_allocated(),
                        )

                    torch.cuda.empty_cache()

                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(
                            "GPU memory cleaned up. Device: %s",
                            torch.cuda.get_device_name(),
                        )

            except Exception as e:
                logger.warning("Failed to clean GPU memory: %s", e)
        else:
            logger.debug("Memory cleanup: Using %s, no GPU cache to clear", device)


def format_duration(seconds: float) -> str:
    total_seconds = int(seconds)

    minutes, sec = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)

    return f"{hours:02d}:{minutes:02d}:{sec:02d}"

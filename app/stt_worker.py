from __future__ import annotations
from enum import Enum
from multiprocessing import Queue
from typing import TYPE_CHECKING
from faster_whisper import WhisperModel
from gettext import gettext as get_


class MessageLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


if TYPE_CHECKING:
    from app.stt_run_config import STTRunConfig


def stt_worker(
    cfg: STTRunConfig,
    result_queue: Queue,
    message_queue: Queue,
    terminate_event,
    is_working,
):
    is_working.set()

    model_name = cfg.model
    device = cfg.device
    batch_size = cfg.batch_size
    compute_type = cfg.compute_type
    language = cfg.language
    audio = cfg.audio
    print("Configs:")

    cfgp = (
        model_name,
        device,
        batch_size,
        compute_type,
        language,
        audio,
    )
    print(cfgp)

    if language == "auto":
        language = None

    try:

        # Load transcription model
        if terminate_event.is_set():
            return  # Exit early if termination requested

        message_queue.put(
            (
                MessageLevel.INFO,
                get_('Loading "{model_name}" model...'),
                {"model_name": model_name},
            )
        )
        model = WhisperModel(
            model_size_or_path=model_name, device=device, compute_type=compute_type
        )

        message_queue.put(
            (
                MessageLevel.INFO,
                get_('"{model_name}" model has been loaded.').format(
                    model_name=model_name
                ),
            )
        )

        if terminate_event.is_set():
            return

        # Transcribe (this may take long)
        message_queue.put((MessageLevel.INFO, get_("Starting transcription...")))

        segments, info = model.transcribe(
            audio=audio,
            language="ru",
            # log_progress=True,
        )

        for seg in segments:
            result_queue.put(seg)

        message_queue.put(
            (MessageLevel.INFO, get_("Transcription completed successfully!"))
        )

    except FileNotFoundError as e:
        error_msg = f"Audio file not found: {str(e)}"
        message_queue.put(
            (MessageLevel.ERROR, get_("Error: {msg}").format(msg=error_msg))
        )

    # except torch.cuda.OutOfMemoryError:
    #     error_msg = "GPU out of memory. Try using CPU or a smaller model."
    #     message_queue.put((logmsg.ERROR, get_("Error: {msg}").format(msg=error_msg)))

    except Exception as e:
        message_queue.put(
            (
                MessageLevel.ERROR,
                get_("Error occurred during transcription: {e}").format(e=e),
            )
        )

    finally:
        is_working.clear()
    #     # Clean up GPU memory
    #     if device == "cuda":
    #         torch.cuda.empty_cache()

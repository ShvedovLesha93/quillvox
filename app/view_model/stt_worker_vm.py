from __future__ import annotations
from dataclasses import asdict
import os
import signal
from queue import Empty
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, QTimer, Signal
from app.stt_worker import WorkerLogMessage, WorkerUserMessage, stt_worker, Level
from app.user_message import user_msg
from app.config.stt_run_config import STTRunConfig
from app.translator import _
from multiprocessing import Event, Process, Queue
from concurrent.futures import ThreadPoolExecutor


import logging

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app.view_model.transcript_vm import TranscriptViewModel
    from app.config.stt_config import STTConfig


class STTWorkerViewModel(QObject):
    finished = Signal()
    process_started = Signal()

    def __init__(
        self,
        transcript_vm: TranscriptViewModel,
        stt_config: STTConfig,
    ):
        super().__init__()
        self.transcript_vm = transcript_vm
        self.stt_config = stt_config

        self.process: Process | None = None
        self.executer = ThreadPoolExecutor(max_workers=1)
        self.termination_future = None

    def run_stt(self) -> None:
        if self.process is not None and self.process.is_alive():
            logger.warning("STT process already running")
            return

        cfg = self.build_run_config()

        self.info_queue = Queue()
        self.segment_queue = Queue()
        self.message_queue = Queue()
        self.terminate_event = Event()
        self.is_working = Event()

        self.process = Process(
            target=stt_worker,
            args=(
                cfg,
                self.info_queue,
                self.segment_queue,
                self.message_queue,
                self.terminate_event,
                self.is_working,
            ),
        )
        self.process.start()

        self.timer = QTimer()
        self.timer.timeout.connect(self._check_result)
        self.timer.start(100)

        self.transcript_vm.on_start_transcription()
        self.process_started.emit()

    def _check_result(self):
        # Check if process is still running
        if not self.process.is_alive():  # pyright: ignore
            self.timer.stop()  # pyright: ignore
            self.process.join()  # pyright: ignore
            self.finished.emit()
            logger.info("STT process completed")
            return

        # Process segments
        try:
            while True:
                seg = self.segment_queue.get_nowait()  # pyright: ignore
                self.transcript_vm._on_segment(seg)
        except Empty:
            pass

        # Process transcript info
        try:
            while True:
                info = self.info_queue.get_nowait()  # pyright: ignore
                self.transcript_vm._on_info(info)
        except Empty:
            pass

        # Process messages
        try:
            while True:
                msg = self.message_queue.get_nowait()  # pyright: ignore
                if isinstance(msg, WorkerUserMessage):
                    self._send_user_message(msg)
                elif isinstance(msg, WorkerLogMessage):
                    self._send_log_message(msg)
        except Empty:
            pass

    def _send_log_message(self, msg: WorkerLogMessage) -> None:
        log_functions = {
            Level.INFO: logger.info,
            Level.WARNING: logger.warning,
            Level.ERROR: logger.error,
            Level.DEBUG: logger.debug,
        }

        try:
            log_fn = log_functions[msg.level]
        except KeyError:
            logger.error(f"Unknown log level: {msg.level}, message: {msg.message}")
            return

        if msg.params:
            log_fn(msg.message, msg.params)
        else:
            log_fn(msg.message)

    def _send_user_message(self, msg: WorkerUserMessage) -> None:
        if msg.params:
            text = _(msg.message).format(**msg.params)
        else:
            text = _(msg.message)

        match msg.level:
            case Level.INFO:
                user_msg.info(text)
            case Level.ERROR:
                user_msg.error(text)

    def _on_finished(self):
        logger.info("STT thread completed")

        self.finished.emit()

    def build_run_config(self) -> STTRunConfig:
        cfg = self.stt_config

        if cfg.audio:

            result = STTRunConfig(
                model=cfg.model,
                device=cfg.device,
                batch_size=cfg.batch_size,
                compute_type=cfg.compute_type,
                language=cfg.language,
                audio=str(cfg.audio.absolute()),
            )

            logger.info("Builded configs for stt: %s", asdict(result))

            return result
        else:
            raise FileNotFoundError

    def terminate_process(self):
        """Terminate the running transcription process safely."""
        if self.termination_future and not self.termination_future.done():
            logger.warning("Termination already in progress")
            return

        if self.is_working.is_set():
            logger.info("Terminating transcription process...")

            # Stop the timer first (no more periodic checks)
            if self.timer:
                self.timer.stop()

            # Run termination in background thread
            self.termination_future = self.executer.submit(self._terminate_background)
        else:
            logger.info("No active process to terminate")

    def _terminate_background(self):
        # Ask the worker process to exit gracefully
        if self.terminate_event:
            self.terminate_event.set()

        # Give the process some time to finish gracefully
        if self.process:
            self.process.join(timeout=5.0)

            # If still alive, try force terminate
            if self.process.is_alive():
                logger.info("Force terminating process...")
                self.process.terminate()
                self.process.join(timeout=2.0)

                # Last resort: kill the process directly
                if self.process.is_alive():
                    if os.name == "nt":  # Windows
                        # On Windows, os.kill with SIGTERM calls TerminateProcess (hard kill)
                        os.kill(self.process.pid, signal.SIGTERM)  # type: ignore
                        print("The process was killed (Windows)")
                    else:  # Unix/Linux/Mac
                        os.kill(self.process.pid, signal.SIGKILL)
                        print("The process was killed (Unix)")
                    self.process.join()

        self.finished.emit()

        logger.info("Process terminated")
        user_msg.info(_("Transcription is terminated"))

        # Clean up resources
        self._cleanup()

    def _cleanup(self):
        """Clean up resources after process termination or completion."""

        # Stop the timer completely
        if self.timer:
            self.timer.stop()
            self.timer = None

        # Drain result queue to avoid memory leaks
        if self.segment_queue:
            try:
                while True:
                    self.segment_queue.get_nowait()
            except Exception:
                pass

        # Drain message queue to avoid memory leaks
        if self.message_queue:
            try:
                while True:
                    self.message_queue.get_nowait()
            except Exception:
                pass

        # Reset process-related attributes
        self.process = None
        self.segment_queue = None
        self.message_queue = None
        self.pause_event = None
        self.terminate_event = None

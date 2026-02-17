import logging
from logging.handlers import RotatingFileHandler, QueueHandler, QueueListener
from multiprocessing import Queue
from rich.logging import RichHandler


def configure_logging(
    multiprocessing_mode=False,
    console_level: int = logging.INFO,
    file_level: int = logging.INFO,
    file_log_name="app",
    show_module_name=True,
    file_logging=True,
) -> tuple[Queue, QueueListener] | None:

    root = logging.getLogger()
    if root.handlers:
        raise RuntimeError("Logging already configured! Call this only once in main().")

    # Create handlers (these run in MAIN process only)
    rich_handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
        show_time=True,
        show_level=True,
        show_path=True,
    )
    rich_handler.setLevel(console_level)

    handlers = []
    handlers.append(rich_handler)

    if file_logging:
        format = "%(asctime)s - %(levelname)s - %(message)s"
        if show_module_name:
            format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

        file_handler = RotatingFileHandler(
            f"{file_log_name}.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )

        file_handler.setLevel(file_level)
        file_handler.setFormatter(logging.Formatter(format))

        handlers.append(file_handler)

    if multiprocessing_mode:
        # Set up queue for multiprocessing
        log_queue = Queue(-1)  # No size limit

        # QueueListener processes logs from queue in main process
        listener = QueueListener(log_queue, *handlers, respect_handler_level=True)
        listener.start()

        # Configure root logger to use queue
        queue_handler = QueueHandler(log_queue)
        root.addHandler(queue_handler)
        root.setLevel(console_level)

        return log_queue, listener
    else:
        if file_logging:
            root.addHandler(file_handler)  # pyright: ignore

        root.addHandler(rich_handler)
        root.setLevel(console_level)

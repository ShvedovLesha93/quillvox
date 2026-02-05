import logging
from logging.handlers import RotatingFileHandler, QueueHandler, QueueListener
from multiprocessing import Queue
from rich.logging import RichHandler


def configure_logging(
    console_level: int = logging.INFO, file_level: int = logging.INFO
) -> tuple[Queue, QueueListener]:
    """Configure application-wide logging.

    Sets up console and file handlers and initializes a multiprocessing-safe
    logging queue with a corresponding listener. This function is intended
    to be called once during application startup.

    Args:
        console_level: Log level for console output.
        file_level: Log level for file output.

    Returns:
        A tuple of (log_queue, listener) used for multiprocessing logging.

    Raises:
        RuntimeError: If logging has already been configured.
    """
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

    file_handler = RotatingFileHandler(
        "app.log",
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )

    file_handler.setLevel(file_level)
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )

    handlers = [rich_handler, file_handler]

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

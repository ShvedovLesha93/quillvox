import logging
from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler

import app.waveform_loader_worker


def configure_logging() -> None:
    """Configure logging once for the entire application."""
    root = logging.getLogger()
    if root.handlers:
        return

    root.setLevel(logging.DEBUG)

    # ---- silence specific modules ----
    logging.getLogger(app.waveform_loader_worker.__name__).setLevel(logging.WARNING)

    console = RichHandler(rich_tracebacks=True, markup=True)
    console.setLevel(logging.DEBUG)
    console.setFormatter(logging.Formatter("[%(module)s] %(message)s"))
    root.addHandler(console)

    file = RotatingFileHandler(
        "app.log",
        encoding="utf-8",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
    )
    file.setLevel(logging.INFO)
    file.setFormatter(
        logging.Formatter("%(asctime)s - [%(module)s] - %(levelname)s - %(message)s")
    )
    root.addHandler(file)

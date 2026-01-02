# logging_config.py
import logging
from rich.logging import RichHandler


def configure_logging() -> None:
    """Configure logging once for the entire application."""
    root = logging.getLogger()
    if root.handlers:
        return

    root.setLevel(logging.DEBUG)

    console = RichHandler(rich_tracebacks=True, markup=True)
    console.setLevel(logging.DEBUG)
    console.setFormatter(logging.Formatter("[%(module)s] %(message)s"))
    root.addHandler(console)

    file = logging.FileHandler("app.log", encoding="utf-8")
    file.setLevel(logging.INFO)
    file.setFormatter(
        logging.Formatter("%(asctime)s - [%(module)s] - %(levelname)s - %(message)s")
    )
    root.addHandler(file)

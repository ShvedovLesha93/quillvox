from pathlib import Path

from app.constants import ThemeMode

import app.resources.styles as styles
import logging

logger = logging.getLogger(__name__)


class StyleLoader:
    """Load app-wide theme stylesheets."""

    _cache: dict[ThemeMode, str] = {}

    @classmethod
    def load(cls, theme: ThemeMode) -> str:
        """Load complete theme stylesheet.

        Args:
            theme: Theme mode ("dark" or "light")

        Returns:
            Complete QSS stylesheet string
        """
        if theme in cls._cache:
            logger.debug("Loaded stylesheet from cache for theme: %s", theme)
            return cls._cache[theme]

        if theme == ThemeMode.DARK:
            theme_ = "dark"
        else:
            theme_ = "light"

        styles_folder = Path(styles.__file__).parent
        style_path = styles_folder / f"{theme_}.qss"

        logger.debug("Styles folder: %s", styles_folder)

        if not style_path.exists():
            logger.error("Theme file not found: %s", style_path)
            raise FileNotFoundError(f"Theme file not found: {style_path}")

        style_content = style_path.read_text(encoding="utf-8")
        logger.info("Loaded stylesheet from file: %s", style_path)

        cls._cache[theme] = style_content
        logger.debug("Cached stylesheet for theme: %s", theme)

        return style_content

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the style cache."""
        logger.info("Clearing stylesheet cache")
        cls._cache.clear()

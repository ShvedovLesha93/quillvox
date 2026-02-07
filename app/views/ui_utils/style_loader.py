from pathlib import Path
from typing import Literal

from app.constants import ThemeMode

Styles = Literal["flat"]


class StyleLoader:
    """Load and cache QSS styles."""

    _cache: dict[str, str] = {}

    @classmethod
    def load(cls, theme: ThemeMode, style: Styles = "flat") -> str:
        """Load QSS style for a specific theme.

        Args:
            theme: Theme enum (LIGHT or DARK)
            style: Style name (e.g., 'flat_icon')

        Returns:
            QSS stylesheet string
        """

        if theme not in (ThemeMode.DARK, ThemeMode.LIGHT):
            raise RuntimeError(
                f"Invalid theme: {theme!r}. Expected ThemeMode.DARK or ThemeMode.LIGHT."
            )

        cache_key = f"{theme.value}_{style}"

        if cache_key in cls._cache:
            return cls._cache[cache_key]

        import app.views.styles.buttons as btn_styles

        styles_folder = Path(btn_styles.__file__).parent
        if theme == ThemeMode.DARK:
            style_path = styles_folder / "dark_theme" / f"{style}.qss"
        else:
            style_path = styles_folder / "light_theme" / f"{style}.qss"

        if not style_path.exists():
            raise FileNotFoundError(f"Style file not found: {style_path}")

        # Load and cache
        style_content = style_path.read_text(encoding="utf-8")
        cls._cache[style] = style_content

        return style_content

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the style cache. Useful for development/hot-reload."""
        cls._cache.clear()

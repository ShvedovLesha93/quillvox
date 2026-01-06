import locale
import gettext

from PySide6.QtCore import QObject, Signal
import re


class LanguageManager(QObject):
    language_changed = Signal()

    def __init__(self):
        super().__init__()

        self._ = None
        self.translator = None
        self.current_lang = self.get_language_code()
        self.set_language(self.current_lang)

    def get_language_code(self) -> str:
        lang, _ = locale.getlocale()

        if not lang:
            return "en"

        # Normalize to lowercase for easier matching
        lang = lang.lower()

        # Case 1: POSIX-style, e.g. "ru_by", "en_us"
        if re.match(r"^[a-z]{2}_[a-z]{2}$", lang):
            return lang.split("_")[0]

        # Case 2: Windows-style, e.g. "russian_belarus"
        mapping = {
            "english": "en",
            "russian": "ru",
        }

        base = lang.split("_")[0].split(" ")[0]  # "russian_belarus" → "russian"
        return mapping.get(base, "en")

    def set_language(self, lang_code: str) -> None:
        self.current_lang = lang_code

        self.translator = gettext.translation(
            domain="messages",
            localedir="app/locales",
            languages=[self.current_lang],
            fallback=True,
        )
        print(f"Language set to {lang_code}")

        self._ = self.translator.gettext
        self.language_changed.emit()

    def get_text(self, message: str) -> str:
        return self._(message)  # pyright: ignore


language_manager = LanguageManager()


def _(message: str) -> str:
    return language_manager.get_text(message)

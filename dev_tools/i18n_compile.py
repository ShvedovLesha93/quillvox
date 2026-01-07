import argparse
from pathlib import Path
import sys

import polib


BASE_LOCALES_PATH = Path("app/locales")


def compile_language(lang: str) -> None:
    lc_messages_path = BASE_LOCALES_PATH / lang / "LC_MESSAGES"
    po_file = lc_messages_path / "messages.po"
    mo_file = lc_messages_path / "messages.mo"

    if not po_file.exists():
        print(f"Warning: Skipping '{lang}': messages.po not found", file=sys.stderr)
        return

    # Defensive: ensure directory exists
    lc_messages_path.mkdir(parents=True, exist_ok=True)

    po = polib.pofile(po_file)
    po.save_as_mofile(str(mo_file))

    print(f"Compiled {mo_file}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compile gettext .po files into .mo files"
    )
    parser.add_argument(
        "languages",
        nargs="+",
        help="Language codes (e.g. en ru de)",
    )
    args = parser.parse_args()

    for lang in args.languages:
        compile_language(lang)


if __name__ == "__main__":
    main()

import argparse
import sys
from pathlib import Path

import polib


BASE_LOCALES_PATH = Path("app/locales")
POT_FILE = BASE_LOCALES_PATH / "messages.pot"


def process_language(lang: str) -> None:
    lang_path = BASE_LOCALES_PATH / lang
    lc_messages_path = lang_path / "LC_MESSAGES"
    po_file = lc_messages_path / "messages.po"

    lc_messages_path.mkdir(parents=True, exist_ok=True)

    pot = polib.pofile(POT_FILE)

    if not po_file.exists():
        # Initialize new PO file (msginit replacement)
        po = polib.POFile()

        po.metadata = {
            "Language": lang,
            "Content-Type": "text/plain; charset=UTF-8",
        }

        for entry in pot:
            po.append(
                polib.POEntry(
                    msgid=entry.msgid,
                    msgid_plural=entry.msgid_plural,
                    msgstr_plural={} if entry.msgid_plural else None,
                    occurrences=entry.occurrences,
                    flags=entry.flags,
                    comment=entry.comment,
                )
            )

        po.save(str(po_file))
        print(f"Initialized {po_file}")

    else:
        # Update existing PO file (msgmerge replacement)
        po = polib.pofile(po_file)

        po.merge(pot)
        po.save()
        print(f"Updated {po_file}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Initialize or update gettext .po files using polib"
    )
    parser.add_argument(
        "languages",
        nargs="+",
        help="Language codes (e.g. en ru de)",
    )
    args = parser.parse_args()

    if not POT_FILE.exists():
        print(f"messages.pot not found at {POT_FILE}", file=sys.stderr)
        sys.exit(1)

    for lang in args.languages:
        process_language(lang)


if __name__ == "__main__":
    main()

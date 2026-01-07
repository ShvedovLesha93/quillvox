import subprocess
import sys
from pathlib import Path


APP_DIR = Path("app")
LOCALES_DIR = APP_DIR / "locales"
POT_FILE = LOCALES_DIR / "messages.pot"


def main() -> None:
    LOCALES_DIR.mkdir(parents=True, exist_ok=True)

    # Collect all .py files under app/
    py_files = [str(p) for p in APP_DIR.rglob("*.py") if "__pycache__" not in p.parts]

    if not py_files:
        print("No Python files found under app/", file=sys.stderr)
        return

    try:
        subprocess.run(
            [
                "xgettext",
                "-L",
                "Python",
                "-k_",
                "-o",
                str(POT_FILE),
                "--files-from=-",
            ],
            input="\n".join(py_files),
            text=True,
            check=True,
        )
    except FileNotFoundError:
        print("xgettext not found in PATH", file=sys.stderr)
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)

    print(f"Generated {POT_FILE}")


if __name__ == "__main__":
    main()

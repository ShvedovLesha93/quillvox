import shutil
from pathlib import Path
import subprocess

from app.constants import FrozenPath

DIST_PATH = Path("dist/QuillVox")


def run_pyinstaller() -> tuple[bool, str | None]:
    cmd = ["uv", "run", "pyinstaller", "main.spec"]

    try:
        subprocess.run(cmd, check=True)
        return (True, None)
    except subprocess.CalledProcessError as e:
        return (False, str(e))


def copy_files(copy_from: Path, to_folder: str, include: str) -> None:
    for f in copy_from.rglob(include):
        relative = f.relative_to(copy_from)
        target = DIST_PATH / to_folder / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)


def copy_manager() -> None:
    import app.resources.styles as styles
    import app.locales as locales

    styles_path = Path(styles.__file__).parent
    locales_path = Path(locales.__file__).parent

    copy_files(styles_path, to_folder=FrozenPath.STYLES.value, include="*.qss")
    copy_files(locales_path, to_folder=FrozenPath.LOCALES.value, include="*.mo")


def clean():
    """Clean previous builds."""
    print("🧹 Cleaning previous builds...")

    dirs_to_clean = ["dist"]
    for dir_name in dirs_to_clean:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"   Removed {dir_name}/")

    print("✓ Clean complete\n")


def main() -> None:
    clean()
    result, err = run_pyinstaller()
    if result:
        print("✓ PyInstaller build complete\n")
        copy_manager()
        print("✓ Locales copied\n")
    else:
        print(f"✗ Build failed: {err}")


if __name__ == "__main__":
    main()

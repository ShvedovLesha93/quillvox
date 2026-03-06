from pathlib import Path
import tarfile
import platform
import zipfile


EXCLUDED_FROM_ARCHIVE = {".venv", "uv.exe", "uv"}


def create_archive() -> None:
    release_path = Path("release")
    release_path.mkdir(exist_ok=True)
    dist_path = Path("dist")
    system = platform.system()

    found = [name for name in EXCLUDED_FROM_ARCHIVE if (dist_path / name).exists()]
    if found:
        raise RuntimeError(
            f"dist/ contains files that must not be archived: {', '.join(found)}. "
            f"Clean up dist/ before creating a release archive."
        )

    if system == "Linux":
        archive_path = release_path / "QuillVox.tar.gz"
        with tarfile.open(archive_path, "w:gz") as tar:
            for path in dist_path.rglob("*"):
                tar.add(path, arcname=path.relative_to(dist_path))
        print(f"Archive created: {archive_path}")

    elif system == "Windows":
        archive_path = release_path / "QuillVox.zip"
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for path in dist_path.rglob("*"):
                zf.write(path, arcname=path.relative_to(dist_path))
        print(f"Archive created: {archive_path}")

    else:
        raise RuntimeError(f"Unsupported platform: {system}")


if __name__ == "__main__":
    create_archive()

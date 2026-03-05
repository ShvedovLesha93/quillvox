from pathlib import Path
import tarfile
import platform
import subprocess


def create_archive() -> None:
    if platform.system() == "Linux":
        release_path = Path("release")
        release_path.mkdir(exist_ok=True)

        archive_path = release_path / "QuillVox.tar.gz"
        dist_path = Path("dist")

        with tarfile.open(archive_path, "w:gz") as tar:
            for path in dist_path.rglob("*"):
                tar.add(path, arcname=path.relative_to(dist_path))

        print(f"Archive created: {archive_path}")
    else:
        subprocess.run(["iscc", "installer.iss"])


if __name__ == "__main__":
    create_archive()

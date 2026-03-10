import os
from pathlib import Path
import subprocess
import shutil
import sys


def has_cuda_support() -> bool:
    if shutil.which("nvidia-smi"):
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                return True
        except Exception:
            pass

    if shutil.which("nvcc"):
        try:
            result = subprocess.run(
                ["nvcc", "--version"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return True
        except Exception:
            pass

    return False


def has_nvidia_libs_installed() -> bool:
    import sysconfig

    site_packages = Path(sysconfig.get_path("purelib"))
    nvidia = site_packages / "nvidia"

    if sys.platform == "win32":
        paths = [
            nvidia / "cudnn" / "bin",
            nvidia / "cublas" / "bin",
        ]
    else:
        paths = [
            nvidia / "cudnn" / "lib",
            nvidia / "cublas" / "lib",
        ]

    result = all(p.exists() for p in paths)
    # logger.debug("has_nvidia_libs_installed (%s): %s", sys.platform, result)
    # for p in paths:
    #     logger.debug("  %s -> exists=%s", p, p.exists())
    return result


def has_nvidia_libs_in_env() -> bool:
    import sysconfig

    site_packages = Path(sysconfig.get_path("purelib"))
    nvidia = site_packages / "nvidia"

    if sys.platform == "win32":
        paths = [
            str(nvidia / "cudnn" / "bin"),
            str(nvidia / "cublas" / "bin"),
        ]
        current = os.environ.get("PATH", "")
    else:
        paths = [
            str(nvidia / "cudnn" / "lib"),
            str(nvidia / "cublas" / "lib"),
        ]
        current = os.environ.get("LD_LIBRARY_PATH", "")

    return all(p in current for p in paths)

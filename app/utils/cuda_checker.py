import os
from pathlib import Path
import subprocess
import shutil


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


def has_nvidia_libs_in_env() -> bool:
    import sysconfig

    site_packages = Path(sysconfig.get_path("purelib"))
    nvidia = site_packages / "nvidia"
    paths = [
        str(nvidia / "cudnn/lib"),
        str(nvidia / "cublas/lib"),
    ]
    current = os.environ.get("LD_LIBRARY_PATH", "")
    return all(p in current for p in paths)


def has_nvidia_libs_installed() -> bool:
    import sysconfig

    site_packages = Path(sysconfig.get_path("purelib"))
    nvidia = site_packages / "nvidia"
    paths = [
        nvidia / "cudnn" / "lib",
        nvidia / "cublas" / "lib",
    ]
    result = all(p.exists() for p in paths)
    print(f"has_nvidia_libs_installed: {result}")
    print(f"  cudnn: {paths[0].exists()} -> {paths[0]}")
    print(f"  cublas: {paths[1].exists()} -> {paths[1]}")
    return result

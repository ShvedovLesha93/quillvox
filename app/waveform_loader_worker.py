from pathlib import Path
import subprocess
import sys
import traceback
import numpy as np
import logging
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)


def get_subprocess_startup_info():
    """Get startup info to hide console windows on Windows."""
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        return startupinfo
    return None


def get_creation_flags():
    """Get creation flags to hide console windows on Windows."""
    if sys.platform == "win32":
        return subprocess.CREATE_NO_WINDOW
    return 0


class WaveformLoaderWorker(QObject):
    """
    Worker that streams audio through ffmpeg and computes a min/max
    envelope (Audacity-style). Extremely memory-efficient.
    """

    finished = Signal(object, object)  # (x_data, waveform_data)
    error = Signal(str)

    def __init__(self, file: Path, block_size: int = 256) -> None:
        super().__init__()
        self.file = file
        self.block_size = block_size  # samples per block (min/max pair)

    def run(self) -> None:
        try:
            logger.info("Loading waveform (streaming) for: %s", self.file.name)

            # --- 1. Probe audio info ---
            probe_cmd = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "stream=sample_rate,channels",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(self.file),
            ]

            probe = subprocess.run(
                probe_cmd,
                capture_output=True,
                text=True,
                check=True,
                creationflags=get_creation_flags(),
                startupinfo=get_subprocess_startup_info(),
            )

            lines = probe.stdout.strip().split("\n")
            sample_rate = int(lines[0])

            # --- 2. Start ffmpeg PCM stream ---
            ffmpeg_cmd = [
                "ffmpeg",
                "-i",
                str(self.file),
                "-f",
                "f32le",  # float32 PCM
                "-acodec",
                "pcm_f32le",
                "-ac",
                "1",  # mono
                "-ar",
                str(sample_rate),
                "-v",
                "error",
                "pipe:1",
            ]

            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=4096,
                creationflags=get_creation_flags(),
                startupinfo=get_subprocess_startup_info(),
            )

            # --- 3. Streaming min/max extraction ---
            block_bytes = self.block_size * 4  # float32 = 4 bytes
            mins = []
            maxs = []
            positions = []

            sample_index = 0

            while True:
                raw = process.stdout.read(block_bytes)  # pyright: ignore
                if not raw:
                    break

                # Convert to float32 array
                block = np.frombuffer(raw, dtype=np.float32)
                if block.size == 0:
                    break

                # Compute min/max for this block
                mins.append(block.min())
                maxs.append(block.max())

                # Store the sample index for x-axis
                positions.append(sample_index)

                sample_index += block.size

            process.wait()

            if process.returncode != 0:
                stderr = process.stderr.read().decode("utf-8")  # pyright: ignore
                raise RuntimeError(f"FFmpeg error: {stderr}")

            if not mins:
                raise RuntimeError("No audio data decoded")

            # --- 4. Build interleaved envelope arrays ---
            mins = np.array(mins, dtype=np.float32)
            maxs = np.array(maxs, dtype=np.float32)
            positions = np.array(positions, dtype=np.int32)

            # Interleave min/max for PyQtGraph
            waveform = np.empty(mins.size * 2, dtype=np.float32)
            x_data = np.empty(mins.size * 2, dtype=np.int32)

            waveform[0::2] = mins
            waveform[1::2] = maxs

            x_data[0::2] = positions
            x_data[1::2] = positions

            logger.info("Generated %s envelope points", len(waveform))

            self.finished.emit(x_data, waveform)

        except Exception as e:
            logger.error("Waveform error: %s", e)
            logger.debug(traceback.format_exc())
            self.error.emit(str(e))

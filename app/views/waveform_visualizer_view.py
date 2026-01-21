from pathlib import Path
import subprocess
import tracemalloc
import traceback
import pyqtgraph as pg
from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QWidget, QVBoxLayout
import numpy as np

import logging

logger = logging.getLogger(__name__)


class WaveformDataWorker(QObject):
    """Worker for loading and processing audio data using ffmpeg"""

    finished = Signal(object, object)  # (x_data, waveform_data)
    error = Signal(str)

    def __init__(self, file: Path, max_samples: int = 1000000) -> None:
        super().__init__()
        self.file = file
        self.max_samples = max_samples

    def run(self):
        """Load audio file and process waveform data using ffmpeg streaming"""
        # Start memory tracking
        tracemalloc.start()

        try:
            logger.info(f"Starting waveform loading for: {self.file.name}")

            # Use ffprobe to get audio info without loading the file
            probe_cmd = [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "stream=sample_rate,channels,duration",
                "-of",
                "default=noprint_wrappers=1:nokey=1",
                str(self.file),
            ]

            probe_result = subprocess.run(
                probe_cmd, capture_output=True, text=True, check=True
            )

            lines = probe_result.stdout.strip().split("\n")
            sample_rate = int(lines[0])
            channels = int(lines[1])
            duration = float(lines[2])
            total_samples = int(duration * sample_rate)

            logger.info(
                f"Audio info: {total_samples} samples, {sample_rate}Hz, {channels}ch, {duration:.2f}s"
            )
            current, peak = tracemalloc.get_traced_memory()
            logger.debug(
                f"Memory after probe: {current / 1024 / 1024:.2f} MB (peak: {peak / 1024 / 1024:.2f} MB)"
            )

            # Use ffmpeg to decode audio to raw PCM
            ffmpeg_cmd = [
                "ffmpeg",
                "-i",
                str(self.file),
                "-f",
                "s16le",  # 16-bit PCM
                "-acodec",
                "pcm_s16le",
                "-ar",
                str(sample_rate),
                "-ac",
                "1",  # Convert to mono
                "-v",
                "error",
                "pipe:1",
            ]

            logger.debug("Starting ffmpeg process...")
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=10**8,
            )

            # Read all audio data from ffmpeg
            logger.debug("Reading audio data from ffmpeg...")
            raw_data = process.stdout.read()  # pyright: ignore
            process.wait()

            current, peak = tracemalloc.get_traced_memory()
            logger.debug(
                f"Memory after ffmpeg read: {current / 1024 / 1024:.2f} MB (peak: {peak / 1024 / 1024:.2f} MB)"
            )

            # Check for errors
            if process.returncode != 0:
                stderr = process.stderr.read().decode("utf-8")  # pyright: ignore
                raise RuntimeError(f"FFmpeg error: {stderr}")

            # Convert bytes to numpy array efficiently (avoid extra copies)
            logger.debug("Converting to numpy array...")
            # Use np.frombuffer with copy=False to avoid extra allocation
            audio_int16 = np.frombuffer(raw_data, dtype=np.int16)

            # Free raw_data immediately before conversion
            del raw_data

            current, peak = tracemalloc.get_traced_memory()
            logger.debug(
                f"Memory after int16 conversion & del raw_data: {current / 1024 / 1024:.2f} MB (peak: {peak / 1024 / 1024:.2f} MB)"
            )

            # Convert to float32 with explicit output array to control memory
            logger.debug("Converting int16 to float32...")
            audio_data = np.empty(len(audio_int16), dtype=np.float32)
            audio_data[:] = audio_int16  # Copy with type conversion
            audio_data /= 32768.0  # In-place division

            # Free int16 array
            del audio_int16

            current, peak = tracemalloc.get_traced_memory()
            logger.debug(
                f"Memory after float32 conversion & del int16: {current / 1024 / 1024:.2f} MB (peak: {peak / 1024 / 1024:.2f} MB)"
            )

            # Downsample if needed using vectorized operations
            if len(audio_data) > self.max_samples:
                logger.info(
                    f"Downsampling from {len(audio_data)} to ~{self.max_samples} samples"
                )
                chunk_size = len(audio_data) // (self.max_samples // 2)

                # Trim audio to be divisible by chunk_size for reshape
                num_full_chunks = len(audio_data) // chunk_size
                trimmed_length = num_full_chunks * chunk_size
                audio_trimmed = audio_data[:trimmed_length]

                logger.debug(f"Chunk size: {chunk_size}, num_chunks: {num_full_chunks}")
                current, peak = tracemalloc.get_traced_memory()
                logger.debug(
                    f"Memory after trim: {current / 1024 / 1024:.2f} MB (peak: {peak / 1024 / 1024:.2f} MB)"
                )

                # Reshape into chunks: (num_chunks, chunk_size)
                logger.debug("Reshaping into chunks...")
                chunks = audio_trimmed.reshape(num_full_chunks, chunk_size)

                current, peak = tracemalloc.get_traced_memory()
                logger.debug(
                    f"Memory after reshape: {current / 1024 / 1024:.2f} MB (peak: {peak / 1024 / 1024:.2f} MB)"
                )

                # Vectorized min/max operations across all chunks at once
                logger.debug("Computing min/max for all chunks (vectorized)...")
                min_vals = np.min(chunks, axis=1)  # Min of each chunk
                max_vals = np.max(chunks, axis=1)  # Max of each chunk
                min_indices = np.argmin(chunks, axis=1)  # Index of min in each chunk
                max_indices = np.argmax(chunks, axis=1)  # Index of max in each chunk

                current, peak = tracemalloc.get_traced_memory()
                logger.debug(
                    f"Memory after min/max computation: {current / 1024 / 1024:.2f} MB (peak: {peak / 1024 / 1024:.2f} MB)"
                )

                chunk_starts = np.arange(num_full_chunks) * chunk_size
                global_min_pos = chunk_starts + min_indices
                global_max_pos = chunk_starts + max_indices

                # Interleave min/max based on which comes first
                # Create output arrays
                waveform_data = np.empty(num_full_chunks * 2, dtype=np.float32)
                x_data = np.empty(num_full_chunks * 2, dtype=np.int32)

                # Vectorized interleaving: check where min comes before max
                min_first = min_indices < max_indices

                # Use numpy's where to assign values based on condition
                waveform_data[0::2] = np.where(min_first, min_vals, max_vals)
                waveform_data[1::2] = np.where(min_first, max_vals, min_vals)
                x_data[0::2] = np.where(min_first, global_min_pos, global_max_pos)
                x_data[1::2] = np.where(min_first, global_max_pos, global_min_pos)

                logger.debug(f"Downsampling complete: {len(waveform_data)} samples")
                current, peak = tracemalloc.get_traced_memory()
                logger.debug(
                    f"Memory after downsampling: {current / 1024 / 1024:.2f} MB (peak: {peak / 1024 / 1024:.2f} MB)"
                )

                # Free original audio_data
                del audio_data

                current, peak = tracemalloc.get_traced_memory()
                logger.debug(
                    f"Memory after del audio_data: {current / 1024 / 1024:.2f} MB (peak: {peak / 1024 / 1024:.2f} MB)"
                )

            else:
                # No downsampling needed
                logger.info(f"No downsampling needed: {len(audio_data)} samples")
                waveform_data = audio_data
                x_data = np.arange(len(audio_data), dtype=np.int32)

            logger.info(
                f"Final waveform: {len(waveform_data)} samples, x_data: {len(x_data)}"
            )
            current, peak = tracemalloc.get_traced_memory()
            logger.info(
                f"Memory before emit: {current / 1024 / 1024:.2f} MB (peak: {peak / 1024 / 1024:.2f} MB)"
            )

            # Emit the processed data
            self.finished.emit(x_data, waveform_data)

            current, peak = tracemalloc.get_traced_memory()
            logger.info(
                f"Memory after emit: {current / 1024 / 1024:.2f} MB (peak: {peak / 1024 / 1024:.2f} MB)"
            )
            logger.info("Waveform loading completed successfully")

        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg/FFprobe error: {e.stderr}")
            self.error.emit(f"FFmpeg/FFprobe error: {e.stderr}")
        except Exception as e:
            logger.error(f"Error loading waveform: {str(e)}")
            logger.debug(traceback.format_exc())
            self.error.emit(f"Error loading waveform: {str(e)}")
        finally:
            # Stop memory tracking and log final peak
            current, peak = tracemalloc.get_traced_memory()
            logger.info(
                f"FINAL MEMORY STATS - Current: {current / 1024 / 1024:.2f} MB, Peak: {peak / 1024 / 1024:.2f} MB"
            )
            tracemalloc.stop()


class WaveformVisualizer(QWidget):
    """High-performance waveform visualizer using PyQtGraph's built-in optimizations"""

    seek_started = Signal()
    position_moved = Signal(float)
    seek_finished = Signal(float)
    loading_finished = Signal()
    loading_error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.x_data = None
        self.original_length = 0
        self.current_position = 0.0
        self.is_dragging = False

        self.setMinimumHeight(80)
        self.setMaximumHeight(120)

        self._setup_ui()

        self._thread: QThread | None = None
        self._worker: WaveformDataWorker | None = None

    def _setup_ui(self):
        """Initialize PyQtGraph plot widget with built-in optimizations"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create plot widget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground((40, 40, 40))
        self.plot_widget.setMouseTracking(True)

        # Configure axes
        self.plot_widget.showGrid(x=False, y=False)
        self.plot_widget.hideAxis("left")
        self.plot_widget.hideAxis("bottom")
        self.plot_widget.setMenuEnabled(False)
        self.plot_widget.hideButtons()
        self.plot_widget.setContentsMargins(0, 0, 0, 0)

        # Get ViewBox for custom zoom behavior
        self.view_box = self.plot_widget.getViewBox()
        self.view_box.setMouseEnabled(
            x=True, y=False
        )  # Allow horizontal panning/zooming
        self.view_box.setLimits(yMin=-1.2, yMax=1.2)  # Limit Y axis

        # Create single waveform plot
        self.waveform = self.plot_widget.plot(
            pen=pg.mkPen(color=(100, 180, 255), width=1)
        )

        # Enable PyQtGraph's built-in optimizations
        self.waveform.setDownsampling(auto=True)
        self.waveform.setClipToView(True)

        # Create position line
        self.position_line = pg.InfiniteLine(
            pos=0, angle=90, pen=pg.mkPen(color=(255, 100, 100), width=2), movable=False
        )
        self.position_line.setVisible(False)
        self.plot_widget.addItem(self.position_line)

        # Create hover line
        self.hover_line = pg.InfiniteLine(
            pos=0,
            angle=90,
            pen=pg.mkPen(color=(255, 100, 100, 100), width=2),
            movable=False,
        )
        self.hover_line.setVisible(False)
        self.plot_widget.addItem(self.hover_line)

        # Add center line
        self.center_line = pg.InfiniteLine(
            pos=0, angle=0, pen=pg.mkPen(color=(80, 80, 80), width=1), movable=False
        )
        self.plot_widget.addItem(self.center_line)

        layout.addWidget(self.plot_widget)

        # Connect mouse events
        self.plot_widget.scene().sigMouseMoved.connect(self._on_mouse_move)  # type: ignore
        self.plot_widget.scene().sigMouseClicked.connect(self._on_mouse_click)  # type: ignore
        self.plot_widget.viewport().installEventFilter(self)

    def load_waveform_data(self, audio: Path) -> None:
        """Load waveform data in background thread"""
        # Clean up previous thread if exists
        if self._thread is not None and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait()

        # Create new thread and worker
        self._thread = QThread()
        self._worker = WaveformDataWorker(audio)
        self._worker.moveToThread(self._thread)

        # Connect signals
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_waveform_loaded)
        self._worker.error.connect(self._on_loading_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)

        # Start loading
        self._thread.start()

    def reset(self) -> None:
        """Reset the visualizer to empty state"""
        self.x_data = None
        self.original_length = 0
        self.current_position = 0.0
        self.waveform.setData([])
        self.position_line.setPos(0)
        self.position_line.setEnabled(False)

    def set_position(self, position):
        """Set current playback position (0.0 to 1.0)"""
        self.current_position = max(0.0, min(1.0, position))

        if not self.is_dragging and self.original_length > 0:
            # Just update position line - waveform stays stable
            pos_sample = int(self.current_position * self.original_length)
            self.position_line.setPos(pos_sample)

    def _on_waveform_loaded(self, x_data, waveform_data):
        """Callback when waveform data is loaded"""
        self.x_data = x_data
        self.original_length = x_data[-1] if len(x_data) > 0 else len(waveform_data)

        # Set initial view range
        self.view_box.setLimits(xMin=0, xMax=self.original_length)
        self.view_box.setRange(
            xRange=(0, self.original_length), yRange=(-1.1, 1.1), padding=0
        )

        # Update display
        self.position_line.setVisible(True)
        self.waveform.setData(x_data, waveform_data)

        # Emit signal that loading is finished
        self.loading_finished.emit()

    def _on_loading_error(self, error_msg: str):
        """Callback when loading fails"""
        self.loading_error.emit(error_msg)

    def _get_position_from_scene(self, scene_pos):
        """Convert scene position to normalized position (0.0 to 1.0)"""
        if self.original_length == 0:
            return 0.0

        mouse_point = self.view_box.mapSceneToView(scene_pos)
        x = mouse_point.x()

        # x is in original sample coordinates
        position = x / self.original_length if self.original_length > 0 else 0.0
        return max(0.0, min(1.0, position))

    def _on_mouse_move(self, pos):
        """Handle mouse movement for hover and drag"""
        if self.x_data is None:
            return

        position = self._get_position_from_scene(pos)

        if self.is_dragging:
            self.current_position = position
            pos_sample = int(position * self.original_length)
            self.position_line.setPos(pos_sample)
            self.position_moved.emit(position)
        else:
            # Show hover line
            hover_x = position * self.original_length
            self.hover_line.setPos(hover_x)
            self.hover_line.setVisible(True)
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def _on_mouse_click(self, event):
        """Handle mouse clicks for seeking"""
        if self.x_data is None:
            return

        if event.button() == Qt.MouseButton.LeftButton:
            position = self._get_position_from_scene(event.scenePos())

            self.is_dragging = True
            self.current_position = position
            pos_sample = int(position * self.original_length)
            self.position_line.setPos(pos_sample)
            self.seek_started.emit()
            self.position_moved.emit(position)
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))

    def mouseReleaseEvent(self, event):
        """Handle mouse release to finish seeking"""
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.is_dragging = False
            self.seek_finished.emit(self.current_position)
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def leaveEvent(self, event):
        """Hide hover line when mouse leaves"""
        self.hover_line.setVisible(False)
        self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

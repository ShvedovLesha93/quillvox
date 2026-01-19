from pathlib import Path
from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
import librosa

from app.constants import PlaybackState

import logging

logger = logging.getLogger(__name__)


class AudioPlayerViewModel(QObject):
    playback_state_changed = Signal(PlaybackState)
    duration_changed = Signal(int)
    position_changed = Signal(int)
    file_loaded = Signal(str)
    str_speed_changed = Signal(str)
    str_current_time_changed = Signal(str)
    str_total_time_changed = Signal(str)
    int_volume_changed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)
        self._audio_path: Path

        self._state = PlaybackState.STOPPED
        self._was_playing = False
        self.is_muted = False

        # Qt → VM
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.playbackStateChanged.connect(self._on_qt_state_changed)

    def load(self, audio: Path):
        self.player.setSource(QUrl.fromLocalFile(audio))
        self._audio_path = audio
        self.file_loaded.emit(audio.stem)

    def load_waveform_data(self) -> tuple:
        print(f"File: {self._audio_path}")
        audio_data, sr = librosa.load(str(self._audio_path), sr=None, mono=True)
        return audio_data, sr

    def toggle_play(self):
        is_playing = self._state != PlaybackState.PLAYING

        if is_playing:
            self.player.play()
        else:
            self.player.pause()

        logger.info("Playback: %s", "playing" if is_playing else "paused")

    def stop(self):
        self.player.stop()
        self.player.setPosition(0)

        logger.info("Playback: stopped")

    def begin_seek(self):
        self._was_playing = self._state == PlaybackState.PLAYING
        self.player.pause()

        logger.info("Playback: seek started")

    def end_seek(self, pos: int):
        self.player.setPosition(pos)
        if self._was_playing:
            self.player.play()

        logger.info("Playback: seek finished")
        logger.debug("Current position: %s", pos)

    def seek_to(self, pos: int):
        self._on_position_changed(pos)

    def _on_qt_state_changed(self, qt_state):
        if qt_state == QMediaPlayer.PlaybackState.PlayingState:
            self._set_state(PlaybackState.PLAYING)
        elif qt_state == QMediaPlayer.PlaybackState.PausedState:
            self._set_state(PlaybackState.PAUSED)
        else:
            self._set_state(PlaybackState.STOPPED)

    def _set_state(self, state: PlaybackState):
        if self._state == state:
            return

        self._state = state
        self.playback_state_changed.emit(state)

    def set_volume(self, value: int) -> None:
        if value > 0:
            self.is_muted = False
        else:
            self.is_muted = True

        volume = value / 100.0
        self.audio_output.setVolume(volume)
        self.int_volume_changed.emit(value)

    def set_speed(self, value: int) -> None:
        speed = value / 100.0
        self.player.setPlaybackRate(speed)
        self.str_speed_changed.emit(f"{speed:.2f}x")

    def reset_speed(self) -> None:
        self.player.setPlaybackRate(1)

        logger.info("Playback: speed reset")

    def _on_duration_changed(self, duration: int):
        self.duration_changed.emit(duration)
        self.str_total_time_changed.emit(self._format_time(duration))

    def _on_position_changed(self, pos: int):
        self.position_changed.emit(pos)
        self.str_current_time_changed.emit(self._format_time(pos))

    @staticmethod
    def _format_time(ms: int) -> str:
        total_seconds = ms // 1000
        seconds = total_seconds % 60
        minutes = (total_seconds // 60) % 60
        hours = total_seconds // 3600

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

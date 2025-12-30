from pathlib import Path
from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from app.constants import PlaybackState


class PlayerViewModel(QObject):
    playback_state_changed = Signal(PlaybackState)
    duration_changed = Signal(int)
    position_changed = Signal(int)
    str_speed_changed = Signal(str)
    str_current_time_changed = Signal(str)
    str_total_time_changed = Signal(str)
    str_volume_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)

        self._state = PlaybackState.STOPPED
        self._was_playing = False

        # Qt → VM
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.playbackStateChanged.connect(self._on_qt_state_changed)

    def load(self, audio: Path):
        self.player.setSource(QUrl.fromLocalFile(audio))

    def toggle_play(self):
        if self._state == PlaybackState.PLAYING:
            self.player.pause()
        else:
            self.player.play()

    def stop(self):
        self.player.stop()
        self.player.setPosition(0)

    def begin_seek(self):
        self._was_playing = self._state == PlaybackState.PLAYING
        self.player.pause()

    def end_seek(self, pos: int):
        self.player.setPosition(pos)
        if self._was_playing:
            self.player.play()

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
        volume = value / 100.0
        self.audio_output.setVolume(volume)
        self.str_volume_changed.emit(f"{value}%")

    def set_speed(self, value: int) -> None:
        speed = value / 100.0
        self.player.setPlaybackRate(speed)
        self.str_speed_changed.emit(f"{speed:.2f}x")

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

from pathlib import Path
from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

from app.constants import PlaybackState

import logging

from app.utils.time_format import format_time
from app.view_model.waveform_vm import WaveformViewModel

logger = logging.getLogger(__name__)


class AudioPlayerViewModel(QObject):
    playback_state_changed = Signal(PlaybackState)
    duration_changed = Signal(int)
    position_changed = Signal(int)
    hover_position_changed = Signal(int)
    hover_position_left = Signal()
    file_loaded = Signal(str)
    str_speed_changed = Signal(str)
    str_current_time_changed = Signal(str)
    str_total_time_changed = Signal(str)
    int_volume_changed = Signal(int)

    def __init__(self, waveform_vm: WaveformViewModel, parent=None):
        super().__init__(parent)

        self.waveform_vm = waveform_vm

        self.player = QMediaPlayer(self)
        self.audio_output = QAudioOutput(self)
        self.player.setAudioOutput(self.audio_output)

        self._state = PlaybackState.STOPPED
        self._was_playing = False
        self.is_muted = False
        self.is_file_loaded = False

        # Qt → VM
        self.player.durationChanged.connect(self._on_duration_changed)
        self.player.positionChanged.connect(self._on_position_changed)
        self.player.playbackStateChanged.connect(self._on_qt_state_changed)

    def load(self, audio: Path):
        self.player.setSource(QUrl.fromLocalFile(audio))
        self.waveform_vm.load_waveform_file(audio)
        self.file_loaded.emit(audio.name)
        self.is_file_loaded = True

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
        self.set_position(pos)
        if self._was_playing:
            self.player.play()

        logger.info("Playback: seek finished")
        logger.debug("Current position: %s", pos)

    def rewind(self, seconds: int = 5) -> None:
        ms = seconds * 1000
        val = self.player.position()
        rewound = val - ms
        self.player.setPosition(rewound)

    def forward(self, seconds: int = 5) -> None:
        ms = seconds * 1000
        val = self.player.position()
        rewound = val + ms
        self.player.setPosition(rewound)

    def set_position(self, pos: int) -> None:
        self.player.setPosition(pos)

    def seek_to(self, pos: int):
        self._on_position_changed(pos)
        self.hover_position_left.emit()

    def hover_seek_to(self, pos: int) -> None:
        self.hover_position_changed.emit(pos)

    def hover_end_seek(self) -> None:
        self.hover_position_left.emit()

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
        self.str_total_time_changed.emit(format_time(duration))

    def _on_position_changed(self, pos: int):
        self.position_changed.emit(pos)
        self.str_current_time_changed.emit(format_time(pos))

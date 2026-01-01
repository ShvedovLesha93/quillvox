from __future__ import annotations
from typing import TYPE_CHECKING
from app.view_model.audio_player_vm import AudioPlayerVM
from app.view_model.file_selector import FileSelectorVM

if TYPE_CHECKING:
    from app.models.main_model import MainModel


class MainViewModel:
    def __init__(self, main_model: MainModel):
        self.main_model = main_model
        self.audio_player_vm = AudioPlayerVM()
        self.file_selector_vm = FileSelectorVM(
            main_model=self.main_model,
            audio_player_vm=self.audio_player_vm,
        )

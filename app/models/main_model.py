from app.models.transcript import Transcript
from app.models.file_data import SupportedFormats


class MainModel:
    def __init__(self):
        self.file_formats = SupportedFormats()
        self.stt_transcript = Transcript()

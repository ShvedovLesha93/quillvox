from app.models.stt_transcript import STTTranscript
from app.models.file_data import SupportedFormats


class MainModel:
    def __init__(self):
        self.file_formats = SupportedFormats()
        self.stt_transcript = STTTranscript()

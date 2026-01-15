from app.models.stt_transcript import STTTranscript
from app.models.file_data import MediaFile, SupportedFormats


class MainModel:
    def __init__(self):
        self.file_formats = SupportedFormats()
        self.media_file = MediaFile()
        self.stt_transcript = STTTranscript()

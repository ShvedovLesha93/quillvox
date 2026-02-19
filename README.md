# QuillVox

A user-friendly desktop application for transcribing audio files with automatic format conversion. Built with PySide6 and powered by faster-whisper for accurate speech-to-text transcription.

## Features

- 🎯 Accurate audio transcription using faster-whisper
- 📄 Automatic JSON export of transcript data
- 🖥️ Clean and intuitive desktop interface
- ⚡ Fast processing with local inference
- 🔄 Support for multiple audio formats

## Requirements

- Python 3.12+
- PySide6
- faster-whisper

## Installation
```bash
git clone https://github.com/ShvedovLesha93/quillvox.git
cd quillvox
```

## Run

### CPU version
```bash
uv sync
uv run main.py
```

### CUDA version

**Option A: With a dedicated virtual environment (recommended)**
```bash
uv venv .venv-cuda
.venv-cuda\Scripts\activate
uv sync --extra cuda --active
uv run --active main.py
```

**Option B: Switch existing environment to CUDA**
```bash
uv sync --extra cuda
uv run main.py
```
> ⚠️ Switching between CPU and CUDA will reinstall torch each time.

## Usage

1. Launch the application
2. Select your audio file
3. Click transcribe
4. The transcript will be automatically saved as a JSON file

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Built with [PySide6](https://wiki.qt.io/Qt_for_Python)
- Powered by [faster-whisper](https://github.com/guillaumekln/faster-whisper)

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
# Clone the repository
git clone https://github.com/ShvedovLesha93/quillvox.git
cd quillvox

# Install dependencies with uv
uv sync

# Install torch with CUDA
uv pip install torch --index-url https://download.pytorch.org/whl/cu126
```

## Usage

```bash
uv run main.py
```

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

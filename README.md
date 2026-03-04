# QuillVox

A user-friendly desktop application for transcribing audio files with automatic format conversion.
Built with PySide6 and powered by faster-whisper for accurate speech-to-text transcription.

## Features

- 🎯 Accurate audio transcription using faster-whisper
- 📄 Automatic JSON export of transcript data
- 🖥️ Clean and intuitive desktop interface
- ⚡ Fast processing with local inference
- 🔄 Support for multiple audio formats

## Usage

1. Launch the application
2. Select your audio file
3. Click transcribe
4. The transcript will be automatically saved as a JSON file

## For Developers

See [Development Tools](dev_tools/DEVELOPMENT.md) for:

- Translation management workflow
- Icon management and compilation
- Development scripts usage

### Requirements

See [pyproject.toml](pyproject.toml) for the full dependency list.

### Installation

```bash
git clone https://github.com/ShvedovLesha93/quillvox.git
cd quillvox
```

### Run

#### CPU version

```bash
uv sync
uv run main.py
```

#### CUDA version

Option A: Switch existing environment to CUDA

```bash
uv sync --extra cuda
uv run main.py
```

> ⚠️ Switching between CPU and CUDA will reinstall torch each time.

Option B: With a dedicated virtual environment

On Windows:

```bash
uv venv .venv-cuda
.venv-cuda\Scripts\activate
uv sync --extra cuda --active
uv run --active main.py
```

On Linux/macOS:

```bash
uv venv .venv-cuda
source .venv-cuda/bin/activate
uv sync --extra cuda --active
uv run --active main.py
```

#### Args

These arguments are supported by both the `launcher.py` and the `app.py` itself.
When using the launcher binary, all arguments are forwarded to the app transparently.

| Argument            | Description                                                 |
| ------------------- | ------------------------------------------------------------|
| `--debug-logging`   | Enable debug logging (sets log level to DEBUG)              |
| `--no-crash-dialog` | Disable crash dialog on fatal error                         |
| `--audio`           | Path to the audio file                                      |
| `--dev-restart`     | Enable the hard reset application using the Ctrl-R shortcut |

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Built with [PySide6](https://wiki.qt.io/Qt_for_Python)
- Powered by [faster-whisper](https://github.com/guillaumekln/faster-whisper)

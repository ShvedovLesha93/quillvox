# QuillVox

A user-friendly desktop application for transcribing audio files with automatic format conversion.
Built with PySide6 and powered by faster-whisper for accurate speech-to-text transcription.

https://github.com/user-attachments/assets/28d7c3d5-5f2f-4d0f-a0ba-cd59ed6a6ca3

## Features

- 🎯 Accurate audio transcription using faster-whisper
- 📄 Automatic JSON export of transcript data
- 🖥️ Clean and intuitive desktop interface
- ⚡ Fast processing with local inference
- 🔄 Support for multiple audio formats
- ✏️ Edit transcripts and adjust timestamps manually

## Requirements

- `ffmpeg` and `ffprobe` must be installed on your system
  - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
  - **Linux**: Install via package manager (`sudo apt install ffmpeg` on Ubuntu/Debian)

## Installation

> ℹ️ Note: The program is currently available as a portable version;
> an installer will be released in the future.

1. Download the latest archive from the [Releases](https://github.com/ShvedovLesha93/quillvox/releases) page
2. Extract the archive to your preferred location
3. Run `QuillVox.exe` (Windows) or `QuillVox` (Linux)

## Usage

1. Launch the application
2. Select your audio file
3. Click "Transcribe"
4. The transcript will be automatically saved as a JSON file
5. Edit the transcript or adjust timestamps manually if needed

> ℹ️ Note: Downloaded models are stored in the `.models` folder next to `QuillVox.exe`.

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

On Linux:

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

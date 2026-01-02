from pathlib import Path
import sys
import time
import subprocess
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import argparse


class EventHandler(FileSystemEventHandler):
    def __init__(self) -> None:
        super().__init__()
        self.last_restart = 0
        self.debounce_seconds = 1.0

    def on_modified(self, event) -> None:
        if event.is_directory:
            return

        path = Path(event.src_path)  # pyright: ignore

        # Filter temporary files
        if path.name.startswith(".") or path.name.startswith("~"):
            return

        if path.suffix != ".py":
            return

        if "__pycache__" in path.parts:
            return

        # Debounce restarting
        now = time.time()
        if now - self.last_restart < self.debounce_seconds:
            return

        print("[Watcher] File changed → restarting script...")

        if hasattr(self, "process"):
            self.process.terminate()
            self.process.wait()

        self.process = subprocess.Popen(self.command)

    def run(self, module: str) -> None:
        self.command = [
            sys.executable,
            "-m",
            module,
        ]
        self.process = subprocess.Popen(self.command)


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.resolve()
    sys.path.append(str(project_root))

    parser = argparse.ArgumentParser(
        description="Auto reload Python module on file changes"
    )

    parser.add_argument("module", help="Python module to run (example: app.main)")

    args = parser.parse_args()

    event_handler = EventHandler()
    event_handler.run(args.module)

    observer = Observer()
    observer.schedule(event_handler, "app", recursive=True)
    observer.start()
    print("\n[Watcher] To stop the program, press Control-C")
    print("----------------------------------------------\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Watcher] Stopping watcher...")

    finally:
        observer.stop()
        observer.join()
        event_handler.process.terminate()
        event_handler.process.wait()
        print("[Watcher] The program closed.")

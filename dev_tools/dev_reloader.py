from pathlib import Path
import sys
import time
import subprocess
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
import argparse


class EventHandler(FileSystemEventHandler):

    def on_modified(self, event) -> None:
        if not event.is_directory and event.src_path.endswith(".py"):  # pyright: ignore
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
    observer.schedule(event_handler, ".", recursive=True)
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

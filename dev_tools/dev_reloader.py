from pathlib import Path
import sys
import time
import subprocess
import argparse


def run(module: str) -> subprocess.Popen:
    return subprocess.Popen([sys.executable, "-m", module])


def wait_for_exit(process: subprocess.Popen) -> None:
    while process.poll() is None:
        time.sleep(0.5)


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.resolve()
    sys.path.append(str(project_root))

    parser = argparse.ArgumentParser(description="Run Python module, restart on Ctrl-C")
    parser.add_argument("module", help="Python module to run (example: app.main)")
    args = parser.parse_args()

    process = run(args.module)

    print("\n[Runner] To restart, press Ctrl-C once. To stop, press Ctrl-C twice.")
    print("-------------------------------------------------------------------------\n")

    last_interrupt = 0.0

    while True:
        try:
            time.sleep(0.5)

            # Exit if the module crashed or exited on its own
            if process.poll() is not None:
                exit_code = process.returncode
                if exit_code != 0:
                    print(
                        f"\n[Runner] Process exited with error code {exit_code}. Stopping."
                    )
                    sys.exit(exit_code)
                else:
                    print("\n[Runner] Process exited cleanly. Stopping.")
                    sys.exit(0)

        except KeyboardInterrupt:
            now = time.time()
            if now - last_interrupt < 2.0:
                print("\n[Runner] Stopping...")
                process.terminate()
                process.wait()
                print("[Runner] The program closed.")
                sys.exit(0)

            last_interrupt = now
            print("\n[Runner] Restarting...")
            process.terminate()
            process.wait()
            process = run(args.module)
            print("[Runner] Restarted. Press Ctrl-C twice to stop.\n")

import subprocess
import sys


def compile_resources():
    try:
        # Compile .qrc to Python module
        subprocess.run(
            [
                "pyside6-rcc",
                "app/resources/resources.qrc",
                "-o",
                "app/resources/resources_rc.py",
            ],
            check=True,
        )
        print("Resources compiled successfully!")
    except subprocess.CalledProcessError:
        print("Error compiling resources")
        sys.exit(1)


if __name__ == "__main__":
    compile_resources()

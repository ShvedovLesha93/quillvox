import subprocess
import sys
from pathlib import Path


def compile_resources():
    """Compile Qt resources from .qrc to Python module."""
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    qrc_file = project_root / "app" / "resources" / "resources.qrc"
    output_file = project_root / "app" / "resources" / "resources_rc.py"

    print("=" * 60)
    print("Qt Resources Compiler")
    print("=" * 60)
    print(f"Input:  {qrc_file}")
    print(f"Output: {output_file}")
    print()

    if not qrc_file.exists():
        print(f"Error: QRC file not found: {qrc_file}")
        sys.exit(1)

    try:
        # Compile .qrc to Python module
        result = subprocess.run(
            [
                "pyside6-rcc",
                str(qrc_file),
                "-o",
                str(output_file),
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        print("✓ Resources compiled successfully!")

        # Show file size
        if output_file.exists():
            size_kb = output_file.stat().st_size / 1024
            print(f"✓ Generated file size: {size_kb:.2f} KB")

        if result.stdout:
            print(f"\nOutput:\n{result.stdout}")

    except FileNotFoundError:
        print("Error: pyside6-rcc not found!")
        print("Make sure PySide6 is installed: pip install PySide6")
        sys.exit(1)

    except subprocess.CalledProcessError as e:
        print("Error compiling resources!")
        if e.stderr:
            print(f"\nError details:\n{e.stderr}")
        sys.exit(1)


if __name__ == "__main__":
    compile_resources()

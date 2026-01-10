if __name__ == "__main__":
    import re
    from pathlib import Path

    def get_icon_files(icons_dir: Path) -> list[str]:
        """Get all .svg filenames (without extension) from icons directory."""
        if not icons_dir.exists():
            raise FileNotFoundError(f"Icons directory not found: {icons_dir}")

        icon_files = sorted(icons_dir.glob("*.svg"))
        return [icon.stem for icon in icon_files]

    def generate_enum_members(icon_names: list[str]) -> str:
        """Generate enum member definitions from icon names."""
        members = []
        for name in icon_names:
            enum_name = name.upper()
            members.append(f'    {enum_name} = "{name}"')

        return "\n".join(members)

    def generate_qrc_file_entries(icon_names: list[str]) -> str:
        """Generate <file> entries for .qrc file."""
        entries = []
        for name in icon_names:
            entries.append(f"        <file>icons/{name}.svg</file>")

        return "\n".join(entries)

    def update_icon_enum(file_path: Path, new_members: str) -> bool:
        """Update the IconName enum in the file with new members."""
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            return False

        content = file_path.read_text(encoding="utf-8")

        pattern = r'(class IconName\(str, Enum\):)\s*\n(?:    [A-Z_]+ = "[^"]+"\s*\n)+'

        if not re.search(pattern, content):
            print(f"Error: IconName enum not found in {file_path}")
            return False

        new_enum = f"\\1\n{new_members}\n"
        new_content = re.sub(pattern, new_enum, content)

        if content == new_content:
            print("✓ No changes needed - IconName enum is up to date.")
            return False

        file_path.write_text(new_content, encoding="utf-8")
        return True

    def update_qrc_file(qrc_path: Path, icon_names: list[str]) -> bool:
        """Update the resources.qrc file with new icon entries."""
        if not qrc_path.exists():
            print(f"Warning: QRC file not found: {qrc_path}")
            print("Creating new resources.qrc file...")
            create_new_qrc_file(qrc_path, icon_names)
            return True

        content = qrc_path.read_text(encoding="utf-8")

        pattern = r'(<qresource prefix="/icons">)\s*\n((?:\s*<file>.*?</file>\s*\n)*)\s*(</qresource>)'

        if not re.search(pattern, content):
            print(f'Error: Could not find <qresource prefix="/icons"> in {qrc_path}')
            return False

        new_entries = generate_qrc_file_entries(icon_names)

        new_content = re.sub(pattern, f"\\1\n{new_entries}\n    \\3", content)

        if content == new_content:
            print("✓ No changes needed - resources.qrc is up to date.")
            return False

        qrc_path.write_text(new_content, encoding="utf-8")
        return True

    def create_new_qrc_file(qrc_path: Path, icon_names: list[str]) -> None:
        """Create a new resources.qrc file from scratch."""
        entries = generate_qrc_file_entries(icon_names)

        qrc_content = f"""<!DOCTYPE RCC>
<RCC version="1.0">
    <qresource prefix="/icons">
{entries}
    </qresource>
</RCC>
"""

        qrc_path.parent.mkdir(parents=True, exist_ok=True)
        qrc_path.write_text(qrc_content, encoding="utf-8")
        print("✓ Created new resources.qrc file")

    # Main execution
    print("=" * 60)
    print("IconName Enum & QRC Auto-Updater")
    print("=" * 60)

    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    icons_dir = project_root / "app" / "resources" / "icons"
    qrc_path = project_root / "app" / "resources" / "resources.qrc"

    print(f"Scanning icons directory: {icons_dir}")

    try:
        icon_names = get_icon_files(icons_dir)

        if not icon_names:
            print("Warning: No .svg files found!")
            exit(1)

        print(f"Found {len(icon_names)} icons:")
        for name in icon_names:
            print(f"  - {name}")

        new_members = generate_enum_members(icon_names)

        print("\nGenerated enum members:")
        print(new_members)

        # Update IconName enum
        import app.views.ui_utils.icons as icons

        icons_module = Path(icons.__file__)

        print(f"\nUpdating {icons_module.name}...")
        enum_updated = update_icon_enum(icons_module, new_members)
        if enum_updated:
            print("✓ Successfully updated IconName enum!")

        # Update resources.qrc
        print("\nUpdating resources.qrc...")
        qrc_updated = update_qrc_file(qrc_path, icon_names)
        if qrc_updated:
            print("✓ Successfully updated resources.qrc!")
            print("\n⚠️  Don't forget to recompile resources:")
            print("  pyside6-rcc app/resources/resources.qrc -o app/resources_rc.py")

        if not enum_updated and not qrc_updated:
            print("\n✓ Everything is already up to date!")

    except Exception as e:
        print(f"Error: {e}")
        exit(1)

if __name__ == "__main__":
    import re
    from pathlib import Path

    def get_icon_files(icons_dir: Path) -> tuple[set[str], set[str]]:
        """Get all unique theme folders and icon names from icons directory.

        Returns:
            tuple of (theme_names, icon_names)
            Example: ({'dark_theme', 'light_theme'}, {'pause', 'play_arrow', 'stop'})
        """
        if not icons_dir.exists():
            raise FileNotFoundError(f"Icons directory not found: {icons_dir}")

        themes = set()
        icons = set()

        # Scan all subdirectories (themes)
        for theme_dir in sorted(icons_dir.iterdir()):
            if theme_dir.is_dir():
                themes.add(theme_dir.name)

                # Get all .svg files in this theme
                for svg_file in theme_dir.glob("*.svg"):
                    icons.add(svg_file.stem)

        return themes, icons

    def generate_theme_enum(theme_names: set[str]) -> str:
        """Generate Theme enum members."""
        members = []
        for name in sorted(theme_names):
            enum_name = name.upper()
            members.append(f'    {enum_name[:-6]} = "{name}"')

        return "\n".join(members)

    def generate_icon_enum(icon_names: set[str]) -> str:
        """Generate IconName enum members."""
        members = []
        for name in sorted(icon_names):
            enum_name = name.upper()
            members.append(f'    {enum_name} = "{name}"')

        return "\n".join(members)

    def generate_qrc_file_entries(icons_dir: Path) -> str:
        """Generate <file> entries for .qrc file with nested structure."""
        entries = []

        # Scan all theme directories
        for theme_dir in sorted(icons_dir.iterdir()):
            if theme_dir.is_dir():
                theme_name = theme_dir.name

                # Add all .svg files from this theme
                for svg_file in sorted(theme_dir.glob("*.svg")):
                    entries.append(
                        f"        <file>icons/{theme_name}/{svg_file.name}</file>"
                    )

        return "\n".join(entries)

    def update_theme_enum(file_path: Path, new_members: str) -> bool:
        """Update the Theme enum in the file with new members."""
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            return False

        content = file_path.read_text(encoding="utf-8")

        pattern = r'(class Theme\(str, Enum\):)\s*\n(?:    [A-Z_]+ = "[^"]+"\s*\n)+'

        if not re.search(pattern, content):
            print(f"Error: Theme enum not found in {file_path}")
            return False

        new_enum = f"\\1\n{new_members}\n"
        new_content = re.sub(pattern, new_enum, content)

        if content == new_content:
            print("✓ No changes needed - Theme enum is up to date.")
            return False

        file_path.write_text(new_content, encoding="utf-8")
        return True

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

    def update_qrc_file(qrc_path: Path, icons_dir: Path) -> bool:
        """Update the resources.qrc file with new icon entries."""
        if not qrc_path.exists():
            print(f"Warning: QRC file not found: {qrc_path}")
            print("Creating new resources.qrc file...")
            create_new_qrc_file(qrc_path, icons_dir)
            return True

        content = qrc_path.read_text(encoding="utf-8")

        pattern = r'(<qresource prefix="/icons">)\s*\n((?:\s*<file>.*?</file>\s*\n)*)\s*(</qresource>)'

        if not re.search(pattern, content):
            print(f'Error: Could not find <qresource prefix="/icons"> in {qrc_path}')
            return False

        new_entries = generate_qrc_file_entries(icons_dir)

        new_content = re.sub(pattern, f"\\1\n{new_entries}\n    \\3", content)

        if content == new_content:
            print("✓ No changes needed - resources.qrc is up to date.")
            return False

        qrc_path.write_text(new_content, encoding="utf-8")
        return True

    def create_new_qrc_file(qrc_path: Path, icons_dir: Path) -> None:
        """Create a new resources.qrc file from scratch."""
        entries = generate_qrc_file_entries(icons_dir)

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
    print("Theme & IconName Enum Auto-Updater")
    print("=" * 60)

    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    icons_dir = project_root / "app" / "resources" / "icons"
    qrc_path = project_root / "app" / "resources" / "resources.qrc"

    print(f"Scanning icons directory: {icons_dir}")

    try:
        themes, icons = get_icon_files(icons_dir)

        if not themes:
            print("Warning: No theme directories found!")
            exit(1)

        if not icons:
            print("Warning: No .svg files found!")
            exit(1)

        print(f"\nFound {len(themes)} themes:")
        for theme in sorted(themes):
            print(f"  - {theme}")

        print(f"\nFound {len(icons)} unique icons:")
        for icon in sorted(icons):
            print(f"  - {icon}")

        # Generate enum members
        theme_members = generate_theme_enum(themes)
        icon_members = generate_icon_enum(icons)

        print("\n" + "=" * 60)
        print("Generated Theme enum:")
        print("=" * 60)
        print(theme_members)

        print("\n" + "=" * 60)
        print("Generated IconName enum:")
        print("=" * 60)
        print(icon_members)

        # Update enums
        import app.views.ui_utils.icons as icons_module

        icons_file = Path(icons_module.__file__)

        print(f"\nUpdating {icons_file.name}...")

        theme_updated = update_theme_enum(icons_file, theme_members)
        if theme_updated:
            print("✓ Successfully updated Theme enum!")

        icon_updated = update_icon_enum(icons_file, icon_members)
        if icon_updated:
            print("✓ Successfully updated IconName enum!")

        # Update resources.qrc
        print("\nUpdating resources.qrc...")
        qrc_updated = update_qrc_file(qrc_path, icons_dir)
        if qrc_updated:
            print("✓ Successfully updated resources.qrc!")
            print("\n⚠️  Don't forget to recompile resources:")
            print("  pyside6-rcc app/resources/resources.qrc -o app/resources_rc.py")

        if not theme_updated and not icon_updated and not qrc_updated:
            print("\n✓ Everything is already up to date!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
        exit(1)

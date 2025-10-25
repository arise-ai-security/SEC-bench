"""
Script: Remove files/directories in artifact/input/ that are not listed in artifact/repos.json

For each item in artifact/repos.json, extract the substring after the last period (.).
Then, delete any files/directories in artifact/input/ whose name (excluding extension)
does not match any of those extracted names.
"""

import json
import os
import shutil
from pathlib import Path


def extract_last_segment(item: str) -> str:
    """
    Extract the substring after the last period (.)

    Example:
        "secb.x86_64.openjpeg.cve-2024-56827" -> "CVE-2024-56827"
    """
    return item.split('.')[-1].upper()


def get_name_without_extension(path: Path) -> str:
    """
    Return the filename or directory name without its extension

    Example:
        "cve-2024-56827.json" -> "cve-2024-56827"
    """
    if path.is_file():
        return path.stem
    return path.name


def main():
    # Paths
    repos_json_path = Path("artifact/repos.json")
    input_dir = Path("artifact/input")

    # Validate paths
    if not repos_json_path.exists():
        print(f"Error: {repos_json_path} does not exist.")
        return

    if not input_dir.exists():
        print(f"Error: {input_dir} does not exist.")
        return

    # Read repos.json
    print(f"📖 Reading {repos_json_path} ...")
    with open(repos_json_path, 'r') as f:
        repos_data = json.load(f)

    # Extract last segment after '.'
    valid_names = set()
    for item in repos_data:
        last_segment = extract_last_segment(item)
        valid_names.add(last_segment)

    print(f"✅ Extracted {len(valid_names)} unique names from {len(repos_data)} entries.")
    print(f"   Example: {list(valid_names)[:5]}")

    # List files/directories under artifact/input
    items_in_input = [item for item in input_dir.iterdir() if item.name != '.DS_Store']
    print(f"\n📁 Found {len(items_in_input)} items in {input_dir}")

    # Find items to remove
    to_remove = []
    for item in items_in_input:
        name_without_ext = get_name_without_extension(item)
        if name_without_ext not in valid_names:
            to_remove.append(item)

    if not to_remove:
        print("\n✨ No items to remove. All files/directories are valid.")
        return

    # Show removal preview
    print(f"\n  The following {len(to_remove)} items will be removed:")
    for item in to_remove[:20]:  # show only first 20
        item_type = "directory" if item.is_dir() else "file"
        print(f"   - {item.name} ({item_type})")

    if len(to_remove) > 20:
        print(f"   ... and {len(to_remove) - 20} more")

    response = input("\nProceed with deletion? (y/N): ")
    if response.lower() != 'y':
        print("❌ Cancelled.")
        return

    # Execute removal
    print("\n  Removing...")
    removed_count = 0
    failed_count = 0

    for item in to_remove:
        try:
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
            removed_count += 1
            if removed_count <= 10 or removed_count % 100 == 0:
                print(f"   ✓ Removed: {item.name}")
        except Exception as e:
            print(f"   ✗ Failed to remove {item.name}: {e}")
            failed_count += 1

    print(f"\n✅ Done! Removed {removed_count} items.")
    if failed_count > 0:
        print(f"⚠️  {failed_count} items failed to remove.")


if __name__ == "__main__":
    main()

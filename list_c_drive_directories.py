#!/usr/bin/env python3
"""
List all directories on C: drive
Lists directories recursively with optional size information
"""

import os
import sys
from pathlib import Path


def get_directory_size(path):
    """Calculate total size of directory in bytes"""
    total = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                try:
                    total += os.path.getsize(filepath)
                except (OSError, IOError):
                    pass
    except (PermissionError, OSError):
        return None
    return total


def format_size(bytes_size):
    """Format bytes to human readable format"""
    if bytes_size is None:
        return "N/A"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


def list_directories(root_path, show_size=False, max_depth=None, current_depth=0, indent=0):
    """
    Recursively list all directories
    
    Args:
        root_path: Root directory to start from
        show_size: Show directory sizes
        max_depth: Maximum recursion depth (None = unlimited)
        current_depth: Current recursion depth
        indent: Indentation level for display
    """
    try:
        entries = os.listdir(root_path)
    except (PermissionError, OSError) as e:
        print(f"{'  ' * indent}[Access Denied] {root_path}")
        return

    # Filter only directories
    dirs = []
    for entry in entries:
        full_path = os.path.join(root_path, entry)
        if os.path.isdir(full_path):
            dirs.append((entry, full_path))

    # Sort directories alphabetically
    dirs.sort(key=lambda x: x[0].lower())

    # Print directories
    for dir_name, dir_path in dirs:
        if show_size:
            size = get_directory_size(dir_path)
            size_str = f" ({format_size(size)})"
        else:
            size_str = ""

        print(f"{'  ' * indent}📁 {dir_name}{size_str}")

        # Recurse if within depth limit
        if max_depth is None or current_depth < max_depth:
            list_directories(dir_path, show_size, max_depth, current_depth + 1, indent + 1)


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(
        description='List all directories on C: drive'
    )
    parser.add_argument(
        '-s', '--size',
        action='store_true',
        help='Show directory sizes'
    )
    parser.add_argument(
        '-d', '--depth',
        type=int,
        default=None,
        help='Maximum recursion depth (default: unlimited)'
    )
    parser.add_argument(
        '-p', '--path',
        default='C:\\',
        help='Starting path (default: C:\\)'
    )

    args = parser.parse_args()

    # Verify path exists
    if not os.path.exists(args.path):
        print(f"Error: Path '{args.path}' does not exist")
        sys.exit(1)

    print(f"📋 Listing directories from: {args.path}")
    print(f"{'=' * 80}")

    try:
        list_directories(args.path, show_size=args.size, max_depth=args.depth)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(0)

    print(f"{'=' * 80}")
    print("Done!")


if __name__ == '__main__':
    main()

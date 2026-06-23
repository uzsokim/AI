import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

root = "C:\\"

for entry in sorted(os.scandir(root), key=lambda e: e.name):
    if entry.is_dir(follow_symlinks=False):
        print(entry.path)
        try:
            for sub in sorted(os.scandir(entry.path), key=lambda e: e.name):
                if sub.is_dir(follow_symlinks=False):
                    print(f"  {sub.path}")
        except PermissionError:
            pass

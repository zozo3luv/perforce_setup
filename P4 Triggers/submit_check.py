#!/usr/bin/env python3
import sys
import subprocess
import os

os.environ["P4PORT"] = "ssl:localhost:1666"
os.environ["P4USER"] = "username"
os.environ["P4PASSWD"] = "passwd"
os.environ["P4CHARSET"] = "utf8"

def get_files_in_changelist(cl):
    """Return all paths of changelist items."""
    cmd = ["p4", "opened", "-c", cl]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("Error getting file list from changelist:", result.stderr)
        sys.exit(1)
    
    files = []
    for line in result.stdout.splitlines():
        if line.startswith("//"):
            path = line.split("#")[0].strip()
            files.append(path)
    return files

def main():
    if len(sys.argv) != 2:
        print("Usage: check_prefix.py <changelist>")
        sys.exit(1)

    changelist = sys.argv[1]
    files = get_files_in_changelist(changelist)

    bad_files = []
    for f in files:
        if f.lower().endswith(".mat") or f.lower().endswith(".mat.meta"):
            filename = os.path.basename(f)
            if not filename.startswith("Mat_"):
                bad_files.append(filename)

    if bad_files:
        print("The following '.mat' files SHOULD BE NAMED AS 'Mat_', failed to submit: \n")
        for f in bad_files:
            suggested = "Mat_" + f if not f.startswith("Mat_") else f
            print(f"  - {f}  →  Should be named as：{suggested}")
        print("\nPlease RENAME the files before submitting again.")
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
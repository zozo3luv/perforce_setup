#!/usr/bin/env python3
import sys
import os
import subprocess

# =======================
# JSON Config 
# FILE TYPES -> Prefix
PREFIX_RULES = {
    # Unity Types
    ".mat": "Mat_",
    ".mat.meta": "Mat_",

    ".shader": "Sh_",
    ".shader.meta": "Sh_",

    # Picture Types
    ".png": "Tex_",
    ".png.meta": "Tex_",

    ".psd": "Ps_",
    ".psd.meta": "Ps_",
    
    # 3D Model Types
    ".fbx": "Fbx_",
    ".fbx.meta": "Fbx_"

    ".obj"
}
# =======================

def get_files_in_changelist(cl):
    """返回 changelist 中的所有文件路径"""
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
        filename = os.path.basename(f)
        for ext, prefix in PREFIX_RULES.items():
            if filename.lower().endswith(ext):
                if not filename.startswith(prefix):
                    bad_files.append((filename, prefix))
                break

    if bad_files:
        print("❌ 以下文件命名不符合规则，提交被拒绝：\n")
        for f, prefix in bad_files:
            suggested = prefix + f if not f.startswith(prefix) else f
            print(f"  - {f}  →  建议改为：{suggested}")
        print("\n请在提交前重命名这些文件。")
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
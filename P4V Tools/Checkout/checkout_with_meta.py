# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import re

def has_jp_cn(path: str) -> bool:
    """Check if the path contains Japanese or Chinese characters"""
    return bool(re.search(r'[\u3040-\u30ff\u31f0-\u31ff\u4e00-\u9fff]', path))

def checkout_file(path: str):
    """Execute p4 edit on the given path and its .meta file if exists."""
    if not os.path.exists(path):
        return

    # Check if the path contains Chinese or Japanese characters
    _has_jp_cn = has_jp_cn(path)

    # Execute p4 edit (with -Q cp936 if the path contains Chinese characters)
    cmd = ["p4"]
    if _has_jp_cn:
        cmd += ["-Q", "cp936"]
    cmd += ["edit", path]

    subprocess.run(cmd, shell=False)

    # 如果是文件夹（以 \... 结尾）
    if path.endswith("\\..."):
        path = path[:-4]

    # 检查是否存在对应的 .meta 文件
    meta_path = path + ".meta"
    if os.path.exists(meta_path):
        cmd = ["p4"]
        if _has_jp_cn:
            cmd += ["-Q", "cp936"]
        cmd += ["edit", meta_path]
        subprocess.run(cmd, shell=False)


def main():
    args = sys.argv[1:]
    if not args:
        print("No arguments received from P4V.")
        return

    for arg in args:
        checkout_file(arg)

    print("Done.")

if __name__ == "__main__":
    main()
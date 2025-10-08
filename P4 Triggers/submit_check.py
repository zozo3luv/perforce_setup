#!/usr/bin/env python3
import os
import subprocess
import re
import json
import sys

# File suffix rules, such as _v01, _v02
VERSION_PATTERN   = re.compile(r'_v\d{2}$')
VERSION_PATTERN_1 = re.compile(r'_v\d{1}$')

# Exclude patterns (case-sensitive)
EXCLUDE_PATTERN    = re.compile(r'EXTN_')
EXCLUDE_PATTERN_1  = re.compile(r'_EXTN')

class FileNameChecker:
    def __init__(self, prefix_rules_path):
        """Init checker, read JSON config"""
        self.prefix_rules = self.load_rules(prefix_rules_path)

    @staticmethod
    def load_rules(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def get_files_in_changelist(cl):
        """Get all file paths and actions in the changelist (robust & fast)."""
        cmd = ['p4', '-ztag', 'describe', '-s', str(cl)]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        if result.returncode != 0:
            print("Error getting file list from changelist:", result.stderr)
            sys.exit(1)

        out = result.stdout

        pattern = re.compile(r'^\s*\.{3}\s+(depotFile\d+|action\d+)\s(.+)$', re.MULTILINE)
        files = []
        current_depot = None
        for m in pattern.finditer(out):
            typ, val = m.group(1), m.group(2).strip()
            if typ.startswith('depotFile'):
                current_depot = val.split('#', 1)[0]
            elif typ.startswith('action'):
                if current_depot is not None:
                    files.append({'path': current_depot, 'action': val})
                    current_depot = None
        return files

    def check_files(self, files):
        """Check prefix and suffix"""
        bad_files = []

        for f in files:

            if f['action'] == "delete" or f['action'] == "move/delete" or f['action'] == "purge":
                continue

            # Skip files that match exclude patterns in the filename
            if EXCLUDE_PATTERN.search(f['path']) or EXCLUDE_PATTERN_1.search(f['path']):
                continue

            filename_full = os.path.basename(f['path'])
            filename = filename_full[:-5] if filename_full.lower().endswith('.meta') else filename_full

            # Check for matched rule
            prefix_rule = None
            file_type = None

            for ext, prefix in self.prefix_rules.items():
                if filename.lower().endswith(ext):
                    prefix_rule = prefix
                    file_type = ext
                    break

            if not prefix_rule:
                continue

            # Check prefix
            good_prefix = True
            if not filename.startswith(prefix_rule):
                good_prefix = False

            # Check suffix: VERSION_PATTERN
            no_ext_name = filename[:-len(file_type)]
            good_suffix = True
            if not VERSION_PATTERN.search(no_ext_name) and not VERSION_PATTERN_1.search(no_ext_name):
                good_suffix = False

            if not good_prefix and not good_suffix:
                bad_files.append((filename_full, file_type, prefix_rule, "presuf"))
            elif not good_prefix:
                bad_files.append((filename_full, file_type, prefix_rule, "prefix"))
            elif not good_suffix:
                bad_files.append((filename_full, file_type, prefix_rule, "suffix"))

        return bad_files

    @staticmethod
    def report_and_exit(bad_files):
        """REPORT"""
        if not bad_files:
            sys.exit(0)

        print("Please rename the following files：\n")
        
        for f, file_type, prefix_rule, err_type in bad_files:
            if (f.lower().endswith('.meta')):
                name_only = f[:-5]

            name_only = f[:-len(file_type)]

            if err_type == "prefix":
                suggested = prefix_rule + f
                print(f"  - {f}  → Missing prefix: '{prefix_rule}'  |  Suggested: {suggested}")
                print(f"  - {f}  → 缺少前缀: '{prefix_rule}'  |  请改为: {suggested}")

            elif err_type == "suffix":
                suggested = f"{name_only}_v01{file_type}"
                print(f"  - {f}  → Missing version suffix like '_v01'  |  Suggested: {suggested}")
                print(f"  - {f}  → 缺少版本后缀，如 '_v01'  |  推荐改为: {suggested}")

            elif err_type == "presuf":
                suggested = f"{prefix_rule}{name_only}_v01{file_type}"
                print(f"  - {f}  → Missing both prefix '{prefix_rule}' and version suffix like '_v01'  |  Suggested: {suggested}")
                print(f"  - {f}  → 同时缺少前缀： '{prefix_rule}'，以及版本后缀，如 '_v01'  |  推荐改为: {suggested}")

        print("\nPlease rename the files before submitting again.")
        print("\nIf you have external imported resources, please add the EXTN_ prefix in the root folder of the resources.")
        print("\n请务必在 P4V软件内 重命名文件后再提交")
        print("\n若有外部导入资源，请在资源的根文件夹中添加 EXTN_ 前缀")
        sys.exit(1)
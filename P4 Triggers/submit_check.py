#!/usr/bin/env python3
import os
import subprocess
import re
import json
import sys

# File suffix rules, such as _v01, _v02
VERSION_PATTERN   = re.compile(r'_v\d{2}$')
VERSION_PATTERN_1 = re.compile(r'_v\d{1}$')

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
        """get all file paths in the changelist"""
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

    def check_files(self, files):
        """Check prefix and suffix"""
        bad_files = []

        for f in files:
            filename = os.path.basename(f)

            # Check for matched rule
            prefix_rule = None
            file_type = None
            for rule_ext, prefix in self.prefix_rules.items():
                if filename.lower().endswith(rule_ext):
                    prefix_rule = prefix
                    file_type = rule_ext
                    break

            if not prefix_rule:
                continue

            # Check prefix
            good_prefix = True
            if not filename.startswith(prefix_rule):
                good_prefix = False

            # Check suffix: VERSION_PATTERN
            good_suffix = True
            if not VERSION_PATTERN.search(filename) and not VERSION_PATTERN_1.search(filename):
                good_suffix = False

            if not good_prefix and not good_suffix:
                bad_files.append((filename, file_type, prefix_rule, "presuf"))
            elif not good_prefix:
                bad_files.append((filename, file_type, prefix_rule, "prefix"))
            elif not good_suffix:
                bad_files.append((filename, file_type, prefix_rule, "suffix"))

        return bad_files

    @staticmethod
    def report_and_exit(bad_files):
        """REPORT"""
        if not bad_files:
            sys.exit(0)

        print("Please rename the following files：\n")
        
        for f, file_type, prefix_rule, err_type in bad_files:
            name_only = f[:-len(file_type)] if f.lower().endswith(file_type.lower()) else f

            if err_type == "prefix":
                suggested = prefix_rule + f
                print(f"  - {f}  → Missing prefix: '{prefix_rule}'  |  Suggested: {suggested}")

            elif err_type == "suffix":
                suggested = f"{name_only}_v01{file_type}"
                print(f"  - {f}  → Missing version suffix like '_v01'  |  Suggested: {suggested}")

            elif err_type == "presuf":
                suggested = f"{prefix_rule}{name_only}_v01{file_type}"
                print(f"  - {f}  → Missing both prefix '{prefix_rule}' and version suffix like '_v01'  |  Suggested: {suggested}")

        print("\nPlease rename the files before submitting again.")
        sys.exit(1)
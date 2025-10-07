#!/usr/bin/env python3
import os
import sys
from submit_check import FileNameChecker

# ========================
# 仓库特定配置
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PREFIX_RULES_FILE = os.path.join(SCRIPT_DIR, "prefix_rules.json")
# 可扩展：P4USER, P4PORT 等
os.environ["P4PORT"] = "ssl:localhost:1666"
os.environ["P4USER"] = "username"
os.environ["P4PASSWD"] = "passwd"
os.environ["P4CHARSET"] = "utf8"
# ========================

if len(sys.argv) != 2:
    print("Usage: trigger_repo1.py <changelist>")
    sys.exit(1)

cl = sys.argv[1]

checker = FileNameChecker(PREFIX_RULES_FILE)
files = checker.get_files_in_changelist(cl)
bad_files = checker.check_files(files)
checker.report_and_exit(bad_files)
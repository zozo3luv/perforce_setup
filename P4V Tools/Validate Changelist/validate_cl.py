# -*- coding: utf-8 -*-
import os
import sys
import subprocess
import re

def has_jp_cn(path: str) -> bool:
    """Check if the path contains Japanese or Chinese characters"""
    return bool(re.search(r'[\u3040-\u30ff\u31f0-\u31ff\u4e00-\u9fff]', path))

def validate_cl(cl: str):
    """Validate changelist"""
    #################################
    # Fetch the result of changelist

    if cl.lower() == "default":
        print("\n==================== RESULT ====================")
        print("Please save the default changelist, and try again. 请保存 Default Changelist 后再试。")
        print("Right-click the Default changelist in P4V and select 'Submit', fill in a description and SAVE")
        print("右键点击 P4V 中的 Default Changelist，选择 'Submit'，填写描述并保存")

        return
    
    result = subprocess.run(
        ["p4", "change", "-o", cl],
        capture_output=True, text=True, encoding="utf-8"
    )
 
    out = result.stdout

    # Check files, get files to revert, or revert and mark delete
    to_revert, to_revert_and_mark_delete = check_files(out)

    if not to_revert and not to_revert_and_mark_delete:
        # Nothing to do, all files valid, will try to submit
        if submit_cl(cl):
            print("\n==================== RESULT ====================")
            print("Successfully submitted changelist.")
            print("成功提交")
        else:
            print("\n==================== RESULT ====================")
            print("Please fix the problems and try again.")
            print("请修复问题后再提交")
        return

    # create new changelist and revert the files
    global to_revert_cl
    if to_revert_cl is None:
        to_revert_cl = create_new_cl("(Auto Generated) Revert Missing Files")

    if to_revert:
        add_files_to_cl(to_revert_cl, to_revert)

    if to_revert_and_mark_delete:
        global to_delete_cl
        if to_delete_cl is None:
            to_delete_cl = create_new_cl("(Auto Generated) Files to be deleted, please submit this changelist")
        add_files_to_cl(to_revert_cl, to_revert_and_mark_delete)
    
    # revert the changelist, and delete it
    revert_cl(to_revert_cl)
    delete_cl(to_revert_cl)
    
    # now mark the files as to delete and add files back to the to delete changelist
    if to_revert_and_mark_delete:
        mark_files_for_delete(to_revert_and_mark_delete)
        add_files_to_cl(to_delete_cl, to_revert_and_mark_delete)
        submit_cl(to_delete_cl, printMsg=False)
        print("Deleted moved away files that can't be tracked.")

    print("\n==================== RESULT ====================")
    print("There were files missing, the issue has been automatically dealt with. 有以下文件在本地不存在，已自动从 Changelist 中移除：")
    print("\n".join(to_revert))
    print("Please check the changelist and submit again. Changelist 已更新，请检查并重新提交。")
    
    return

# Convert depot path to local path
def depot_to_local(depot_path):
    """Use 'p4 where' to convert depot path to local path"""
    if has_jp_cn(depot_path):
        full_path = subprocess.run(
            ["p4", "-Q", "cp936", "where", depot_path],
            stdout=subprocess.PIPE,
            text=True,
            check=True
        )
    else:
        full_path = subprocess.run(
            ["p4", "where", depot_path],
            stdout=subprocess.PIPE,
            text=True,
            check=True
        )

    # 匹配 D: 或 C: 开头的路径，直到行尾
    match = re.search(r"[A-Za-z]:.*", full_path.stdout.strip())
    if match:
        return match.group(0)
    return None

def check_files(files):
    # 初始化列表
    to_revert = []
    to_revert_and_mark_delete = []

    # 正则匹配文件行
    pattern = re.compile(r"^\s*(//.+?)\s+#\s+(\S+)", re.MULTILINE)
    
    for match in pattern.finditer(files):
        depot_path, action = match.groups()

        if action not in ("add", "move/add"):
            continue

        # 验证文件是否存在
        local_path = depot_to_local(depot_path)
        if os.path.exists(local_path):
            continue
        
        # if the file does not exist, add to the appropriate list
        if action == "add":
            to_revert.append(depot_path)
        elif action in ("move/add"): #, "move/delete"):
            to_revert_and_mark_delete.append(depot_path)

    return to_revert, to_revert_and_mark_delete

def mark_files_for_delete(files):
    """Mark files for delete"""
    if not files:
        return
    
    _has_jp_cn = False
    for f in files:
        if has_jp_cn(f):
            _has_jp_cn = True
            break

    # mark files for delete
    if _has_jp_cn:
        subprocess.run(["p4", "-Q", "cp936", "delete"] + files)
    else:
        subprocess.run(["p4", "delete"] + files)
    
def add_files_to_cl(cl, files):
    """把文件加入 changelist"""
    if not files:
        return
    
    _has_jp_cn = False
    for f in files:
        if has_jp_cn(f):
            _has_jp_cn = True
            break

    # move files to the changelist
    if _has_jp_cn:
        subprocess.run(["p4", "-Q", "cp936", "reopen", "-c", cl] + files)
    else:
        subprocess.run(["p4", "reopen", "-c", cl] + files)

def create_new_cl(description):
    cmd = f'p4 --field "Description={description}" --field "Files=" change -o | p4 change -i'
    out = subprocess.run(cmd, text=True, capture_output=True, shell=True).stdout

    match = re.search(r"Change\s+(\d+)\s+created", out)
    if match:
        _new_cl = match.group(1)
        return _new_cl
    else:
        print("[Error] Failed to create changelist.")
        return None

def revert_cl(cl):
    """Revert the changelist"""
    cmd = f"p4 revert -c {cl} //..."
    out = subprocess.run(cmd, text=True, capture_output=True, shell=True, encoding="utf-8").stdout
    print(f"Reverted changelist {cl}:\n{out}")

def submit_cl(cl, printMsg=True) -> bool:
    """Submit the changelist"""
    cmd = f"p4 submit -c {cl}"
    result = subprocess.run(cmd, text=True, capture_output=True, shell=True, encoding="utf-8")
    if result.returncode != 0:
        print("Error submitting changelist:", result.stderr)
        return False
    
    # if no error, print the output
    if printMsg:
        print(f"All changes are valid, submitted changelist {cl}:\n{result.stdout}")
    return True

def delete_cl(cl):
    """Delete the changelist"""
    cmd = f"p4 change -d {cl}"
    out = subprocess.run(cmd, text=True, capture_output=True, shell=True, encoding="utf-8").stdout
    print(f"Deleted changelist {cl}:\n{out}")

to_revert_cl = None
to_delete_cl = None
def main():
    args = sys.argv[1:]
    if not args:
        print("No arguments received from P4V.")
        return
    
    for arg in args:
        validate_cl(arg)

if __name__ == "__main__":
    main()
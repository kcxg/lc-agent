"""Whitelist of extra directories (outside the current project) that
edit_extra_dirs_file.py is allowed to write/edit.

Only absolute paths are accepted. Add or remove entries as needed;
the script reloads this file on every run, so no restart is required.
"""

EXTRA_DIRS = [
    # r"D:\codes\project-b",
    # r"D:\codes\project-c",
    r"D:\codes",
]

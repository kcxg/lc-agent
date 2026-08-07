---
name: extra-dirs-file-edit
description: >-
  Write or edit files in extra directories outside the current project
  (e.g. another project on disk that the current workspace cannot modify).
  Use when the user asks to write, rewrite, append, or edit a file located
  in a directory outside the current project, or when Trae/agent reports
  that the target file is outside the workspace boundary. Operates on
  directories listed in the EXTRA_DIRS whitelist in scripts/extra_dirs_config.py.
---

# Extra-Dirs File Edit

Write or edit files in whitelisted extra directories (outside the current project) using the bundled script.

## Prerequisites

The target directory must be listed in `scripts/extra_dirs_config.py` (EXTRA_DIRS list, absolute paths). If it is missing, **do NOT edit the config yourself** — tell the user which directory to add (show the exact line to add), and wait for the user to confirm before proceeding.

## Commands

All commands run from the skill's `scripts/` directory:

```powershell
python edit_extra_dirs_file.py list
python edit_extra_dirs_file.py write <path> --content <text> [--mode rewrite|append]
python edit_extra_dirs_file.py write <path> --content-file <file> [--mode rewrite|append]
python edit_extra_dirs_file.py edit <path> <old_string> <new_string> [--expected N]
```

### list

Show the whitelist directories and verify the config file parses correctly.

### write

Write a file (rewrite whole file by default; `--mode append` appends). Parent directories are created automatically. Encoding is UTF-8 (no BOM).

**Rewriting an existing file is destructive**: `--mode rewrite` (the default) overwrites the entire file with no backup and no undo. Never use `rewrite` on an existing file — by default, modify existing files with `edit` (targeted find-and-replace). `rewrite` is only allowed in two cases: creating a new file, or the user explicitly asks for a full rewrite — and even then only after you have read the original file's complete content, so you know exactly what you are replacing.

**Append carefully**: before appending, read the file first and confirm the content you are about to add is not already present (avoid duplicate appends). If the existing file does not end with a newline, start your content with `\n` — otherwise it is concatenated onto the last line.

- Use `--content` inline only for short, plain text without newlines or shell-special characters (quotes, `$`, etc.).
- For any content containing newlines, quotes, `$`, non-ASCII characters, or a longer body: **you must** use `--content-file` — first write the content to a temp file inside the current project, then pass it with `--content-file <tempfile>`; delete the temp file afterwards.

### edit

Exactly find-and-replace a text block. `old_string` must match the file content character-for-character (including whitespace and newlines). Use `--expected N` to require exactly N matches (default 1) — the edit is refused if the actual match count differs.

**Be extremely careful when editing**: always prefer several small edits with a long, unique `old_string` (include surrounding context lines) over one edit with a large `--expected N`. A large `--expected` replaces all N matching blocks in one go and can silently modify unrelated code if the pattern repeats. Only raise `--expected` above 1 after verifying the exact match count and confirming you intend to change every occurrence. When in doubt, keep `--expected` at its default (1) and make multiple targeted edits.

## Workflow

1. Check the whitelist: `python edit_extra_dirs_file.py list`
2. If the target directory is not listed, **stop and ask the user to add it** to `scripts/extra_dirs_config.py` (show the exact line to add, e.g. `r"D:\codes\project-b",`). Never edit the config file yourself — only the user decides which directories are whitelisted. The script also refuses to write/edit `extra_dirs_config.py` itself, even if the skill directory is accidentally whitelisted. Continue only after the user confirms.
3. Run write or edit; if it fails (e.g. path not in whitelist, old_string not found), read the error and fix before retrying

## Notes

- Requires Python 3.6+ (pure standard library; no third-party packages). If `python` is not on PATH or is too old, run with a suitable interpreter explicitly, e.g. `D:\ProgramData\miniconda3\envs\py312\python.exe`.
- Paths not under any whitelist directory are rejected with an error.
- Always pass **absolute paths** for `<path>` and `--content-file`. Relative paths are resolved against the current working directory.
- For content with newlines or shell-special characters (quotes, `$`), prefer `--content-file`: write the content to a temp file first, then pass it. This avoids PowerShell quoting issues and command-line length limits. When using `--content` or `edit` with special characters, wrap arguments in single quotes in PowerShell.
- The script reloads `extra_dirs_config.py` on every run, so config changes take effect immediately.
- `edit` preserves the target file's line endings byte-for-byte; new content is written back with the same newline style as the original file.

"""Edit files in extra directories outside the current project (write/edit/list).

Usage:
  python edit_extra_dirs_file.py list
  python edit_extra_dirs_file.py write <path> --content <text> [--mode rewrite|append]
  python edit_extra_dirs_file.py write <path> --content-file <file> [--mode rewrite|append]
  python edit_extra_dirs_file.py edit <path> <old_string> <new_string> [--expected N]

The whitelist of extra directories is read from extra_dirs_config.py in the
same directory (EXTRA_DIRS list). Paths not under any whitelist directory are
rejected.
"""
import argparse
import os
import sys
from pathlib import Path
from typing import List

# UTF-8 stdout/stderr so output is not garbled on Windows PowerShell.
# reconfigure() is Python 3.7+; ignore where unavailable.
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_FILE = SCRIPT_DIR / "extra_dirs_config.py"


def load_extra_dirs() -> List[Path]:
    """Load the EXTRA_DIRS whitelist from extra_dirs_config.py.

    Raises SystemExit with a clear message if the config file is missing or
    EXTRA_DIRS is not a non-empty list of strings.
    """
    if not CONFIG_FILE.is_file():
        print(f"ERROR: config file not found: {CONFIG_FILE}", file=sys.stderr)
        sys.exit(2)

    namespace = {}
    try:
        exec(compile(CONFIG_FILE.read_text(encoding="utf-8"), str(CONFIG_FILE), "exec"), namespace)
    except Exception as e:
        print(f"ERROR: failed to load config {CONFIG_FILE}: {e}", file=sys.stderr)
        sys.exit(2)

    raw = namespace.get("EXTRA_DIRS")
    if not isinstance(raw, list) or not raw:
        print(f"ERROR: EXTRA_DIRS must be a non-empty list of directory paths in {CONFIG_FILE}", file=sys.stderr)
        sys.exit(2)

    dirs: List[Path] = []
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            print(f"ERROR: EXTRA_DIRS entries must be non-empty strings, got: {item!r}", file=sys.stderr)
            sys.exit(2)
        p = Path(item.strip()).expanduser()
        if not p.is_absolute():
            print(f"ERROR: EXTRA_DIRS entries must be absolute paths, got: {item!r}", file=sys.stderr)
            sys.exit(2)
        dirs.append(p.resolve())

    return dirs


def resolve_and_check(target: str, extra_dirs: List[Path]) -> Path:
    """Resolve target to an absolute path and verify it is inside the whitelist.

    The comparison is case-insensitive (Windows) and resolves '..' so path
    traversal outside the whitelist is rejected. The config file itself
    (extra_dirs_config.py) is always protected and can never be edited
    through this script — only the user may modify it by hand.
    """
    p = Path(target).expanduser().resolve()
    if os.path.normcase(str(p)) == os.path.normcase(str(CONFIG_FILE)):
        print(
            f"ERROR: editing the config file itself is not allowed: {CONFIG_FILE}\n"
            f"Only the user may modify it by hand.",
            file=sys.stderr,
        )
        sys.exit(2)

    norm_target = os.path.normcase(str(p))
    for d in extra_dirs:
        if norm_target == os.path.normcase(str(d)) or norm_target.startswith(os.path.normcase(str(d)) + os.sep):
            return p

    dirs_display = "\n".join(f"  - {d}" for d in extra_dirs)
    print(
        f"ERROR: path not in whitelist: {target}\n"
        f"Allowed extra directories ({len(extra_dirs)}):\n{dirs_display}",
        file=sys.stderr,
    )
    sys.exit(2)


def cmd_list(args: argparse.Namespace, extra_dirs: List[Path]) -> None:
    print(f"[extra-dirs] whitelist directories ({len(extra_dirs)}):")
    for d in extra_dirs:
        print(f"  - {d}")


def cmd_write(args: argparse.Namespace, extra_dirs: List[Path]) -> None:
    path = resolve_and_check(args.path, extra_dirs)

    if args.content is not None and args.content_file is not None:
        print("ERROR: use either --content or --content-file, not both", file=sys.stderr)
        sys.exit(2)

    if args.content is not None:
        content = args.content
    elif args.content_file is not None:
        cf = Path(args.content_file)
        if not cf.is_file():
            print(f"ERROR: content file not found: {cf}", file=sys.stderr)
            sys.exit(2)
        try:
            content = cf.open("r", encoding="utf-8", newline="").read()
        except Exception as e:
            print(f"ERROR: failed to read content file {cf}: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        print("ERROR: one of --content or --content-file is required", file=sys.stderr)
        sys.exit(2)

    if args.mode not in ("rewrite", "append"):
        print(f"ERROR: invalid mode: {args.mode} (use 'rewrite' or 'append')", file=sys.stderr)
        sys.exit(2)

    if args.mode == "append" and path.exists():
        try:
            existing = path.open("r", encoding="utf-8", newline="").read()
        except Exception as e:
            print(f"ERROR: existing file is not valid UTF-8, refusing to append: {path}: {e}", file=sys.stderr)
            sys.exit(2)
        # Avoid concatenating onto the last line: if the file does not end
        # with a newline and the new content does not already start with one,
        # insert a newline separator first.
        if existing and not existing.endswith("\n") and not content.startswith("\n"):
            content = "\n" + content

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if args.mode == "append":
            with open(str(path), "a", encoding="utf-8", newline="") as f:
                f.write(content)
            action = "Appended"
        else:
            with open(str(path), "w", encoding="utf-8", newline="") as f:
                f.write(content)
            action = "Written"
    except Exception as e:
        print(f"ERROR: failed to {args.mode} file {path}: {e}", file=sys.stderr)
        sys.exit(2)

    line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
    print(f"{action} {line_count} lines to {path}")


def cmd_edit(args: argparse.Namespace, extra_dirs: List[Path]) -> None:
    path = resolve_and_check(args.path, extra_dirs)

    if not path.is_file():
        print(f"ERROR: file not found: {args.path}", file=sys.stderr)
        sys.exit(2)

    try:
        content = path.open("r", encoding="utf-8", newline="").read()
    except UnicodeDecodeError as e:
        print(f"ERROR: file is not valid UTF-8: {path}: {e}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"ERROR: failed to read file {path}: {e}", file=sys.stderr)
        sys.exit(2)

    old_string = args.old_string
    new_string = args.new_string

    if not old_string:
        print("ERROR: old_string must not be empty", file=sys.stderr)
        sys.exit(2)

    count = content.count(old_string)
    if count == 0:
        snippet = old_string[:80]
        print(
            f"ERROR: old_string not found in file.\n"
            f'Searched for: "{snippet}{"..." if len(old_string) > 80 else ""}"',
            file=sys.stderr,
        )
        sys.exit(2)

    if count != args.expected:
        print(
            f"ERROR: expected {args.expected} occurrence(s) of old_string, "
            f"but found {count}. Refusing to replace to avoid unintended modifications.\n"
            f"Pass --expected {count} if you intend to replace all occurrences.",
            file=sys.stderr,
        )
        sys.exit(2)

    new_content = content.replace(old_string, new_string, args.expected)

    try:
        with open(str(path), "w", encoding="utf-8", newline="") as f:
            f.write(new_content)
    except Exception as e:
        print(f"ERROR: failed to write file {path}: {e}", file=sys.stderr)
        sys.exit(2)

    old_lines = old_string.count("\n") + 1
    new_lines = new_string.count("\n") + 1
    print(f"Replaced {count} occurrence(s) in {path}")
    print(f"  {old_lines} lines -> {new_lines} lines")


def main() -> None:
    parser = argparse.ArgumentParser(description="Write or edit files in whitelisted extra directories.")
    sub = parser.add_subparsers(dest="command")

    p_list = sub.add_parser("list", help="List whitelisted extra directories")
    p_list.set_defaults(func=cmd_list)

    p_write = sub.add_parser("write", help="Write (rewrite or append) a file in an extra directory")
    p_write.add_argument("path", help="Target file path (absolute, must be inside a whitelist directory)")
    p_write.add_argument("--content", help="Text content to write (for small files)")
    p_write.add_argument("--content-file", help="Path to a UTF-8 file whose content is written to the target (for large files)")
    p_write.add_argument("--mode", choices=["rewrite", "append"], default="rewrite", help="Write mode (default: rewrite)")
    p_write.set_defaults(func=cmd_write)

    p_edit = sub.add_parser("edit", help="Exactly find and replace a text block in a file in an extra directory")
    p_edit.add_argument("path", help="Target file path (absolute, must be inside a whitelist directory)")
    p_edit.add_argument("old_string", help="Exact text to replace; must match the file content character-for-character")
    p_edit.add_argument("new_string", help="Replacement text")
    p_edit.add_argument("--expected", type=int, default=1, help="Expected number of replacements (default: 1)")
    p_edit.set_defaults(func=cmd_edit)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(2)

    extra_dirs = load_extra_dirs()
    args.func(args, extra_dirs)


if __name__ == "__main__":
    main()

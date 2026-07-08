from pathlib import Path


PACKAGE_ROOT = Path("lc_agent")


def test_lc_agent_package_does_not_use_print_for_logging():
    violations = []
    repo_root = Path(__file__).resolve().parents[1]

    for path in (repo_root / PACKAGE_ROOT).rglob("*.py"):
        relative_path = path.relative_to(repo_root)
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if "print(" in stripped:
                violations.append(f"{relative_path}:{line_number}: {stripped}")

    assert violations == []

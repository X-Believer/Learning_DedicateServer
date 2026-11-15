import os
import sys
from pathlib import Path

WARNING_LIMIT = 50 * 1024 * 1024
GITHUB_LIMIT = 100 * 1024 * 1024


def get_status(size):
    if size >= GITHUB_LIMIT:
        return "EXCEED"
    elif size >= WARNING_LIMIT:
        return "WARNING"
    return "OK"


def print_report(title, results):
    print(f"\n=== {title} ===")
    exceed_count = 0
    warning_count = 0

    for path, size, status in results:
        print(f"[{status}] {size / (1024 * 1024):.2f} MB | {path}")
        if status == "EXCEED":
            exceed_count += 1
        else:
            warning_count += 1

    print("\nSummary:")
    print(f"EXCEED: {exceed_count}")
    print(f"WARNING: {warning_count}")


def is_ignored(root, path, specs):
    """Apply .gitignore rules from root down to the file's parent directory."""
    parts = path.relative_to(root).parts
    if ".git" in parts:
        return True  # Git's own metadata is never part of the checkout.

    active = []

    def matches(target, is_dir=False):
        ignored = False
        for base, spec in active:
            relative = target.relative_to(base).as_posix() + ("/" if is_dir else "")
            for pattern in spec.patterns:
                if pattern.include is not None and pattern.match_file(relative):
                    ignored = pattern.include
        return ignored

    for depth in range(len(parts)):
        directory = root.joinpath(*parts[:depth])
        if depth and matches(directory, is_dir=True):
            return True
        spec = specs.get(directory)
        if spec is not None:
            active.append((directory, spec))

    return matches(path)


def scan_directory(root):
    root = Path(root).resolve()
    if not root.is_dir():
        print(f"Not a directory: {root}", file=sys.stderr)
        return 1

    results = []
    ignore_files = []
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            filepath = Path(dirpath) / name
            if name == ".gitignore" and ".git" not in filepath.relative_to(root).parts:
                ignore_files.append(filepath)
            try:
                size = filepath.stat().st_size
            except OSError:
                continue
            status = get_status(size)
            if status != "OK":
                results.append((filepath, size, status))

    results.sort(key=lambda item: item[1], reverse=True)
    print_report("All files (ignore not applied)", results)

    if ignore_files:
        try:
            import pathspec
        except ImportError:
            print("\nTo apply .gitignore rules, install pathspec: python -m pip install pathspec", file=sys.stderr)
            return 1

        specs = {}
        for ignore_file in ignore_files:
            try:
                lines = ignore_file.read_text(encoding="utf-8-sig", errors="replace").splitlines()
            except OSError:
                continue
            specs[ignore_file.parent] = pathspec.GitIgnoreSpec.from_lines(lines)

        filtered = [item for item in results if not is_ignored(root, item[0], specs)]
        print_report("After .gitignore", filtered)
        print(f"Ignored large files: {len(results) - len(filtered)}")
    else:
        print("\nNo .gitignore found; filtered report skipped.")

    return 0


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    sys.exit(scan_directory(root))

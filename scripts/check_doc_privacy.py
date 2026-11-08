"""Read-only privacy checks for tracked public documentation."""
import argparse
import re
import subprocess
import sys
from pathlib import Path

TEXT_SUFFIXES = {".md", ".markdown", ".rst", ".adoc", ".txt", ".html", ".htm",
                 ".json", ".yaml", ".yml", ".toml"}
PATTERNS = (
    ("personal attribution", re.compile(r"\b\u004d\u0065\u0064\u0068\u0061\u0074\b|\u0645\u062f\u062d\u062a", re.I)),
    ("private home path", re.compile(r"/Users/[^/<>\s]+/|/home/(?!runner/)[^/<>\s]+/|[A-Z]:[\\/]+Users[\\/]+[^\\/<>%\s]+[\\/]", re.I)),
    ("private workspace", re.compile(r"owner workspace|Documents[/\\]+Codex|work/(?:release[\w/-]*|windows\d+|export\d+|watermark\d+|website-release)|outputs/Agmad[\w./-]*Review", re.I)),
)

def is_document(name):
    path = Path(name)
    return (path.suffix.lower() in TEXT_SUFFIXES
            or path.name.upper().startswith(("README", "LICENSE", "NOTICE", "COPYING")))

def safe_label(name):
    return "<redacted document path>" if any(p.search(name) for _, p in PATTERNS) else name

def check_text(name, data):
    try:
        text = data.decode("utf-8-sig")
    except UnicodeError:
        return [f"{safe_label(name)}: documentation must be UTF-8"]
    return [f"{safe_label(name)}:{number}: {kind}"
            for number, line in enumerate(text.splitlines(), 1)
            for kind, pattern in PATTERNS if pattern.search(line)]

def check_repository(root):
    result = subprocess.run(["git", "-C", str(root), "ls-files", "--cached", "-z"],
                            capture_output=True)
    if result.returncode:
        raise ValueError("Cannot enumerate tracked documentation; use a Git checkout.")
    names = result.stdout.decode("utf-8").split("\0")
    documents = sorted(name for name in names if name and is_document(name))
    if not documents:
        raise ValueError("No tracked documentation found.")
    failures = []
    for name in documents:
        path = root / name
        if any(pattern.search(name) for _, pattern in PATTERNS):
            failures.append("Tracked document path: private reference (path redacted)")
        if path.is_symlink() or not path.is_file():
            failures.append(f"{safe_label(name)}: documentation must be a regular file")
            continue
        try:
            data = path.read_bytes()
        except OSError:
            failures.append(f"{safe_label(name)}: cannot read documentation")
            continue
        failures.extend(check_text(name, data))
    if failures:
        raise ValueError("Documentation privacy check failed:\n" + "\n".join(failures))
    return len(documents)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    try:
        count = check_repository(args.root)
    except (OSError, UnicodeError):
        print("Cannot read tracked documentation.", file=sys.stderr)
        return 1
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    print(f"Documentation privacy check passed ({count} tracked documents).")
    return 0

if __name__ == "__main__":
    sys.exit(main())

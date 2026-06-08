#!/usr/bin/env python3
"""Update or verify the README paper-count badge."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


BADGE_RE = re.compile(r"!\[Papers\]\(https://img\.shields\.io/badge/Papers-(\d+)-blue\)")
PAPER_RE = re.compile(r"^\*\s+", re.MULTILINE)


def count_papers(readme_text: str) -> int:
    papers_section = readme_text.split("## 📚 Papers", 1)[-1]
    return len(PAPER_RE.findall(papers_section))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readme", default="README.md", type=Path)
    parser.add_argument("--check", action="store_true", help="fail if the badge is out of date")
    args = parser.parse_args()

    text = args.readme.read_text(encoding="utf-8")
    count = count_papers(text)
    match = BADGE_RE.search(text)
    if not match:
        print("Could not find the Papers badge.", file=sys.stderr)
        return 1

    current = int(match.group(1))
    if current == count:
        print(f"Papers badge is up to date: {count}")
        return 0

    updated = BADGE_RE.sub(f"![Papers](https://img.shields.io/badge/Papers-{count}-blue)", text, count=1)
    if args.check:
        print(f"Papers badge is stale: badge={current}, actual={count}", file=sys.stderr)
        return 1

    args.readme.write_text(updated, encoding="utf-8")
    print(f"Updated Papers badge: {current} -> {count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


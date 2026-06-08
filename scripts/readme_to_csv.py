#!/usr/bin/env python3
"""Extract paper entries from README.md into data/papers.csv."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path


FIELDNAMES = [
    "category",
    "title",
    "venue",
    "year",
    "paper",
    "pdf",
    "code",
    "project",
    "notes",
]

HEADING_RE = re.compile(r"^###\s+(?P<heading>.+?)\s*$")
PAPER_RE = re.compile(r"^\*\s+(?P<body>.+?)\s+`(?P<venue>[^`]+)`\s*(?P<links>.*)$")
LINK_RE = re.compile(r"\[\[(?P<label>[^\]]+)\]\((?P<url>[^)]+)\)\]")


def normalize_heading(heading: str) -> str:
    # Remove leading emoji or pictographic markers while preserving text.
    return re.sub(r"^[^\w\[]+\s*", "", heading).strip()


def split_venue_year(venue_text: str) -> tuple[str, str]:
    parts = venue_text.rsplit(" ", 1)
    if len(parts) == 2 and re.fullmatch(r"\d{2,4}", parts[1]):
        year = parts[1]
        if len(year) == 2:
            year = "20" + year if int(year) <= 50 else "19" + year
        return parts[0], year
    return venue_text, ""


def parse_readme(readme: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    category = ""

    for line in readme.read_text(encoding="utf-8").splitlines():
        heading_match = HEADING_RE.match(line)
        if heading_match:
            category = normalize_heading(heading_match.group("heading"))
            continue

        paper_match = PAPER_RE.match(line)
        if not paper_match:
            continue

        body = paper_match.group("body").strip()
        title = body[:-1] if body.endswith(".") else body
        venue, year = split_venue_year(paper_match.group("venue").strip())
        links = {match.group("label").lower(): match.group("url") for match in LINK_RE.finditer(paper_match.group("links"))}

        rows.append(
            {
                "category": category,
                "title": title,
                "venue": venue,
                "year": year,
                "paper": links.get("paper", ""),
                "pdf": links.get("pdf", ""),
                "code": links.get("code", ""),
                "project": links.get("project", ""),
                "notes": "",
            }
        )

    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--readme", default="README.md", type=Path)
    parser.add_argument("--output", default="data/papers.csv", type=Path)
    parser.add_argument("--force", action="store_true", help="overwrite the output file if it exists")
    args = parser.parse_args()

    if args.output.exists() and not args.force:
        print(f"{args.output} already exists. Re-run with --force to overwrite.", file=sys.stderr)
        return 2

    rows = parse_readme(args.readme)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


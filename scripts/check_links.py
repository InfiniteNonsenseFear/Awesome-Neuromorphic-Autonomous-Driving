#!/usr/bin/env python3
"""Check links in Markdown and CSV files."""

from __future__ import annotations

import argparse
import csv
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\((https?://[^)]+)\)")
CSV_URL_COLUMNS = {"paper", "pdf", "code", "project"}
USER_AGENT = "Awesome-Neuromorphic-Autonomous-Driving/0.1 (link check)"


def urls_from_markdown(path: Path) -> list[str]:
    return MARKDOWN_LINK_RE.findall(path.read_text(encoding="utf-8"))


def urls_from_csv(path: Path) -> list[str]:
    urls: list[str] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            for column in CSV_URL_COLUMNS:
                value = (row.get(column) or "").strip()
                if value.startswith(("http://", "https://")):
                    urls.append(value)
    return urls


def urls_from_path(path: Path) -> list[str]:
    if path.suffix.lower() == ".csv":
        return urls_from_csv(path)
    return urls_from_markdown(path)


def check_url(url: str, timeout: int) -> tuple[bool, str]:
    headers = {"User-Agent": USER_AGENT}
    for method in ("HEAD", "GET"):
        request = urllib.request.Request(url, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                status = response.getcode()
                if 200 <= status < 400:
                    return True, str(status)
                last_status = str(status)
        except urllib.error.HTTPError as exc:
            # Some hosts reject HEAD but allow GET, so only fail after GET.
            last_status = str(exc.code)
            if method == "HEAD" and exc.code in {403, 405, 429}:
                continue
            return False, last_status
        except Exception as exc:
            last_status = exc.__class__.__name__
            if method == "HEAD":
                continue
            return False, last_status
    return False, last_status


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, default=[Path("README.md"), Path("data/papers.csv")])
    parser.add_argument("--timeout", default=15, type=int)
    parser.add_argument("--max", default=0, type=int, help="limit number of unique URLs checked; 0 means all")
    args = parser.parse_args()

    urls: list[str] = []
    for path in args.paths:
        if path.exists():
            urls.extend(urls_from_path(path))
        else:
            print(f"SKIP missing path: {path}")

    unique_urls = list(dict.fromkeys(urls))
    if args.max:
        unique_urls = unique_urls[: args.max]

    failed: list[tuple[str, str]] = []
    for index, url in enumerate(unique_urls, start=1):
        ok, status = check_url(url, args.timeout)
        print(f"[{index}/{len(unique_urls)}] {'OK' if ok else 'FAIL'} {status} {url}")
        if not ok:
            failed.append((url, status))

    if failed:
        print("\nFailed links:", file=sys.stderr)
        for url, status in failed:
            print(f"- {status} {url}", file=sys.stderr)
        return 1

    print(f"Checked {len(unique_urls)} unique URLs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


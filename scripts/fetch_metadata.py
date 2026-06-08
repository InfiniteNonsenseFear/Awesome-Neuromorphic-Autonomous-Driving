#!/usr/bin/env python3
"""Enrich data/papers.csv with metadata from OpenAlex."""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


OPENALEX = "https://api.openalex.org/works"
USER_AGENT = "Awesome-Neuromorphic-Autonomous-Driving/0.1 (metadata enrichment)"


def request_json(url: str, timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def doi_from_url(url: str) -> str:
    match = re.search(r"(10\.\d{4,9}/[^\s)]+)", url, flags=re.IGNORECASE)
    return match.group(1).rstrip(".") if match else ""


def arxiv_id_from_url(url: str) -> str:
    match = re.search(r"arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{4,5})(?:v\d+)?", url, flags=re.IGNORECASE)
    return match.group(1) if match else ""


def openalex_url(row: dict[str, str]) -> str:
    paper = row.get("paper", "")
    doi = doi_from_url(paper)
    if doi:
        return f"{OPENALEX}/doi:{urllib.parse.quote(doi)}"

    arxiv_id = arxiv_id_from_url(paper)
    if arxiv_id:
        doi = f"10.48550/arxiv.{arxiv_id}"
        return f"{OPENALEX}/doi:{urllib.parse.quote(doi)}"

    query = urllib.parse.urlencode({"search": row["title"], "per-page": "1"})
    return f"{OPENALEX}?{query}"


def normalize_result(payload: dict[str, Any]) -> dict[str, Any] | None:
    if "results" in payload:
        results = payload.get("results") or []
        return results[0] if results else None
    return payload if payload.get("title") else None


def source_name(result: dict[str, Any]) -> str:
    location = result.get("primary_location") or {}
    source = location.get("source") or {}
    return source.get("display_name") or location.get("raw_source_name") or ""


def best_url(result: dict[str, Any]) -> str:
    location = result.get("primary_location") or {}
    return location.get("landing_page_url") or result.get("doi") or result.get("id") or ""


def best_pdf(result: dict[str, Any]) -> str:
    best_oa = result.get("best_oa_location") or {}
    open_access = result.get("open_access") or {}
    return best_oa.get("pdf_url") or open_access.get("oa_url") or ""


def enrich_row(row: dict[str, str], result: dict[str, Any]) -> dict[str, str]:
    enriched = dict(row)
    if not enriched.get("title"):
        enriched["title"] = result.get("title") or ""
    if not enriched.get("year") and result.get("publication_year"):
        enriched["year"] = str(result["publication_year"])
    if not enriched.get("venue"):
        enriched["venue"] = source_name(result)
    if not enriched.get("paper"):
        enriched["paper"] = best_url(result)
    if not enriched.get("pdf"):
        enriched["pdf"] = best_pdf(result)
    return enriched


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default="data/papers.csv", type=Path)
    parser.add_argument("--output", default="data/papers.enriched.csv", type=Path)
    parser.add_argument("--metadata", default="data/metadata.json", type=Path)
    parser.add_argument("--timeout", default=15, type=int)
    parser.add_argument("--sleep", default=0.15, type=float, help="delay between OpenAlex requests")
    parser.add_argument("--limit", default=0, type=int, help="limit number of rows processed; 0 means all")
    args = parser.parse_args()

    with args.input.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = reader.fieldnames or []
    if args.limit:
        rows = rows[: args.limit]

    enriched_rows: list[dict[str, str]] = []
    metadata: list[dict[str, Any]] = []

    for index, row in enumerate(rows, start=1):
        url = openalex_url(row)
        try:
            payload = request_json(url, args.timeout)
            result = normalize_result(payload)
        except Exception as exc:  # Network and malformed-response errors are reported per row.
            print(f"[{index}/{len(rows)}] ERROR {row.get('title', '')}: {exc}")
            enriched_rows.append(row)
            continue

        if result:
            enriched_rows.append(enrich_row(row, result))
            metadata.append(
                {
                    "title": row.get("title", ""),
                    "openalex_id": result.get("id"),
                    "doi": result.get("doi"),
                    "publication_year": result.get("publication_year"),
                    "source": source_name(result),
                    "landing_page_url": best_url(result),
                    "pdf_url": best_pdf(result),
                }
            )
            print(f"[{index}/{len(rows)}] OK {row.get('title', '')}")
        else:
            enriched_rows.append(row)
            print(f"[{index}/{len(rows)}] MISS {row.get('title', '')}")

        time.sleep(args.sleep)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(enriched_rows)

    args.metadata.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(enriched_rows)} rows to {args.output}")
    print(f"Wrote {len(metadata)} metadata records to {args.metadata}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

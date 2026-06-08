# Maintenance Scripts

These scripts keep the paper list maintainable without extra Python dependencies.

## Typical Workflow

```bash
python3 scripts/readme_to_csv.py --force
python3 scripts/fetch_metadata.py
python3 scripts/update_badge_count.py
python3 scripts/check_links.py README.md
```

## Scripts

* `readme_to_csv.py`: extracts paper entries from `README.md` into `data/papers.csv`.
* `fetch_metadata.py`: enriches rows in `data/papers.csv` with OpenAlex metadata and writes `data/papers.enriched.csv` plus `data/metadata.json`.
* `update_badge_count.py`: keeps the `Papers-*` badge in `README.md` synchronized with the number of paper bullets.
* `check_links.py`: checks Markdown and CSV URLs using HTTP HEAD with GET fallback.

`fetch_metadata.py` and `check_links.py` require network access.


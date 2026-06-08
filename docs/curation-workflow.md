# Curation Workflow

## Add a Paper

1. Add the paper to the right section in `README.md`.
2. Include at least one stable `Paper` link, preferably DOI, arXiv, publisher, or conference page.
3. Add `PDF`, `Code`, or `Project` links when available.
4. Run:

```bash
python3 scripts/update_badge_count.py
python3 scripts/readme_to_csv.py --force
python3 scripts/check_links.py README.md data/papers.csv
```

## Refresh Metadata

Use OpenAlex enrichment when many rows are missing metadata:

```bash
python3 scripts/fetch_metadata.py
```

Review `data/papers.enriched.csv` manually before copying any changes back into `README.md`.


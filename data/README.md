# Data

`papers.csv` is the structured source table for paper metadata.

## Columns

* `category`: README section name.
* `title`: paper title.
* `venue`: venue or source label.
* `year`: publication year.
* `paper`: canonical DOI, arXiv, publisher, or conference link.
* `pdf`: direct PDF link when available.
* `code`: code repository link when available.
* `project`: project page link when available.
* `notes`: short curator notes.

Use `python3 scripts/readme_to_csv.py --force` to regenerate this file from `README.md`.


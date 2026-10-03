# Frozen synthetic raw data

`synthetic_savings_experiment.csv` is fictional, generated with seed `20261003`, and contains no real participant records. Its SHA-256 digest is recorded in `manifest.json`.

Treat this file as an immutable input: analysis writes derived data under `data/processed/` and never edits the raw CSV. The generator refuses to replace it unless you explicitly pass `--force`; only do that when you intentionally want a new synthetic fixture and will review the changed raw file and manifest.

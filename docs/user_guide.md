# Beginner guide

This project is a safe practice example. The normal commands use made-up data and do not contact OpenAI or Prolific.

## Run it

Open a terminal in the repository folder. With Python 3.11 or newer:

```bash
PYTHONPATH=src python -m research_demo.cli
PYTHONPATH=src python -m research_demo.cli --run-experiment
PYTHONPATH=src python -m research_demo.cli --evaluate-labels
PYTHONPATH=src python -m research_demo.cli --batch-demo
PYTHONPATH=src python -m unittest discover -s tests -v
```

On Windows PowerShell, first set the source folder once in that terminal:

```powershell
$env:PYTHONPATH = "src"
python -m research_demo.cli --run-experiment
```

## What each example prints or creates

- The default command prints a small processing log for four fictional comments.
- `--run-experiment` verifies the raw data checksum, applies the consent, eligibility, attention, and time rules, and writes cleaned CSV plus a summary JSON under `data/processed/`.
- `--evaluate-labels` compares simulated model labels with fictional human reference labels and writes a confusion matrix, agreement, and Cohen's kappa. No AI call is made.
- `--batch-demo` simulates 100 items, two temporary errors, and a restart from a saved checkpoint. It never calls an AI service.
- The test command runs the checks with Python's built-in `unittest`; it does not require API keys.

The checked-in raw file already contains its randomized assignments. To understand how it was generated, read `make_synthetic_participants()` in `src/research_demo/experiment.py`. The generator will not overwrite the frozen CSV unless you explicitly pass `--force`.

## API keys

The live examples in the first version of this project need environment variables named `OPENAI_API_KEY` and `PROLIFIC_API_TOKEN`. `.env.example` is only a list of names; the code does not load `.env` automatically. Never paste a real key into a source file, GitHub issue, README, or chat. Start with the offline commands above.

## Common problems

- `No module named research_demo`: run the command from the repository root and set `PYTHONPATH=src` as shown above.
- `OPENAI_API_KEY` missing: you selected the live LLM option without setting a key. Use the default offline command, or set the key in your own secure shell environment.
- Checksum changed: restore the committed raw fixture or intentionally create a new version with a new manifest. Do not silently edit the raw CSV.
- Batch item failed: rerunning with the same checkpoint skips completed items and retries failed ones.

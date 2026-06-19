# InterpUpdates dashboard

Live experiment dashboard for the InterpUpdates project (interpretable fine-tuning
updates: localizing & removing spurious-correlation shortcuts in LLMs).

Published via GitHub Pages at https://interpupdates.github.io

## Structure
- `index.html` — dashboard (generated from `experiments.json`)
- `experiments.json` — the running experiment log (source of truth)
- `build_dashboard.py` — regenerates `index.html` from the manifest
- `reports/<id>/index.html` — individual experiment reports

## Adding an experiment
1. Append an entry to `experiments.json` (id, title, date, status, tags, summary, report path).
2. Drop the report HTML at `reports/<id>/index.html`.
3. `python build_dashboard.py` and commit.

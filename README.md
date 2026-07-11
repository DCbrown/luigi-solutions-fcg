# Fictional Client Generator (FCG)

Generate a realistic-but-fake client data project, practice against it, then upload
your work and get it scored.

## Loop

1. **Generate** — the app invents a client, a business context, a brief with
   deliverables, and a messy dataset to match.
2. **Practice** — you work the project in your own tools (notebook, script, BI).
3. **Submit** — upload your deliverables back into the app.
4. **Score** — the app grades the submission against the rubric generated with
   the brief and returns a scorecard with feedback.

## Quickstart

```bash
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
streamlit run app/main.py
```

Then: **Generate** → read the brief → go build it → **Submit** your repo URL.

Same seed, same client. Hand someone `4471` and you'll both get Old Mill Bakery,
the same brief, and comparable scores.

```bash
pytest        # 37 tests
```

## Layout

| Path | What lives here |
| --- | --- |
| `app/` | Streamlit UI only — pages, widgets, no business logic |
| `src/fcg/generator/` | Client, brief, and dataset generation |
| `src/fcg/scoring/` | Rubric, checks, and scorecard reporting |
| `data/seeds/` | Name/industry/scenario pools the generator draws from |
| `data/generated/` | Generated projects (one folder per project id) |
| `data/submissions/` | Uploaded user submissions |
| `docs/` | Vision, requirements, quality bar, decisions, roadmap |
| `tests/` | Pytest suite |

## Docs

- [Vision](docs/vision.md)
- [Requirements](docs/requirements.md)
- [Quality](docs/quality.md)
- [Decisions](docs/decisions.md)
- [Roadmap](docs/roadmap.md)

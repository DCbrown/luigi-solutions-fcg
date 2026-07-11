"""Where projects and submissions live on disk.

Files, not a database — single user, small data, and a JSON blob you can just
*look at* is worth a lot while the generator is still being tuned
(docs/decisions.md D5). This module is the seam that would absorb a real database
later, which is why nothing else in the app calls `open()`.

    data/generated/<project_id>/project.json     the Project, serialised
    data/generated/<project_id>/seed_data.csv    what the user downloads
    data/submissions/<project_id>/               scorecards
"""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

import pandas as pd

from fcg.models import Brief, Client, Feature, Project, RubricItem

ROOT = Path(__file__).resolve().parents[2]
GENERATED = ROOT / "data" / "generated"
SUBMISSIONS = ROOT / "data" / "submissions"
SEEDS = ROOT / "data" / "seeds"


def project_dir(project_id: str) -> Path:
    return GENERATED / project_id


def submission_dir(project_id: str) -> Path:
    return SUBMISSIONS / project_id


def save_project(project: Project, seed_data: pd.DataFrame) -> Path:
    """Write project.json and seed_data.csv. Return the project folder.

    The rubric lives inside project.json. It is not secret from the *filesystem* —
    a determined user can read it — but the UI never shows it before submission,
    which is what D6 actually cares about. Making it genuinely unreadable would
    mean encrypting it against its own owner, which is silly.
    """
    d = project_dir(project.id)
    d.mkdir(parents=True, exist_ok=True)

    payload = asdict(project)
    payload["created_at"] = project.created_at.isoformat()
    (d / "project.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    seed_data.to_csv(d / project.seed_data_file, index=False)
    return d


def load_project(project_id: str) -> Project:
    """Rehydrate a Project from disk."""
    path = project_dir(project_id) / "project.json"
    if not path.exists():
        raise FileNotFoundError(f"No project {project_id!r} at {path}")

    raw = json.loads(path.read_text())
    brief = raw["brief"]

    return Project(
        id=raw["id"],
        seed=raw["seed"],
        difficulty=raw["difficulty"],
        scenario=raw["scenario"],
        client=Client(**raw["client"]),
        brief=Brief(
            ask=brief["ask"],
            context=brief["context"],
            features=[Feature(**f) for f in brief["features"]],
            required_files=brief["required_files"],
            constraints=brief["constraints"],
        ),
        rubric=[RubricItem(**r) for r in raw["rubric"]],
        created_at=date.fromisoformat(raw["created_at"]),
        seed_data_file=raw["seed_data_file"],
    )


def load_seed_data(project_id: str) -> pd.DataFrame:
    """The client's content, exactly as the generator made it.

    CSV has no types, and the defaults are actively wrong for us:

    * An empty description is content — the client left the field blank — not a
      missing value. Left to itself pandas reads it back as NaN.
    * `available` returns as the *strings* "True"/"False", and a non-empty string
      is truthy. `data[data["available"]]` would then quietly treat every product
      as available, and `seed_data_used` would demand the user display an item the
      client marked as sold out.

    So the types are pinned on the way in rather than trusted.
    """
    project = load_project(project_id)
    path = project_dir(project_id) / project.seed_data_file

    df = pd.read_csv(
        path,
        keep_default_na=False,
        dtype={
            "sku": str, "name": str, "category": str,
            "description": str, "allergens": str,
        },
    )
    # Depending on the pandas version this arrives already parsed as bool, or as
    # the strings "True"/"False". Coerce only when it's the latter: mapping a
    # column that is *already* bool matches nothing, yields NaN — and NaN is
    # truthy, so it would resurrect the very bug this is here to prevent.
    if df["available"].dtype != bool:
        df["available"] = df["available"].map(
            {"True": True, "true": True, "False": False, "false": False}
        )
    df["available"] = df["available"].astype(bool)
    df["price"] = df["price"].astype(float)
    return df


def list_projects() -> list[str]:
    """Project ids currently on disk, newest first."""
    if not GENERATED.exists():
        return []
    return sorted((p.name for p in GENERATED.iterdir() if p.is_dir()), reverse=True)

"""The signed-in user's generation history, rebuilt from seeds.

No project payload is stored anywhere: a project is a pure function of its
seed (docs/decisions.md D1), and the project_id in generation_events —
"bakery-4471" — encodes scenario and seed. So history is just rows from that
table, and each entry regenerates byte-identically on demand.

Caveat pinned here on purpose: difficulty is NOT in the id (it's always
"medium" today, D7). The day difficulty becomes real, generation_events
needs a difficulty column and this module stops assuming the default.
"""

import pandas as pd

from fcg.generator import generate_project
from fcg.models import Project

from auth import _client, current_user


def parse_project_id(project_id: str) -> tuple[str, int]:
    """Split "bakery-4471" into ("bakery", 4471)."""
    scenario, seed = project_id.rsplit("-", 1)
    if not scenario:
        raise ValueError(f"no scenario in project id: {project_id!r}")
    return scenario, int(seed)


def rebuild(project_id: str) -> tuple[Project, pd.DataFrame]:
    """Regenerate a project identically from its id (D1)."""
    scenario, seed = parse_project_id(project_id)
    project, seed_data = generate_project(seed=seed, scenario=scenario)
    assert project.id == project_id, f"{project.id} != {project_id}"
    return project, seed_data


def recent_generations(limit: int = 25) -> list[dict]:
    """The user's generation_events rows, newest first.

    Each row: id, project_id, created_at (ISO string). RLS scopes the query
    to the signed-in user via the client's JWT.
    """
    res = (
        _client()
        .table("generation_events")
        .select("id, project_id, created_at")
        .eq("user_id", current_user().id)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return res.data or []

"""Assemble a whole Project from a seed.

Everything random descends from `random.Random(seed)`, so the same seed always
rebuilds the same project — byte for byte. That's what makes a project shareable
("try seed 4471") and a score comparable. See docs/decisions.md D1.
"""

from __future__ import annotations

import random

import pandas as pd

from fcg.generator.brief import generate_brief, generate_rubric
from fcg.generator.client import generate_client
from fcg.generator.dataset import generate_seed_data
from fcg.models import Project

SCENARIO = "bakery"  # v1 ships one scenario — docs/decisions.md D7


def generate_project(
    seed: int | None = None, difficulty: str = "medium"
) -> tuple[Project, pd.DataFrame]:
    """Build a complete, self-consistent fictional engagement.

    Order matters. The client shapes the brief, the brief decides what content the
    page must display, and the rubric is derived from the brief's features — so the
    thing you're graded on can never drift from the thing you were asked for.

    Returns the Project and its seed data; `storage.save_project` writes both.
    """
    if seed is None:
        seed = random.randrange(1, 1_000_000)

    rng = random.Random(seed)

    client = generate_client(rng, SCENARIO)
    brief = generate_brief(rng, client, difficulty)
    seed_data = generate_seed_data(rng, SCENARIO, difficulty)
    rubric = generate_rubric(rng, brief)

    project = Project(
        id=f"{SCENARIO}-{seed}",
        seed=seed,
        difficulty=difficulty,
        scenario=SCENARIO,
        client=client,
        brief=brief,
        rubric=rubric,
    )
    return project, seed_data

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

DEFAULT_SCENARIO = "bakery"
# `scenario` is an explicit parameter, NOT a seeded random choice. That's the whole
# point of the walking skeleton: it proves the generator is scenario-agnostic
# without touching the RNG draw order, so every existing seed still reproduces the
# exact same project it always did (Q2). Wiring scenario selection into the seed —
# so a random seed spreads across scenarios — is a deliberate later step, because
# it renumbers the project space and that's a one-way door once seeds are shared.


def generate_project(
    seed: int | None = None,
    difficulty: str = "medium",
    scenario: str = DEFAULT_SCENARIO,
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

    client = generate_client(rng, scenario)
    brief = generate_brief(rng, client, difficulty, scenario)
    seed_data = generate_seed_data(rng, scenario, difficulty)
    rubric = generate_rubric(rng, brief)

    project = Project(
        id=f"{scenario}-{seed}",
        seed=seed,
        difficulty=difficulty,
        scenario=scenario,
        client=client,
        brief=brief,
        rubric=rubric,
    )
    return project, seed_data

"""Invent the fictional company and the person who emails you about it."""

from __future__ import annotations

import random

from faker import Faker

from fcg.generator.seeds import load_pool
from fcg.models import Client


def generate_client(rng: random.Random, scenario: str = "bakery") -> Client:
    """Draw a company, a contact, and a background paragraph from the pools.

    The Faker instance is seeded from `rng` rather than globally, so client
    generation stays a pure function of the project seed (docs/quality.md Q2).
    """
    pool = load_pool(scenario)

    fake = Faker()
    fake.seed_instance(rng.randrange(2**32))

    name = f"{rng.choice(pool['company_first'])} {rng.choice(pool['company_last'])}"
    location = rng.choice(pool["neighbourhoods"])
    founded = rng.choice(pool["founded"])
    quirk = rng.choice(pool["quirks"])

    # The one line that used to be hardcoded bakery ("has been baking out of…").
    # It now lives in the pool as a template, so a second scenario reads like
    # itself. Pure string formatting — it consumes no RNG draws, so the bakery's
    # output is byte-identical to before (guarded by the Q2 reproducibility test).
    background = pool["background_template"].format(
        name=name, location=location, founded=founded, quirk=quirk
    )

    return Client(
        name=name,
        industry=pool["industry"],
        size=pool["size"],
        contact_name=fake.name(),
        contact_role=rng.choice(pool["roles"]),
        background=background,
    )

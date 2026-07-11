"""Generate the client's content — the products the built page has to display.

This is not a puzzle to be cleaned. It's the company's real list, straight off
their till, and the user's page has to render it.

It always contains at least one **awkward row** — a name too long for a tidy card,
an empty description, an accent, a price with an odd shape. Real content has
these and invented content never does. If the user's layout only works on the data
they'd have made up themselves, they should find that out here rather than in
front of a client (docs/requirements.md R1.4).
"""

from __future__ import annotations

import random

import pandas as pd

from fcg.generator.seeds import load_pool

ROW_COUNT = {"easy": 10, "medium": 14, "hard": 18}

COLUMNS = ["sku", "name", "category", "price", "description", "allergens", "available"]


def generate_seed_data(
    rng: random.Random, scenario: str = "bakery", difficulty: str = "medium"
) -> pd.DataFrame:
    """Build the client's product table.

    Every dataset gets the scenario's **awkward rows** — a name too long for a tidy
    card, an empty description, an accent-and-ampersand, one item sold out. These
    used to be hardcoded bakery products; they live in the pool now, so each
    scenario supplies edge cases that look like its own content (a deli's long name
    is a whole cheese wedge, not a sourdough). They carry fixed SKUs and consume no
    RNG, so the draw order — and every existing seed's output — is unchanged.
    """
    pool = load_pool(scenario)

    n = ROW_COUNT.get(difficulty, 14)
    # Copy each row: the pool is lru_cached, and these dicts must not be mutated.
    awkward = [dict(row) for row in pool["awkward"]]
    n_normal = max(n - len(awkward), 1)

    chosen = rng.sample(pool["products"], min(n_normal, len(pool["products"])))

    prefix = pool["sku_prefix"]
    rows = [
        {
            "sku": f"{prefix}-{200 + i}",
            "name": p["name"],
            "category": p["category"],
            "price": p["price"],
            "description": p["description"],
            "allergens": p["allergens"],
            "available": rng.random() > 0.15,
        }
        for i, p in enumerate(chosen)
    ]
    rows += awkward

    rng.shuffle(rows)
    return pd.DataFrame(rows, columns=COLUMNS)

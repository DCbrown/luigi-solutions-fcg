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


def _awkward_rows(rng: random.Random) -> list[dict]:
    """The rows that break a naive layout. Every dataset gets these."""
    return [
        {
            # Too long for a tidy card. Forces them to think about overflow.
            "sku": "BK-101",
            "name": "Sourdough Loaf with Kalamata Olive, Rosemary and Sea Salt (Large Tin)",
            "category": "Bread",
            "price": 7.25,
            "description": "Our Saturday special. Sells out by ten, every week, without fail.",
            "allergens": "gluten",
            "available": True,
        },
        {
            # Empty optional field. Their template had better cope.
            "sku": "BK-102",
            "name": "Baker's Choice Box",
            "category": "Bread",
            "price": 12.0,
            "description": "",
            "allergens": "gluten, milk, egg, nuts",
            "available": True,
        },
        {
            # Accent and an ampersand. Escaping, or a mangled page.
            "sku": "BK-103",
            "name": "Pain au Chocolat & Crème Pâtissière Twist",
            "category": "Pastry",
            "price": 4.1,
            "description": "The one the owner's daughter insisted on.",
            "allergens": "gluten, milk, egg",
            "available": False,  # not available — does the page show that?
        },
    ]


def generate_seed_data(
    rng: random.Random, scenario: str = "bakery", difficulty: str = "medium"
) -> pd.DataFrame:
    """Build the client's product table."""
    pool = load_pool(scenario)

    n = ROW_COUNT.get(difficulty, 14)
    awkward = _awkward_rows(rng)
    n_normal = max(n - len(awkward), 1)

    chosen = rng.sample(pool["products"], min(n_normal, len(pool["products"])))

    rows = [
        {
            "sku": f"BK-{200 + i}",
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

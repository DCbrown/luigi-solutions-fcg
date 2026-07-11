"""Write the client's ask, and derive the rubric from it.

The rubric is generated *here*, beside the brief, and never later — the app decides
how it will grade you before it has seen a line of your code. See
docs/decisions.md D6.
"""

from __future__ import annotations

import random

from fcg.generator.seeds import load_pool
from fcg.models import Brief, Client, Feature, RubricItem

# How many of the scenario's features the client asks for. Difficulty will scale
# this later (requirements R1.6, [day-2]); for now every brief asks for four.
FEATURE_COUNT = {"easy": 3, "medium": 4, "hard": 6}
CONSTRAINT_COUNT = {"easy": 1, "medium": 2, "hard": 3}

# Always asked for, never sampled — see generate_brief.
MANDATORY_FEATURES = {"product_grid"}

# Rubric weights, summing to 100.
#
# The exact checks (does the file exist, did they use our content) carry the
# single largest weights, and heuristic feature detection carries less — we are
# more sure of the former than the latter, and the score should lean on what we
# actually know. See docs/decisions.md D2.
W_README = 5
W_ENTRY_POINT = 10
W_SEED_DATA = 35
W_PER_FEATURE = 8
W_QUALITY = 18


def generate_brief(
    rng: random.Random,
    client: Client,
    difficulty: str = "medium",
    scenario: str = "bakery",
) -> Brief:
    """Pick what this client wants built and why.

    The ask and context prose below is deliberately domain-neutral — it reads the
    same whether the client is a bakery or a deli, because it only ever talks about
    "what we sell" and "the phone", never "bread". Everything scenario-specific
    (products, features, constraints, the pain being solved) comes from the pool.
    """
    pool = load_pool(scenario)

    n_features = FEATURE_COUNT.get(difficulty, 4)
    n_constraints = CONSTRAINT_COUNT.get(difficulty, 2)

    # The product listing is always required. It is the entire point of the page,
    # and 35 points ride on the client's products appearing in the build — a brief
    # that didn't ask for it would be grading something it never requested. The
    # rest of the features are sampled.
    mandatory = [f for f in pool["features"] if f["id"] in MANDATORY_FEATURES]
    optional = [f for f in pool["features"] if f["id"] not in MANDATORY_FEATURES]
    chosen = mandatory + rng.sample(optional, max(n_features - len(mandatory), 0))

    features = [
        Feature(
            id=f["id"],
            name=f["name"],
            description=f["description"],
            signals=list(f["signals"]),
        )
        for f in chosen
    ]
    constraints = rng.sample(pool["constraints"], n_constraints)
    pain = rng.choice(pool["pains"])

    ask = (
        f"We need a single page — one page, not a whole site — that people can "
        f"look at before they come in or before they call. Right now {pain}, and "
        f"we think most of it goes away if what we sell is just... on the internet, "
        f"where people can read it.\n\n"
        f"We've attached everything we sell as a spreadsheet. That's the real list, "
        f"straight off our till, so please build the page from that rather than "
        f"making something up. If it's in the file it should be on the page."
    )

    context = (
        f"{client.contact_name} ({client.contact_role}) got in touch after a "
        f"particularly bad Saturday. They have no developer, no designer, and no "
        f"appetite for a big project — they want one page that works, and they want "
        f"to stop answering the phone quite so much."
    )

    return Brief(
        ask=ask,
        context=context,
        features=features,
        required_files=["README.md"],
        constraints=constraints,
    )


def generate_rubric(rng: random.Random, brief: Brief) -> list[RubricItem]:
    """Derive the scorecard from the brief, so the two cannot drift apart.

    Every item traces back to something the brief actually asked for: the files it
    demanded, the content it attached, the features it listed.
    """
    rubric: list[RubricItem] = [
        RubricItem(
            id="r_readme",
            criterion="README.md is present",
            weight=W_README,
            check="required_files",
            exact=True,
            target="README.md",
        ),
        RubricItem(
            id="r_entry",
            criterion="The project has a page to look at (an entry point)",
            weight=W_ENTRY_POINT,
            check="entry_point",
            exact=True,
        ),
        RubricItem(
            id="r_seed_data",
            criterion="The build uses the client's actual products, not invented ones",
            weight=W_SEED_DATA,
            check="seed_data_used",
            exact=True,
        ),
    ]

    rubric += [
        RubricItem(
            id=f"r_feat_{f.id}",
            criterion=f"Required feature: {f.name}",
            weight=W_PER_FEATURE,
            check="feature_present",
            exact=False,
            target=f.id,
        )
        for f in brief.features
    ]

    rubric.append(
        RubricItem(
            id="r_quality",
            criterion="Basic front-end quality (mobile viewport, alt text, semantics, README)",
            weight=W_QUALITY,
            check="quality_signals",
            exact=False,
        )
    )
    return rubric

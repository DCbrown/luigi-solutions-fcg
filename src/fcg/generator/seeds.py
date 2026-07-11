"""Load the seed pools the generator draws from.

Cached, because generation is meant to complete in under two seconds
(docs/requirements.md R5.3) and re-reading JSON per project is silly.
"""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from fcg.storage import SEEDS


@lru_cache(maxsize=16)
def load_pool(scenario: str) -> dict[str, Any]:
    """Read a scenario's seed pools, e.g. 'bakery'."""
    path = SEEDS / f"{scenario}.json"
    if not path.exists():
        raise FileNotFoundError(f"No seed pool for scenario {scenario!r} at {path}")
    return json.loads(path.read_text())


def available_scenarios() -> list[str]:
    """Every scenario slug with a seed pool on disk, sorted."""
    return sorted(p.stem for p in SEEDS.glob("*.json"))

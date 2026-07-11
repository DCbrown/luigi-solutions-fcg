"""Every scenario pool on disk must generate a complete, gradeable project.

These run against whatever JSON is in data/seeds/ — adding a scenario means
passing this file, not editing it.
"""

import pytest

from fcg.generator import generate_project
from fcg.generator.dataset import COLUMNS
from fcg.generator.seeds import available_scenarios, load_pool

SCENARIOS = available_scenarios()


def test_the_new_scenarios_exist():
    for expected in [
        "bakery",
        "deli",
        "coffee-shop",
        "restaurant",
        "digital-agency",
        "photography",
        "event-planning",
    ]:
        assert expected in SCENARIOS


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_pool_is_deep_enough_for_every_difficulty(scenario):
    pool = load_pool(scenario)
    # hard briefs sample 5 optional features and 3 constraints
    assert len(pool["features"]) >= 6
    assert len(pool["constraints"]) >= 3
    # medium datasets need 11 normal products after the 3 awkward rows
    assert len(pool["products"]) >= 11
    assert len(pool["awkward"]) >= 3
    feature_ids = [f["id"] for f in pool["features"]]
    assert "product_grid" in feature_ids, "the mandatory feature must exist"
    assert len(feature_ids) == len(set(feature_ids))


@pytest.mark.parametrize("scenario", SCENARIOS)
@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_every_scenario_generates_a_complete_project(scenario, difficulty):
    project, df = generate_project(seed=4471, difficulty=difficulty, scenario=scenario)

    assert project.id == f"{scenario}-4471"
    assert project.scenario == scenario
    assert {f.id for f in project.brief.features} >= {"product_grid"}
    # The grader normalises by total weight, so the sum need not be 100 —
    # it's exactly 100 only at medium (4 features × 8 + 68 fixed).
    assert sum(item.weight for item in project.rubric) > 0
    if difficulty == "medium":
        assert sum(item.weight for item in project.rubric) == 100

    assert list(df.columns) == COLUMNS
    assert len(df) >= 10
    assert (~df["available"]).any(), "each dataset ships one sold-out row"
    assert (df["description"] == "").any(), "each dataset ships one blank description"
    assert df["name"].str.len().max() > 60, "each dataset ships one awkwardly long name"


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_generation_is_reproducible_per_scenario(scenario):
    p1, d1 = generate_project(seed=99, scenario=scenario)
    p2, d2 = generate_project(seed=99, scenario=scenario)
    assert p1.client.name == p2.client.name
    assert p1.brief == p2.brief
    assert d1.equals(d2)

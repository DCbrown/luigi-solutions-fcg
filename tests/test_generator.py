"""Generator tests. The reproducibility one is the load-bearing test in the repo."""

from dataclasses import replace
from datetime import date

import pandas as pd
import pytest

from fcg.generator import generate_project
from fcg.generator.brief import MANDATORY_FEATURES


@pytest.mark.parametrize("scenario", ["bakery", "deli"])
def test_same_seed_reproduces_the_same_project(scenario):
    """quality.md Q2 — the property the whole app rests on.

    If a seed doesn't reproduce, projects aren't shareable, scores aren't
    comparable, and no generator bug can be reproduced from a report.

    `created_at` is excluded deliberately: it's provenance, not generated content,
    and it's the only field allowed to differ between two runs of a seed.

    Parametrized over scenario: the guarantee has to hold for every scenario, and
    the bakery case doubles as proof the scenario refactor left it untouched.
    """
    p1, d1 = generate_project(seed=4471, scenario=scenario)
    p2, d2 = generate_project(seed=4471, scenario=scenario)

    fixed = date(2000, 1, 1)
    assert replace(p1, created_at=fixed) == replace(p2, created_at=fixed)
    pd.testing.assert_frame_equal(d1, d2)


def test_different_seeds_produce_different_projects():
    p1, _ = generate_project(seed=1)
    p2, _ = generate_project(seed=2)
    assert p1.client.name != p2.client.name or p1.brief.features != p2.brief.features


def test_a_second_scenario_flows_through_and_reads_like_itself():
    """The walking skeleton's whole point: a non-bakery scenario runs the entire
    generator end to end and leaks no bakery-specific prose or products."""
    project, data = generate_project(seed=4471, scenario="deli")

    assert project.scenario == "deli"
    assert project.id == "deli-4471"
    assert project.client.industry == "food & drink"
    assert "baking" not in project.client.background.lower()
    assert "deli counter" in project.client.background.lower()

    # Same seed, different scenario -> a different company and the deli's own SKUs.
    bakery, _ = generate_project(seed=4471, scenario="bakery")
    assert project.client.name != bakery.client.name
    assert data["sku"].str.startswith("DL").all()


@pytest.mark.parametrize("scenario", ["bakery", "deli"])
def test_the_product_listing_is_always_required(scenario):
    """35 points ride on the client's products appearing in the build.

    A brief that didn't ask for a product listing would be grading the user on
    something it never requested.
    """
    for seed in range(25):
        project, _ = generate_project(seed=seed, scenario=scenario)
        ids = {f.id for f in project.brief.features}
        assert MANDATORY_FEATURES <= ids, f"{scenario} seed {seed} dropped the product listing"


def test_every_rubric_item_traces_back_to_the_brief():
    """The rubric may only grade things the brief actually asked for (D6)."""
    project, _ = generate_project(seed=99)
    feature_ids = {f.id for f in project.brief.features}

    for item in project.rubric:
        if item.check == "feature_present":
            assert item.target in feature_ids
        if item.check == "required_files":
            assert item.target in project.brief.required_files


def test_rubric_weights_sum_to_100_at_medium():
    project, _ = generate_project(seed=7, difficulty="medium")
    assert sum(r.weight for r in project.rubric) == 100


def test_exact_checks_outweigh_heuristic_ones():
    """decisions.md D2 — the score must lean on what we actually know."""
    project, _ = generate_project(seed=7, difficulty="medium")
    exact = sum(r.weight for r in project.rubric if r.exact)
    heuristic = sum(r.weight for r in project.rubric if not r.exact)
    assert exact >= heuristic


@pytest.mark.parametrize("scenario", ["bakery", "deli"])
@pytest.mark.parametrize("seed", range(10))
def test_seed_data_always_contains_the_awkward_rows(seed, scenario):
    """requirements.md R1.4 — real content, not the tidy content they'd invent.

    Awkward rows live in the pool now, so every scenario has to carry its own.
    """
    _, data = generate_project(seed=seed, scenario=scenario)

    assert data["name"].str.len().max() > 40, "no name long enough to break a card"
    assert data["description"].isna().any() or (data["description"] == "").any()
    assert not data["available"].all(), "nothing unavailable — too tidy"
    assert data["name"].str.contains("è|é|&").any(), "no character needing escaping"

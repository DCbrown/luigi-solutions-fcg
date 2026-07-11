"""Generator tests. The reproducibility one is the load-bearing test in the repo."""

from dataclasses import replace
from datetime import date

import pandas as pd
import pytest

from fcg.generator import generate_project
from fcg.generator.brief import MANDATORY_FEATURES


def test_same_seed_reproduces_the_same_project():
    """quality.md Q2 — the property the whole app rests on.

    If a seed doesn't reproduce, projects aren't shareable, scores aren't
    comparable, and no generator bug can be reproduced from a report.

    `created_at` is excluded deliberately: it's provenance, not generated content,
    and it's the only field allowed to differ between two runs of a seed.
    """
    p1, d1 = generate_project(seed=4471)
    p2, d2 = generate_project(seed=4471)

    fixed = date(2000, 1, 1)
    assert replace(p1, created_at=fixed) == replace(p2, created_at=fixed)
    pd.testing.assert_frame_equal(d1, d2)


def test_different_seeds_produce_different_projects():
    p1, _ = generate_project(seed=1)
    p2, _ = generate_project(seed=2)
    assert p1.client.name != p2.client.name or p1.brief.features != p2.brief.features


def test_the_product_listing_is_always_required():
    """35 points ride on the client's products appearing in the build.

    A brief that didn't ask for a product listing would be grading the user on
    something it never requested.
    """
    for seed in range(25):
        project, _ = generate_project(seed=seed)
        ids = {f.id for f in project.brief.features}
        assert MANDATORY_FEATURES <= ids, f"seed {seed} dropped the product listing"


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


@pytest.mark.parametrize("seed", range(10))
def test_seed_data_always_contains_the_awkward_rows(seed):
    """requirements.md R1.4 — real content, not the tidy content they'd invent."""
    _, data = generate_project(seed=seed)

    assert data["name"].str.len().max() > 40, "no name long enough to break a card"
    assert data["description"].isna().any() or (data["description"] == "").any()
    assert not data["available"].all(), "nothing unavailable — too tidy"
    assert data["name"].str.contains("è|é|&").any(), "no character needing escaping"

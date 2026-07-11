"""The projects list stores nothing — so rebuilding from an id must be exact.

recent_generations() talks to live Supabase and isn't tested here; what must
hold forever is that a project_id round-trips through parse + regenerate
(that's D1 carrying the whole feature).
"""

import pytest

from history import parse_project_id, rebuild


def test_parse_splits_scenario_and_seed():
    assert parse_project_id("bakery-4471") == ("bakery", 4471)
    assert parse_project_id("deli-4471") == ("deli", 4471)


def test_parse_survives_a_hyphenated_scenario():
    assert parse_project_id("farm-shop-12") == ("farm-shop", 12)


def test_parse_rejects_garbage():
    with pytest.raises(ValueError):
        parse_project_id("4471")
    with pytest.raises(ValueError):
        parse_project_id("bakery-cake")


def test_rebuild_returns_the_identical_project():
    p1, d1 = rebuild("bakery-4471")
    p2, d2 = rebuild("bakery-4471")
    assert p1.id == p2.id == "bakery-4471"
    assert p1.client.name == p2.client.name
    assert p1.brief == p2.brief
    assert d1.equals(d2)


def test_rebuild_respects_the_scenario():
    project, _ = rebuild("deli-4471")
    assert project.scenario == "deli"
    assert project.id == "deli-4471"

"""Storage roundtrip tests.

These exist because a bug here is invisible: everything works in one session and
breaks only after a restart, when the project comes back off disk with the wrong
types.
"""

import pandas as pd
import pytest

from fcg.generator import generate_project
from fcg.scoring import grade_submission
from fcg.storage import load_project, load_seed_data, save_project


@pytest.fixture
def saved():
    project, data = generate_project(seed=4471)
    save_project(project, data)
    return project, data


def test_project_survives_the_roundtrip(saved):
    project, _ = saved
    assert load_project(project.id) == project


def test_seed_data_survives_the_roundtrip(saved):
    project, data = saved
    pd.testing.assert_frame_equal(data, load_seed_data(project.id))


def test_an_empty_description_reloads_as_empty_not_missing(saved):
    """The client left the field blank. That's content, not a missing value."""
    project, _ = saved
    reloaded = load_seed_data(project.id)

    assert not reloaded["description"].isna().any()
    assert (reloaded["description"] == "").any()


def test_available_reloads_as_bool_not_string(saved):
    """CSV has no booleans, and "False" is a truthy string.

    Get this wrong and a reloaded project quietly marks every product available —
    then demands the user display an item the client marked as sold out.
    """
    project, _ = saved
    reloaded = load_seed_data(project.id)

    assert reloaded["available"].dtype == bool
    assert not reloaded["available"].all(), "the sold-out product came back available"


def test_scoring_a_reloaded_project_matches_scoring_a_fresh_one(saved):
    """The bug this whole file exists for: same work, different score after a restart."""
    from tests.test_scoring import _good_submission

    project, data = saved
    reloaded_project = load_project(project.id)
    reloaded_data = load_seed_data(project.id)

    sub = _good_submission(project, data)

    fresh = grade_submission(project, sub, data)
    after_restart = grade_submission(reloaded_project, sub, reloaded_data)

    assert fresh.total == after_restart.total

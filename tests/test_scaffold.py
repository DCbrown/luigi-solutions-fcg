"""Smoke tests — the package imports and the domain objects hold together."""

from fcg.models import Client, Feature, RubricItem, Submission
from fcg.scoring.checks import CHECKS, check


def test_package_imports():
    import fcg

    assert fcg.__version__


def test_client_is_constructible():
    c = Client(
        name="Fernwood Bakery",
        industry="food & drink",
        size="small business",
        contact_name="Dana Ruiz",
        contact_role="Owner",
        background="A two-location bakery that still takes orders by phone.",
    )
    assert c.name == "Fernwood Bakery"


def test_feature_carries_signals_for_the_heuristic_check():
    f = Feature(
        id="f1",
        name="contact form",
        description="People need to be able to reach us without calling.",
        signals=["<form", "ContactForm", "onSubmit"],
    )
    assert "ContactForm" in f.signals


def test_rubric_item_records_whether_it_is_exact():
    exact = RubricItem(
        id="r1", criterion="README.md present", weight=5, check="required_files",
        exact=True, target="README.md",
    )
    heuristic = RubricItem(
        id="r2", criterion="Contact form present", weight=10,
        check="feature_present", exact=False, target="f1",
    )
    assert exact.exact and not heuristic.exact


def test_submission_concatenates_source_for_content_checks():
    s = Submission(
        project_id="p1",
        repo_url="https://github.com/x/y",
        files={"index.html": "<h1>Sourdough</h1>", "app.js": "const x = 1;"},
    )
    assert "Sourdough" in s.all_source()
    assert "const x = 1;" in s.all_source()


def test_check_registry_registers_by_name():
    @check("dummy")
    def _dummy(submission, project):
        return 1.0, "ok"

    assert "dummy" in CHECKS
    assert CHECKS["dummy"](None, None) == (1.0, "ok")
    del CHECKS["dummy"]

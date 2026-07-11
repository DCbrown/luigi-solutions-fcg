"""Scorer tests.

The one that matters is `test_good_submission_outscores_bad_one`. If a scorer
can't tell those apart it's decoration, however tidy its internals are.
"""

import pytest

from fcg.generator import generate_project
from fcg.models import Submission
from fcg.scoring import grade_submission


@pytest.fixture
def project_and_data():
    return generate_project(seed=4471, difficulty="medium")


def _good_submission(project, data) -> Submission:
    """What a diligent user hands back: their content, their features, a README."""
    products = "\n".join(
        f'<li class="product"><h3>{row["name"]}</h3>'
        f'<p>{row["description"]}</p>'
        f'<span class="price">£{row["price"]}</span>'
        f'<span class="allergens">Contains: {row["allergens"]}</span></li>'
        for _, row in data.iterrows()
    )
    html = f"""<!doctype html>
<html><head>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{project.client.name}</title>
</head>
<body>
  <header><nav><a href="#menu">Menu</a><a href="#contact">Contact</a></nav></header>
  <main>
    <section id="hours"><h2>Opening hours</h2>
      <p>Tuesday to Sunday, 7am-4pm. Closed Monday.</p></section>
    <section id="menu">
      <select id="category-filter" onchange="filterCategory()">
        <option>All</option><option>Bread</option><option>Cake</option>
      </select>
      <ul class="product-grid">{products}</ul>
    </section>
    <section id="contact">
      <form onsubmit="handleSubmit(event)">
        <label for="email">Email</label>
        <input type="email" id="email">
        <textarea name="order"></textarea>
        <button>Send</button>
      </form>
    </section>
  </main>
  <footer><img src="shop.jpg" alt="The shopfront"></footer>
</body></html>"""

    return Submission(
        project_id=project.id,
        repo_url="https://github.com/test/good",
        files={
            "index.html": html,
            "style.css": ".product-grid { display: grid; }",
            "README.md": "# " + project.client.name + "\n\n"
            "A single-page order site built from the client's product list. "
            "Vanilla HTML and CSS, no build step. Open index.html.\n",
        },
    )


def _bad_submission(project) -> Submission:
    """A generic template with invented products and nothing the client asked for."""
    return Submission(
        project_id=project.id,
        repo_url="https://github.com/test/bad",
        files={
            "index.html": (
                "<html><body><div><div>Welcome to my bakery</div>"
                "<div>Bread - $3</div><div>Cake - $4</div>"
                "<img src='hero.jpg'></div></body></html>"
            ),
        },
    )


def test_good_submission_outscores_bad_one(project_and_data):
    """If this fails, the scorer is decoration."""
    project, data = project_and_data

    good = grade_submission(project, _good_submission(project, data), data)
    bad = grade_submission(project, _bad_submission(project), data)

    assert good.total > bad.total
    assert good.total >= 85, f"a diligent build only scored {good.total}"
    assert bad.total <= 40, f"a lazy build got away with {bad.total}"


def test_score_is_bounded(project_and_data):
    project, data = project_and_data
    for sub in (_good_submission(project, data), _bad_submission(project)):
        score = grade_submission(project, sub, data)
        assert 0 <= score.total <= 100


def test_empty_submission_scores_zero_without_crashing(project_and_data):
    project, data = project_and_data
    empty = Submission(project_id=project.id, repo_url="https://github.com/t/e", files={})

    score = grade_submission(project, empty, data)
    assert score.total == 0
    assert len(score.items) == len(project.rubric)


def test_inventing_your_own_products_costs_the_heaviest_item(project_and_data):
    """The brief was loudest about this, so the rubric should be too."""
    project, data = project_and_data

    sub = _good_submission(project, data)
    for name in data[data["available"]]["name"].tolist()[:4]:
        sub.files["index.html"] = sub.files["index.html"].replace(name, "Generic Bread")

    score = grade_submission(project, sub, data)
    item = next(s for s in score.items if s.rubric_id == "r_seed_data")
    assert item.points < item.max_points


def test_hiding_an_unavailable_product_is_not_punished(project_and_data):
    """The data marks one item unavailable. Hiding it is good judgment, not a miss.

    A scorer that docks marks for a defensible reading of the brief teaches the
    user to stop thinking, which is the opposite of the point.
    """
    project, data = project_and_data
    sub = _good_submission(project, data)

    for name in data[~data["available"]]["name"].tolist():
        sub.files["index.html"] = sub.files["index.html"].replace(name, "")

    score = grade_submission(project, sub, data)
    item = next(s for s in score.items if s.rubric_id == "r_seed_data")
    assert item.points == item.max_points, "punished for hiding an unavailable product"


def test_html_escaping_a_product_name_still_counts(project_and_data):
    """`&amp;` is how a *correct* build writes "&". Matching raw source would fail it.

    An "exact" check that throws false negatives is worse than a heuristic one that
    admits it might — see quality.md Q4.
    """
    project, data = project_and_data
    sub = _good_submission(project, data)

    sub.files["index.html"] = sub.files["index.html"].replace("&", "&amp;")

    score = grade_submission(project, sub, data)
    item = next(s for s in score.items if s.rubric_id == "r_seed_data")
    assert item.points == item.max_points, "escaped entities broke an exact check"


def test_a_word_signal_does_not_match_inside_another_word():
    """"Mon" must not fire on "money". False credit discredits the card too."""
    from fcg.scoring.checks import _signal_matches

    assert not _signal_matches("Mon", "const money = 1; // common case")
    assert not _signal_matches("nav", "function navigate() {}")
    assert _signal_matches("Mon", "<td>Mon</td>")
    assert _signal_matches("filter", "let filtered = items.filter(x => x)")

    # Markup and code signals still match as substrings — that's how they appear.
    assert _signal_matches("<form", '<form onsubmit="go()">')
    assert _signal_matches("products.map", "{products.map(p => <Card/>)}")


def test_case_variants_of_one_signal_are_not_two_pieces_of_evidence(project_and_data):
    """The pools carry "closed"/"Closed". Counting both fakes a confident match."""
    project, data = project_and_data
    hours = next((f for f in project.brief.features if f.id == "opening_hours"), None)
    if hours is None:
        pytest.skip("this seed's brief doesn't ask for opening hours")

    sub = Submission(
        project_id=project.id,
        repo_url="https://github.com/t/x",
        files={"index.html": "<p>closed</p>"},  # one real signal, two pool variants
    )
    score = grade_submission(project, sub, data)
    item = next(s for s in score.items if s.rubric_id == "r_feat_opening_hours")

    assert item.points < item.max_points, "one match was inflated into a confident yes"


def test_every_rubric_item_gets_feedback(project_and_data):
    """A number with no explanation is not a scorecard."""
    project, data = project_and_data
    score = grade_submission(project, _bad_submission(project), data)

    for item in score.items:
        assert item.feedback.strip(), f"{item.rubric_id} scored silently"


def test_heuristic_failures_never_assert_the_user_didnt_build_it(project_and_data):
    """quality.md Q4 — we report evidence, not fact, when we're guessing.

    A scorer that confidently tells you you didn't build the thing you definitely
    built poisons trust in every other number on the card.
    """
    project, data = project_and_data
    score = grade_submission(project, _bad_submission(project), data)

    heuristic_ids = {r.id for r in project.rubric if not r.exact}
    for item in score.items:
        if item.rubric_id in heuristic_ids and item.points < item.max_points:
            text = item.feedback.lower()
            assert "no evidence" in text or "missing:" in text or "possible" in text, (
                f"{item.rubric_id} stated as fact what it only guessed: {item.feedback!r}"
            )

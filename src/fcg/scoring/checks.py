"""The checks a rubric item can point at.

Every check has the same shape — `CheckContext -> (fraction, feedback)` — so the
grader dispatches by name and a new check can be added without touching it. That's
what lets an LLM judge drop in later as just another check (D3); it will need more
than a string search, and the context object is what gives it room to.

Two kinds of check, and the difference is the whole ethic of the scorer:

  **Exact** — the file is there or it isn't; the client's product names are in the
  source or they aren't. We *know*. Say so plainly: "No README.md found."

  **Heuristic** — is that JSX a contact form? We are guessing, and on a framework
  project we will sometimes be wrong (D2). So we report *evidence*, never fact:
  "No evidence of a contact form found."

Confidently telling someone they didn't build the thing they definitely built is
worse than not checking at all — they stop trusting every other number on the
card. See docs/quality.md Q4.
"""

from __future__ import annotations

import html
import re
from collections.abc import Callable
from dataclasses import dataclass

import pandas as pd

from fcg.models import Feature, Project, RubricItem, Submission


@dataclass
class CheckContext:
    """Everything a check is allowed to look at."""

    submission: Submission
    project: Project
    seed_data: pd.DataFrame
    item: RubricItem  # the rubric line being scored; `item.target` says what to look for

    def feature(self) -> Feature | None:
        """The Feature this rubric item points at, if it points at one."""
        return next(
            (f for f in self.project.brief.features if f.id == self.item.target), None
        )


CheckFn = Callable[[CheckContext], tuple[float, str]]

CHECKS: dict[str, CheckFn] = {}


def check(name: str) -> Callable[[CheckFn], CheckFn]:
    """Register a check under `name` so a RubricItem can reference it."""

    def register(fn: CheckFn) -> CheckFn:
        CHECKS[name] = fn
        return fn

    return register


# Anything that could reasonably be "the page". Deliberately broad: the user may
# build in any stack (D2), and demanding index.html would quietly punish everyone
# who reached for Next.js.
ENTRY_POINTS = (
    "index.html", "index.htm", "app.vue", "app.svelte", "app.jsx", "app.tsx",
    "page.tsx", "page.jsx", "index.jsx", "index.tsx", "app.js",
)


# --------------------------------------------------------------------------
# Exact checks — we know the answer, so we say it plainly
# --------------------------------------------------------------------------


@check("required_files")
def required_files(ctx: CheckContext) -> tuple[float, str]:
    """Did they hand back the files the brief demanded?"""
    wanted = ctx.project.brief.required_files
    present = {p.split("/")[-1].lower() for p in ctx.submission.files}

    missing = [w for w in wanted if w.lower() not in present]
    if not missing:
        return 1.0, f"Found {', '.join(wanted)}."

    return (len(wanted) - len(missing)) / len(wanted), f"No {' or '.join(missing)} in the repo."


@check("entry_point")
def entry_point(ctx: CheckContext) -> tuple[float, str]:
    """Is there actually a page to look at?"""
    for path in ctx.submission.files:
        if path.split("/")[-1].lower() in ENTRY_POINTS:
            return 1.0, f"Found an entry point: `{path}`."

    return 0.0, (
        "Couldn't find an entry point — no index.html, and no App/page component. "
        "The client asked for a page they could look at."
    )


def _normalise(text: str) -> str:
    """Fold the source into something a product name can honestly be matched against.

    `&amp;` and `&egrave;` are how a *correct* build writes "&" and "è". Matching
    raw source would fail "Cheese & Onion Pasty" on a page that escaped it properly
    — a false negative in a check the user is told is exact, which is precisely the
    thing docs/quality.md Q4 says destroys trust in the whole card.
    """
    return re.sub(r"\s+", " ", html.unescape(text)).casefold()


@check("seed_data_used")
def seed_data_used(ctx: CheckContext) -> tuple[float, str]:
    """Did they build from the client's list, or invent their own products?

    Exact, and stack-independent: whatever framework you used, if the page shows
    "Country Sourdough" then that string is *somewhere* in the source. This is the
    heaviest item on the rubric, and the brief was loudest about it.

    Only the **available** products are required. The seed data deliberately marks
    one item unavailable, and hiding it is a perfectly reasonable reading of the
    brief — a scorer that docked marks for that would be punishing good judgment.
    Showing it anyway is fine too; we simply don't ask.
    """
    data = ctx.seed_data
    required = data[data["available"]] if "available" in data else data
    names = [str(n) for n in required["name"].tolist()]
    if not names:
        return 0.0, "Internal: the project has no seed data to check against."

    source = _normalise(ctx.submission.all_source())
    found = [n for n in names if _normalise(n) in source]
    fraction = len(found) / len(names)

    if fraction == 1.0:
        return 1.0, f"All {len(names)} of the client's available products are in the build."
    if not found:
        return 0.0, (
            f"None of the client's {len(names)} products appear anywhere in the "
            "source. The brief was explicit — build the page from their list, not "
            "from invented products."
        )

    missing = [n for n in names if _normalise(n) not in source]
    return fraction, (
        f"{len(found)} of {len(names)} of the client's products made it into the "
        f"build. Missing, for example: “{missing[0]}”."
    )


# --------------------------------------------------------------------------
# Heuristic checks — we are looking for evidence, and we can be wrong
# --------------------------------------------------------------------------


def _signal_matches(signal: str, source: str) -> bool:
    """Look for one feature signal in the source, without inventing a sighting.

    Word signals ("filter", "allergen") are matched on word boundaries. A bare
    substring search finds "filter" inside "filterable" — fine — but also finds
    "nav" inside "navigate" and "Mon" inside "money", and then cheerfully awards
    points for an opening-hours section nobody wrote.

    A check that hands out credit at random discredits the scorecard just as
    thoroughly as one that withholds it unfairly. So: markup and code signals
    ("<form", "onSubmit", "products.map") stay substring matches, because that's
    how they appear; plain words get boundaries.
    """
    if re.fullmatch(r"[A-Za-z]+", signal):
        return re.search(rf"\b{re.escape(signal)}\b", source, re.IGNORECASE) is not None
    return signal.casefold() in source.casefold()


@check("feature_present")
def feature_present(ctx: CheckContext) -> tuple[float, str]:
    """Is there any sign they built this feature?

    Grep with domain knowledge, not a DOM query — see D2 for why it can't be
    better than this until we check the rendered page instead of the source.
    """
    feature = ctx.feature()
    if feature is None:
        return 0.0, "Internal: rubric pointed at a feature the brief doesn't have."

    source = ctx.submission.all_source()

    # Dedupe case-insensitively first. The signal pools carry variants like
    # "closed"/"Closed" for readability, and counting both would manufacture a
    # second, independent-looking piece of evidence out of a single match.
    seen: dict[str, str] = {}
    for s in feature.signals:
        seen.setdefault(s.casefold(), s)

    hits = [s for s in seen.values() if _signal_matches(s, source)]

    if not hits:
        return 0.0, (
            f"No evidence of {feature.name} found in the source. If you did build "
            "it, it may simply not look like anything I know how to spot."
        )

    # Two independent signals is a confident yes. One is a maybe — and the score
    # should say "maybe" rather than round a guess up into a promise.
    if len(hits) >= 2:
        return 1.0, f"Found {feature.name} — matched `{hits[0]}` and `{hits[1]}`."

    return 0.6, (
        f"Possible {feature.name}, but only one weak signal (`{hits[0]}`). "
        "Partial credit — I'm genuinely not sure either way."
    )


@check("quality_signals")
def quality_signals(ctx: CheckContext) -> tuple[float, str]:
    """Cheap static heuristics that map to real code-review comments."""
    if not ctx.submission.files:
        # Guard against vacuous credit: an empty repo has no <img> without alt
        # text, and would otherwise be rewarded for it.
        return 0.0, "Nothing to check — the repo has no source files in it."

    source = ctx.submission.all_source()
    lowered = source.lower()

    signals: list[tuple[bool, str, str]] = [
        (
            'name="viewport"' in lowered or "name='viewport'" in lowered,
            "responsive viewport meta tag",
            "no viewport meta tag, and the client said it had to work on a phone",
        ),
        (
            not re.search(r"<img(?![^>]*\balt\s*=)[^>]*>", source, re.IGNORECASE),
            "images have alt text",
            "at least one <img> has no alt attribute",
        ),
        (
            any(t in lowered for t in ("<main", "<header", "<section", "<nav", "<footer", "<article")),
            "semantic HTML",
            "no semantic elements (<main>, <header>, <section>) — it's all divs",
        ),
        (
            _readme_has_content(ctx.submission),
            "a README with something in it",
            "the README is empty or nearly so",
        ),
    ]

    good = [msg for ok, msg, _ in signals if ok]
    bad = [msg for ok, _, msg in signals if not ok]

    parts = []
    if good:
        parts.append("Good: " + "; ".join(good) + ".")
    if bad:
        parts.append("Missing: " + "; ".join(bad) + ".")

    return len(good) / len(signals), " ".join(parts)


def _readme_has_content(sub: Submission) -> bool:
    """A README that exists but says nothing is not a README."""
    for path, text in sub.files.items():
        if path.split("/")[-1].lower() == "readme.md":
            return len(text.strip()) > 80
    return False

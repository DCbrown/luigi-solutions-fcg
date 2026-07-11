"""Core domain objects shared by the generator, the UI, and the scorer.

These are the contract between the three halves of the app. If you're passing a
dict between modules, add a dataclass here instead — see docs/quality.md Q3.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class Client:
    """The fictional company commissioning the build."""

    name: str
    industry: str
    size: str  # "startup" | "small business" | "mid-market"
    contact_name: str
    contact_role: str
    background: str  # a paragraph that reads like a real company


@dataclass
class Feature:
    """One thing the brief requires the page to have.

    `signals` is what the scorer hunts for across the repo's source: HTML
    elements, JSX component names, attribute patterns, handler names. Because the
    user may build in any stack, this is deliberately a bundle of guesses rather
    than one exact query — see docs/decisions.md D2.
    """

    id: str
    name: str  # "contact form"
    description: str  # what the client actually asked for, in their words
    signals: list[str] = field(default_factory=list)


@dataclass
class RubricItem:
    """One scored line on the scorecard.

    `exact` separates the checks we *know* (the file is there or it isn't) from
    the ones we're *guessing at* (is that JSX a contact form?). The wording of the
    feedback depends on it — see docs/quality.md Q4.
    """

    id: str
    criterion: str
    weight: float
    check: str  # a key in fcg.scoring.checks.CHECKS
    exact: bool
    target: str = ""  # what the check looks for: a filename, a feature id, ...


@dataclass
class Brief:
    """The client's ask. The spine of the project.

    The seed data is generated to fit it and the rubric is derived from it, so
    neither can drift away from what the client actually asked for.
    """

    ask: str  # the client's own words
    context: str  # why they need it
    features: list[Feature]  # 3-6 things the page must have
    required_files: list[str]  # at minimum an entry file and a README
    constraints: list[str]  # arbitrary-but-plausible client rules


@dataclass
class Project:
    """A single generated engagement. A pure function of (seed, difficulty).

    `created_at` is the one exception, and deliberately so: it's provenance, not
    generated content, and it's the only field a re-run of the same seed is
    allowed to differ on. The reproducibility test (docs/quality.md Q2) compares
    everything else.
    """

    id: str
    seed: int
    difficulty: str  # "easy" | "medium" | "hard"
    scenario: str  # "bakery", "gym", "salon", ...
    client: Client
    brief: Brief
    rubric: list[RubricItem]  # hidden from the user until they submit (D6)
    created_at: date = field(default_factory=date.today)
    seed_data_file: str = "seed_data.csv"


@dataclass
class Submission:
    """A cloned repo, read as text. Never executed — see docs/quality.md Q5."""

    project_id: str
    repo_url: str
    # Relative path -> file contents. Text files only; binaries are skipped.
    files: dict[str, str] = field(default_factory=dict)

    def all_source(self) -> str:
        """Every file's text, concatenated. What the content checks search."""
        return "\n".join(self.files.values())


@dataclass
class ScoredItem:
    """The result of running one rubric item's check."""

    rubric_id: str
    criterion: str
    points: float
    max_points: float
    feedback: str


@dataclass
class Score:
    """The scorecard. 0-100, with a line of feedback per criterion."""

    project_id: str
    total: float  # out of 100
    items: list[ScoredItem] = field(default_factory=list)

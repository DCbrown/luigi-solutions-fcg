"""Walk the rubric, run each check, total the weights into a score out of 100."""

from __future__ import annotations

import pandas as pd

from fcg.models import Project, Score, ScoredItem, Submission
from fcg.scoring.checks import CHECKS, CheckContext


def grade_submission(
    project: Project, submission: Submission, seed_data: pd.DataFrame
) -> Score:
    """Score one submission against the rubric written with its brief.

    The grader knows nothing about what any individual check does — it looks the
    check up by name, hands it a context, and turns the fraction it returns into
    weighted points. That ignorance is deliberate: it's what keeps this function
    stable when new checks (including an LLM judge) are added later (D3).

    Weights are normalised to 100, so difficulty can change the number of rubric
    items later without the score changing meaning.
    """
    total_weight = sum(item.weight for item in project.rubric)
    if total_weight == 0:
        return Score(project_id=project.id, total=0.0)

    scored: list[ScoredItem] = []

    for item in project.rubric:
        check_fn = CHECKS.get(item.check)
        max_points = 100 * item.weight / total_weight

        if check_fn is None:
            # A rubric that names a check we don't have is a bug in us, not in the
            # user's work — so it costs them nothing.
            scored.append(
                ScoredItem(
                    rubric_id=item.id,
                    criterion=item.criterion,
                    points=max_points,
                    max_points=max_points,
                    feedback=f"Not scored — no check named {item.check!r}. Free marks.",
                )
            )
            continue

        ctx = CheckContext(
            submission=submission, project=project, seed_data=seed_data, item=item
        )
        fraction, feedback = check_fn(ctx)
        fraction = min(max(fraction, 0.0), 1.0)

        scored.append(
            ScoredItem(
                rubric_id=item.id,
                criterion=item.criterion,
                points=round(max_points * fraction, 1),
                max_points=round(max_points, 1),
                feedback=feedback,
            )
        )

    return Score(
        project_id=project.id,
        total=round(sum(s.points for s in scored), 1),
        items=scored,
    )

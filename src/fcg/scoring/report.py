"""Turn a Score into something a human reads."""

from __future__ import annotations

import pandas as pd

from fcg.models import Project, Score


def scorecard_frame(score: Score) -> pd.DataFrame:
    """One row per rubric item: criterion, points, and why."""
    return pd.DataFrame(
        [
            {
                "Criterion": s.criterion,
                "Score": f"{s.points:g} / {s.max_points:g}",
                "Feedback": s.feedback,
            }
            for s in score.items
        ]
    )


def client_reaction(project: Project, score: Score) -> str:
    """What the client would say. The number, with a face on it."""
    name = project.client.contact_name.split()[0]
    total = score.total

    if total >= 85:
        return f"“That's exactly what we asked for. When can you start on the rest?” — {name}"
    if total >= 70:
        return f"“Good. There are a couple of things we asked for that I can't see, but good.” — {name}"
    if total >= 50:
        return f"“It's a start. Half of what we asked for is missing, though.” — {name}"
    return (
        f"“I'm not sure you read the brief. This isn't the shop we described.” — {name}"
    )

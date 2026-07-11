"""Weekly generation quota (docs/decisions.md D10, D11).

Each user may generate WEEKLY_LIMIT projects per calendar week, plus one
extra for every project completed (submitted and scored) that week. The
counters are rows in Supabase's generation_events and completion_events
tables, scoped to the signed-in user by RLS; the week resets Monday
00:00 UTC.
"""

from datetime import datetime, timedelta, timezone

from auth import _client, current_user

WEEKLY_LIMIT = 3


def week_start(now: datetime | None = None) -> datetime:
    """Monday 00:00 UTC of the week containing `now`."""
    now = now or datetime.now(timezone.utc)
    return (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )


def next_week_start(now: datetime | None = None) -> datetime:
    """When the quota resets: Monday 00:00 UTC of the following week."""
    return week_start(now) + timedelta(days=7)


def used_this_week() -> int:
    """How many generations the signed-in user has recorded this week."""
    res = (
        _client()
        .table("generation_events")
        .select("id", count="exact")
        .eq("user_id", current_user().id)
        .gte("created_at", week_start().isoformat())
        .execute()
    )
    return res.count or 0


def record_generation(project_id: str, difficulty: str = "medium") -> None:
    """Record one generation against the signed-in user's weekly allowance.

    Difficulty is stored so the List of projects page can rebuild the project
    exactly as it was generated (D12) — the id alone doesn't encode it.
    """
    _client().table("generation_events").insert(
        {
            "user_id": current_user().id,
            "project_id": project_id,
            "difficulty": difficulty,
        }
    ).execute()


def completions_this_week() -> int:
    """How many projects the signed-in user has completed this week."""
    res = (
        _client()
        .table("completion_events")
        .select("id", count="exact")
        .eq("user_id", current_user().id)
        .gte("created_at", week_start().isoformat())
        .execute()
    )
    return res.count or 0


def allowance_left(used: int, completions: int) -> int:
    """Generations remaining: the weekly base plus one per completion (D11)."""
    return max(WEEKLY_LIMIT + completions - used, 0)


def record_completion(project_id: str, score: float) -> bool:
    """Mark a project complete after scoring. Returns True if newly complete.

    One credit per project, ever — the (user_id, project_id) unique
    constraint turns resubmissions into no-ops (ignore_duplicates), so
    submitting the same repo repeatedly can't mint credits.
    """
    res = (
        _client()
        .table("completion_events")
        .upsert(
            {
                "user_id": current_user().id,
                "project_id": project_id,
                "score": score,
            },
            on_conflict="user_id,project_id",
            ignore_duplicates=True,
        )
        .execute()
    )
    return bool(res.data)

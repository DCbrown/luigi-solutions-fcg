"""Weekly generation quota (docs/decisions.md D10).

Each user may generate WEEKLY_LIMIT projects per calendar week. The counter
is rows in Supabase's generation_events table, scoped to the signed-in user
by RLS; the week resets Monday 00:00 UTC.
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


def record_generation(project_id: str) -> None:
    """Record one generation against the signed-in user's weekly allowance."""
    _client().table("generation_events").insert(
        {"user_id": current_user().id, "project_id": project_id}
    ).execute()

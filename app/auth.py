"""Supabase authentication for the FCG app.

Identity lives in Supabase Auth (docs/decisions.md D9); everything else stays
files-on-disk (D5). The app authenticates with the publishable key from
.streamlit/secrets.toml — client-safe by design. No service or Management API
key is ever used here.
"""

import streamlit as st
from supabase import Client, create_client
from supabase_auth.errors import AuthApiError

# Development levels (docs/decisions.md D12). Stored in Supabase Auth
# user_metadata — no table. The mapping feeds generate_project(difficulty=…),
# which has scaled feature count, constraints, and dataset size since day one.
LEVELS = {
    "junior": "Junior — a smaller brief: 3 features, a 10-row dataset",
    "mid": "Mid-level — the standard brief: 4 features, 14 rows",
    "senior": "Senior — the full ask: 6 features, 18 rows, more constraints",
}
LEVEL_TO_DIFFICULTY = {"junior": "easy", "mid": "medium", "senior": "hard"}
DEFAULT_LEVEL = "mid"


def _client() -> Client:
    # One client per browser session, deliberately not st.cache_resource: the
    # client carries the signed-in user's tokens, and a process-wide cached
    # client would hand one user's session to everyone.
    if "supabase_client" not in st.session_state:
        if "supabase" not in st.secrets:
            st.error(
                "Supabase secrets are not configured. Locally: copy "
                "`.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` "
                "and fill it in. On Streamlit Community Cloud: paste the same "
                "`[supabase]` block under the app's **Settings → Secrets**."
            )
            st.stop()
        cfg = st.secrets["supabase"]
        st.session_state.supabase_client = create_client(
            cfg["url"], cfg["publishable_key"]
        )

    client = st.session_state.supabase_client
    # Re-pin the data-API auth to the live session on every access. The SDK's
    # auth-event handler downgrades the Authorization header to the anon key
    # on any event it doesn't map to a session — update_user's USER_UPDATED
    # included — after which selects silently see zero rows and inserts fail
    # RLS with 42501 (the "changed my level, couldn't generate" bug).
    # get_session() also refreshes an expired token, covering hour-long tabs.
    try:
        session = client.auth.get_session()
        if session:
            client.postgrest.auth(session.access_token)
    except Exception:
        pass  # signed out — anon is the correct identity then
    return client


def current_user():
    """The signed-in Supabase user, or None."""
    return st.session_state.get("auth_user")


def current_level() -> str:
    """The signed-in user's development level.

    Accounts created before levels existed have no metadata — they get
    DEFAULT_LEVEL until they pick one in Settings.
    """
    user = current_user()
    level = (getattr(user, "user_metadata", None) or {}).get("level")
    return level if level in LEVELS else DEFAULT_LEVEL


def update_level(level: str) -> str | None:
    """Change the signed-in user's level. Returns an error message or None."""
    if level not in LEVELS:
        return f"Unknown level {level!r}."
    try:
        res = _client().auth.update_user({"data": {"level": level}})
    except AuthApiError as e:
        return e.message
    except Exception as e:
        return (
            "Could not reach the authentication service "
            f"({type(e).__name__}: {e}). Check your connection and try again."
        )
    st.session_state.auth_user = res.user
    return None


def sign_in(email: str, password: str) -> str | None:
    """Sign in. Returns an error message, or None on success."""
    try:
        res = _client().auth.sign_in_with_password(
            {"email": email, "password": password}
        )
    except AuthApiError as e:
        return e.message
    except Exception as e:
        return (
            "Could not reach the authentication service "
            f"({type(e).__name__}: {e}). Check your connection and try again."
        )
    st.session_state.auth_user = res.user
    return None


def sign_up(email: str, password: str, level: str = DEFAULT_LEVEL) -> tuple[bool, str | None]:
    """Create an account with a development level.

    Returns (signed_in, message). With email confirmation on (the Supabase
    default) a successful signup is NOT signed in yet — the message says to
    check the inbox.
    """
    try:
        res = _client().auth.sign_up(
            {
                "email": email,
                "password": password,
                "options": {"data": {"level": level}},
            }
        )
    except AuthApiError as e:
        return False, e.message
    except Exception as e:
        return False, (
            "Could not reach the authentication service "
            f"({type(e).__name__}: {e}). Check your connection and try again."
        )
    if res.session is None:
        return (
            False,
            "Account created — confirm it from the email we sent you, then log in.",
        )
    st.session_state.auth_user = res.user
    return True, None


def logout() -> None:
    try:
        _client().auth.sign_out()
    except Exception:
        pass  # the server-side session may already be gone; log out locally anyway
    # Clear everything, not just auth keys: the next login in this tab may be a
    # different user, who must not inherit this one's project or score.
    st.session_state.clear()

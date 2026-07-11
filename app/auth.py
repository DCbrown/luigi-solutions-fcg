"""Supabase authentication for the FCG app.

Identity lives in Supabase Auth (docs/decisions.md D9); everything else stays
files-on-disk (D5). The app authenticates with the publishable key from
.streamlit/secrets.toml — client-safe by design. No service or Management API
key is ever used here.
"""

import streamlit as st
from supabase import Client, create_client
from supabase_auth.errors import AuthApiError


def _client() -> Client:
    # One client per browser session, deliberately not st.cache_resource: the
    # client carries the signed-in user's tokens, and a process-wide cached
    # client would hand one user's session to everyone.
    if "supabase_client" not in st.session_state:
        cfg = st.secrets["supabase"]
        st.session_state.supabase_client = create_client(
            cfg["url"], cfg["publishable_key"]
        )
    return st.session_state.supabase_client


def current_user():
    """The signed-in Supabase user, or None."""
    return st.session_state.get("auth_user")


def sign_in(email: str, password: str) -> str | None:
    """Sign in. Returns an error message, or None on success."""
    try:
        res = _client().auth.sign_in_with_password(
            {"email": email, "password": password}
        )
    except AuthApiError as e:
        return e.message
    except Exception:
        return "Could not reach the authentication service. Check your connection and try again."
    st.session_state.auth_user = res.user
    return None


def sign_up(email: str, password: str) -> tuple[bool, str | None]:
    """Create an account.

    Returns (signed_in, message). With email confirmation on (the Supabase
    default) a successful signup is NOT signed in yet — the message says to
    check the inbox.
    """
    try:
        res = _client().auth.sign_up({"email": email, "password": password})
    except AuthApiError as e:
        return False, e.message
    except Exception:
        return False, "Could not reach the authentication service. Check your connection and try again."
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

"""Streamlit entry point.

Run with:  streamlit run app/main.py

UI only. Anything that thinks lives in src/fcg/ (docs/quality.md, Conventions).
Routing is gated on auth (docs/decisions.md D9): signed out, the only page is
login; signed in, the full app.
"""

import os

# pyarrow's bundled mimalloc segfaulted the app mid-session (Arrow conversion
# on a script thread, 2026-07-11 — see docs/HANDOFF.md); the system allocator
# doesn't. Read once at pyarrow import, so it must be set before anything
# imports pyarrow.
os.environ.setdefault("ARROW_DEFAULT_MEMORY_POOL", "system")

import sys
from pathlib import Path

# Local dev imports fcg via the editable install (docs/HANDOFF.md), but deploy
# environments that only install requirements.txt don't reliably honour the
# `-e .` line — Streamlit Community Cloud doesn't. This makes the src/ layout
# importable everywhere; it's a harmless no-op where fcg is already installed.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import streamlit as st

from auth import current_user, logout

st.set_page_config(page_title="Fictional Client Generator", page_icon="📁")

user = current_user()

if user is None:
    page = st.navigation(
        [st.Page("app_pages/login.py", title="Log in", icon=":material/login:")],
        position="hidden",
    )
else:
    with st.sidebar:
        st.caption(f"Signed in as **{user.email}**")
        st.button("Log out", icon=":material/logout:", on_click=logout)
    page = st.navigation(
        [
            st.Page("app_pages/home.py", title="Home", icon=":material/home:", default=True),
            st.Page("app_pages/generate.py", title="Generate", icon=":material/casino:"),
            st.Page("app_pages/projects.py", title="List of projects", icon=":material/folder_open:"),
            st.Page("app_pages/submit.py", title="Submit and score", icon=":material/grading:"),
            st.Page("app_pages/settings.py", title="Settings", icon=":material/settings:"),
        ]
    )

page.run()

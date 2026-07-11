"""Page 1 — generate a new fictional client project."""

import streamlit as st

from fcg.generator import generate_project
from fcg.storage import save_project
from quota import WEEKLY_LIMIT, next_week_start, record_generation, used_this_week

st.title("Generate a project")

# Weekly cap (docs/decisions.md D10). Fail closed: no count, no generating.
try:
    used = used_this_week()
except Exception as e:
    st.error(
        "Couldn't check your weekly project allowance "
        f"({type(e).__name__}: {e}). Generating is paused until the check "
        "works — try reloading."
    )
    st.stop()

left = max(WEEKLY_LIMIT - used, 0)
if left == 0:
    st.warning(
        f"You've used all {WEEKLY_LIMIT} project requests for this week. "
        f"New requests open **{next_week_start():%A %d %B}** at 00:00 UTC."
    )
    st.stop()

st.caption(f"{left} of {WEEKLY_LIMIT} project requests left this week.")

st.write(
    "Same seed, same client — so you can hand someone a number and you'll both "
    "get the identical brief, and your scores will mean the same thing."
)

seed_input = st.text_input("Seed (leave blank for a random one)", placeholder="e.g. 4471")

if st.button("Generate", type="primary"):
    seed = None
    if seed_input.strip():
        try:
            seed = int(seed_input.strip())
        except ValueError:
            st.error("A seed has to be a whole number.")
            st.stop()

    project, seed_data = generate_project(seed=seed)
    save_project(project, seed_data)
    record_generation(project.id)

    st.session_state["project"] = project
    st.session_state["seed_data"] = seed_data
    st.session_state.pop("score", None)  # a new project invalidates the old score

    st.success(
        f"**{project.client.name}** needs a page. Seed `{project.seed}`. "
        f"({left - 1} request(s) left this week.)"
    )
    st.page_link("app_pages/projects.py", label="Read the brief in your projects →")

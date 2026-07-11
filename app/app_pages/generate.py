"""Page 1 — generate a new fictional client project."""

import random

import streamlit as st

from fcg.generator import generate_project
from fcg.generator.seeds import available_scenarios
from fcg.storage import save_project
from quota import (
    WEEKLY_LIMIT,
    allowance_left,
    completions_this_week,
    next_week_start,
    record_generation,
    used_this_week,
)

st.title("Generate a project")

# Weekly cap plus completion credits (docs/decisions.md D10, D11).
# Fail closed: no count, no generating.
try:
    used = used_this_week()
    completions = completions_this_week()
except Exception as e:
    st.error(
        "Couldn't check your weekly project allowance "
        f"({type(e).__name__}: {e}). Generating is paused until the check "
        "works — try reloading."
    )
    st.stop()

cap = WEEKLY_LIMIT + completions
left = allowance_left(used, completions)
if left == 0:
    st.warning(
        f"You've used all {cap} project requests for this week. "
        f"New requests open **{next_week_start():%A %d %B}** at 00:00 UTC — "
        "or complete a project you've already generated (submit it for "
        "scoring) to earn another one right away."
    )
    st.stop()

st.caption(f"{left} of {cap} project requests left this week.")

st.write(
    "Same seed, same client — so you can hand someone a number and you'll both "
    "get the identical brief, and your scores will mean the same thing."
)

SURPRISE = "Surprise me"
scenario_choice = st.selectbox(
    "Business type",
    [SURPRISE, *available_scenarios()],
    format_func=lambda s: s if s == SURPRISE else s.replace("-", " ").capitalize(),
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

    # "Surprise me" picks outside the project seed on purpose: scenario is not
    # part of the seeded draw (a one-way door — see generator/project.py). The
    # choice is still reproducible because the project id records it.
    scenario = (
        random.choice(available_scenarios())
        if scenario_choice == SURPRISE
        else scenario_choice
    )

    project, seed_data = generate_project(seed=seed, scenario=scenario)
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

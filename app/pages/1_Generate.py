"""Page 1 — generate a new fictional client project."""

import streamlit as st

from fcg.generator import generate_project
from fcg.storage import save_project

st.set_page_config(page_title="Generate — FCG", page_icon="📁")
st.title("Generate a project")

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

    st.session_state["project"] = project
    st.session_state["seed_data"] = seed_data
    st.session_state.pop("score", None)  # a new project invalidates the old score

    st.success(f"**{project.client.name}** needs a page. Seed `{project.seed}`.")
    st.page_link("pages/2_Brief.py", label="Read the brief →")

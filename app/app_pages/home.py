"""Home — what this is and where the current project stands."""

import streamlit as st

from fcg.storage import list_projects

st.title("📁 Fictional Client Generator")
st.write(
    "A fake client with a real brief. Build what they asked for, push it to "
    "GitHub, and find out how much of it you actually delivered."
)

st.subheader("How it works")
st.markdown(
    """
1. **Generate** — you get a client, a brief, and a spreadsheet of their content.
2. **Build** — leave the app. Any stack you like. Aim for about two hours.
3. **Submit** — push to a public GitHub repo and paste the link.
4. **Score** — graded against the rubric written *with* your brief, before you
   wrote a line. It can't move the goalposts.
"""
)

current = st.session_state.get("project")
if current:
    st.success(f"Current project: **{current.client.name}** — `{current.id}`")
    st.page_link("app_pages/projects.py", label="Read the brief →")
else:
    st.info("No project yet.")
    st.page_link("app_pages/generate.py", label="Generate one →")

saved = list_projects()
if saved:
    st.caption(f"{len(saved)} project(s) saved in `data/generated/`.")

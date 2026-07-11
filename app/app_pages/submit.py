"""Page 3 — paste your repo URL, get a scorecard."""

import streamlit as st

from fcg.ingest import IngestError, fetch_repo
from fcg.scoring import grade_submission
from fcg.scoring.report import client_reaction, scorecard_frame

st.title("Submit and score")

project = st.session_state.get("project")
seed_data = st.session_state.get("seed_data")

if project is None:
    st.warning("No project to submit against.")
    st.page_link("app_pages/generate.py", label="Generate one →")
    st.stop()

st.caption(f"Submitting against **{project.client.name}** · seed `{project.seed}`")

repo_url = st.text_input(
    "Your public GitHub repo URL",
    placeholder="https://github.com/you/bakery-page",
)

if st.button("Submit for scoring", type="primary", disabled=not repo_url.strip()):
    try:
        with st.spinner("Cloning your repo…"):
            submission = fetch_repo(repo_url, project.id)
    except IngestError as e:
        st.error(str(e))
        st.stop()

    st.caption(f"Read {len(submission.files)} source files. (Nothing was executed.)")

    with st.spinner("Scoring against the brief…"):
        score = grade_submission(project, submission, seed_data)

    st.session_state["score"] = score

score = st.session_state.get("score")
if score:
    st.divider()
    st.metric("Score", f"{score.total:g} / 100")
    st.markdown(f"*{client_reaction(project, score)}*")

    st.markdown("### The scorecard")
    st.dataframe(scorecard_frame(score), width="stretch", hide_index=True)

    st.caption(
        "Checks marked exact are certain. Feature checks read your source rather "
        "than the rendered page, so they can miss things — if one says *no "
        "evidence found* for something you definitely built, that's a limitation "
        "on my end, not necessarily on yours."
    )

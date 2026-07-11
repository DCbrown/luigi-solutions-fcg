"""List of projects — every request this account has generated.

Each entry rebuilds from its seed when rendered (D1): nothing is stored
beyond the generation_events row that the weekly quota already writes.
"""

from datetime import datetime

import streamlit as st

from history import rebuild, recent_generations

st.title("List of projects")

try:
    events = recent_generations()
except Exception as e:
    st.error(
        f"Couldn't load your projects ({type(e).__name__}: {e}). Try reloading."
    )
    st.stop()

if not events:
    st.info("Nothing yet — projects you generate will show up here.")
    st.page_link("app_pages/generate.py", label="Generate one →")
    st.stop()

current = st.session_state.get("project")
st.caption(
    f"{len(events)} project request(s). Details rebuild from the seed — "
    "same seed, same project, every time."
)

for event in events:
    try:
        project, seed_data = rebuild(
            event["project_id"], event.get("difficulty") or "medium"
        )
    except Exception:
        st.caption(f"`{event['project_id']}` — can't rebuild this one.")
        continue

    client = project.client
    brief = project.brief
    is_current = current is not None and current.id == project.id
    title = f"{client.name} — seed `{project.seed}`"
    if is_current:
        title += " · ✓ current"

    with st.expander(title):
        requested = datetime.fromisoformat(event["created_at"])
        st.caption(
            f"{project.scenario} · requested {requested:%d %B %Y} · `{project.id}`"
        )
        st.write(client.background)

        st.markdown("**Why they got in touch** — " + brief.context)
        st.markdown("**What they want** — " + brief.ask)

        st.markdown("**It has to have**")
        for f in brief.features:
            st.markdown(f"- **{f.name}** — {f.description}")

        st.markdown("**And they were quite firm about**")
        for c in brief.constraints:
            st.markdown(f"- {c}")

        st.markdown("**Hand back**")
        for f in brief.required_files:
            st.markdown(f"- `{f}`")
        st.markdown("- the page itself, and a public GitHub repo to find it in")

        st.markdown("**Their content**")
        st.dataframe(seed_data, width="stretch")
        st.download_button(
            "Download products.csv",
            data=seed_data.to_csv(index=False).encode("utf-8"),
            file_name="products.csv",
            mime="text/csv",
            key=f"csv-{event['id']}",
        )

        if not is_current:
            if st.button(
                "Work on this one", key=f"work-{event['id']}", type="primary"
            ):
                st.session_state["project"] = project
                st.session_state["seed_data"] = seed_data
                st.session_state.pop("score", None)
                st.rerun()
        else:
            st.caption("This is your current project.")

st.page_link("app_pages/submit.py", label="Submit the current project →")

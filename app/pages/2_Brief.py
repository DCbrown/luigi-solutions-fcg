"""Page 2 — read the brief, take the client's content, go and build it."""

import streamlit as st

st.set_page_config(page_title="The brief — FCG", page_icon="📁")
st.title("The brief")

project = st.session_state.get("project")
seed_data = st.session_state.get("seed_data")

if project is None:
    st.warning("No project yet.")
    st.page_link("pages/1_Generate.py", label="Generate one →")
    st.stop()

client = project.client
brief = project.brief

st.subheader(client.name)
st.caption(f"{client.contact_name} — {client.contact_role} · seed `{project.seed}`")
st.write(client.background)

st.divider()
st.markdown("### Why they got in touch")
st.write(brief.context)

st.markdown("### What they want")
st.write(brief.ask)

st.markdown("### It has to have")
for f in brief.features:
    st.markdown(f"**{f.name}** — {f.description}")

st.markdown("### And they were quite firm about")
for c in brief.constraints:
    st.markdown(f"- {c}")

st.markdown("### Hand back")
for f in brief.required_files:
    st.markdown(f"- `{f}`")
st.markdown("- the page itself, and a public GitHub repo to find it in")

st.divider()
st.markdown("### Their content")
st.write(
    "This is the real list, off their till. Build the page from **this** — "
    "inventing your own products is the fastest way to lose most of the marks."
)
st.dataframe(seed_data, width="stretch")

st.download_button(
    "Download products.csv",
    data=seed_data.to_csv(index=False).encode("utf-8"),
    file_name="products.csv",
    mime="text/csv",
    type="primary",
)

st.info("Go and build it. When you're done, push it to GitHub and come back.")
st.page_link("pages/3_Submit_and_Score.py", label="Submit your work →")

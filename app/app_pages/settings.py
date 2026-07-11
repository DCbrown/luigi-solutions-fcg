"""Account settings — currently just the development level (D12)."""

import streamlit as st

from auth import LEVELS, current_level, current_user, update_level

st.title("Settings")
st.caption(f"Signed in as **{current_user().email}**")

st.subheader("Development level")
st.write(
    "Sizes the briefs you're given: more features, more constraints, and a "
    "bigger dataset as you go up. It applies from your next generated "
    "project — nothing already generated changes."
)

level = st.radio(
    "Level",
    options=list(LEVELS),
    index=list(LEVELS).index(current_level()),
    format_func=lambda lv: LEVELS[lv],
    label_visibility="collapsed",
)

if st.button("Save", type="primary", disabled=level == current_level()):
    error = update_level(level)
    if error:
        st.error(error)
    else:
        st.success(f"Level saved — briefs are now sized {level}.")
        st.rerun()

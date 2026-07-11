"""Login / signup gate. The only page an unauthenticated visitor sees."""

import streamlit as st

from auth import DEFAULT_LEVEL, LEVELS, sign_in, sign_up

st.title("📁 Fictional Client Generator")
st.write(
    "A fake client with a real brief. Log in to get one — your projects and "
    "scores stay on this machine."
)

login_tab, signup_tab = st.tabs(["Log in", "Sign up"])

with login_tab:
    with st.form("login"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Log in", type="primary"):
            error = sign_in(email.strip(), password)
            if error:
                st.error(error)
            else:
                st.rerun()

with signup_tab:
    with st.form("signup"):
        email = st.text_input("Email")
        password = st.text_input("Password (6+ characters)", type="password")
        level = st.radio(
            "Your development level",
            options=list(LEVELS),
            index=list(LEVELS).index(DEFAULT_LEVEL),
            format_func=lambda lv: LEVELS[lv],
            help="Sizes the briefs you're given. You can change it any time in Settings.",
        )
        if st.form_submit_button("Create account", type="primary"):
            signed_in, message = sign_up(email.strip(), password, level)
            if signed_in:
                st.rerun()
            elif message and message.startswith("Account created"):
                st.success(message)
            else:
                st.error(message)

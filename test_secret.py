import streamlit as st

st.title("Secret Test")

if "APPS_SCRIPT_URL" in st.secrets:
    url = st.secrets["APPS_SCRIPT_URL"]
    st.success(f"Secret loaded! URL starts with: {url[:50]}...")
else:
    st.error("Secret NOT found. Check your secrets TOML formatting.")

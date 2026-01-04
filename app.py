import streamlit as st
import streamlit_authenticator as stauth

st.set_page_config(page_title="Casadisteo Portal", layout="wide")

names = ["Admin"]
usernames = ["admin"]

hashed_passwords = stauth.utilities.hasher.Hasher(
    ["change_me_now"]
).generate()

authenticator = stauth.Authenticate(
    names,
    usernames,
    hashed_passwords,
    "casadisteo_cookie",
    "super_secret_key",
    cookie_expiry_days=7,
)

name, authentication_status, username = authenticator.login("Login", "main")

if authentication_status:
    st.sidebar.success(f"Welcome {name}")
    authenticator.logout("Logout", "sidebar")
    st.title("🏠 Casadisteo Portal")
    st.write("Private dashboard")
elif authentication_status is False:
    st.error("Invalid credentials")
else:
    st.warning("Please log in")

import streamlit as st
import json
from typing import Any

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import bcrypt

st.set_page_config(page_title="Casadisteo Portal", layout="wide")

TEMPLATE_WORKSHEETS = ["FARMACI", "POSOLOGIA", "INVENTARIO", "REGISTRO", "LISTE"]

def _require_secrets() -> None:
    missing = []
    if "auth" not in st.secrets:
        missing.append("auth")
    if "google_sheets" not in st.secrets:
        missing.append("google_sheets")
    if missing:
        st.error(
            "Missing Streamlit secrets: "
            + ", ".join(missing)
            + ". Add them in Render (Environment → Secret Files) or locally as .streamlit/secrets.toml."
        )
        st.info("Use `.streamlit/secrets.toml.example` as a template.")
        st.stop()

def _get_users() -> dict[str, dict[str, str]]:
    """
    Reads users from Streamlit secrets using the same structure as streamlit-authenticator:
      [auth.credentials.usernames.<username>]
      name = "..."
      password = "<bcrypt hash>"
    """
    auth = st.secrets["auth"]
    credentials = auth.get("credentials") or {}
    usernames = credentials.get("usernames") or {}
    if not usernames:
        st.error("No users found in `auth.credentials.usernames` in secrets.")
        st.stop()
    # Convert to plain dict (Streamlit secrets are immutable mappings)
    return {u: {"name": v.get("name", u), "password": v.get("password", "")} for u, v in usernames.items()}

def _check_password(plain_password: str, password_hash: str) -> bool:
    if not plain_password or not password_hash:
        return False
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False

def _login_gate() -> tuple[str, str]:
    """
    Returns (username, display_name) if authenticated; otherwise renders login form and stops.
    """
    if st.session_state.get("auth_username") and st.session_state.get("auth_name"):
        return st.session_state["auth_username"], st.session_state["auth_name"]

    users = _get_users()

    st.title("🏠 Casadisteo Supplies Portal")
    st.info("Please log in")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")

    if submitted:
        user = users.get(username)
        if user and _check_password(password, user.get("password", "")):
            st.session_state["auth_username"] = username
            st.session_state["auth_name"] = user.get("name", username)
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.stop()

def _sheet_client() -> gspread.Client:
    gs = st.secrets["google_sheets"]
    raw = gs.get("gcp_service_account_json")
    if not raw:
        st.error("`google_sheets.gcp_service_account_json` is not set. Update it in secrets.")
        st.stop()

    try:
        info: dict[str, Any] = json.loads(raw)
    except Exception:
        st.error("`google_sheets.gcp_service_account_json` must be valid JSON.")
        st.stop()

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    return gspread.authorize(creds)

def _open_spreadsheet() -> gspread.Spreadsheet:
    gs = st.secrets["google_sheets"]
    sheet_id = gs.get("sheet_id")
    if not sheet_id:
        st.error("`google_sheets.sheet_id` is not set. Update it in secrets.")
        st.stop()

    client = _sheet_client()
    return client.open_by_key(sheet_id)

def _load_worksheet(spreadsheet: gspread.Spreadsheet, worksheet_name: str) -> tuple[gspread.Worksheet, pd.DataFrame]:
    try:
        ws = spreadsheet.worksheet(worksheet_name)
    except Exception:
        st.error(f"Worksheet `{worksheet_name}` not found in the spreadsheet.")
        st.stop()

    records = ws.get_all_records()
    df = pd.DataFrame(records)
    return ws, df

def _save_worksheet(ws: gspread.Worksheet, df: pd.DataFrame) -> None:
    headers = ws.row_values(1)
    if not headers:
        st.error("Worksheet header row (row 1) is empty.")
        st.stop()

    for col in headers:
        if col not in df.columns:
            df[col] = ""

    out = df[headers].fillna("")
    values = [headers] + out.values.tolist()
    ws.update(values)


_require_secrets()
username, display_name = _login_gate()

st.sidebar.success(f"Welcome {display_name}")
if st.sidebar.button("Logout"):
    st.session_state.pop("auth_username", None)
    st.session_state.pop("auth_name", None)
    st.rerun()

spreadsheet = _open_spreadsheet()

gs_cfg = st.secrets["google_sheets"]
configured_ws = (gs_cfg.get("worksheet") or "").strip()
worksheet_candidates: list[str] = []
if configured_ws:
    worksheet_candidates.append(configured_ws)
worksheet_candidates.extend(TEMPLATE_WORKSHEETS)
# Also try lowercase variants for convenience (e.g. "registro")
worksheet_candidates.extend([w.lower() for w in TEMPLATE_WORKSHEETS])

available_worksheets: list[str] = []
seen = set()
for w in worksheet_candidates:
    if not w or w in seen:
        continue
    seen.add(w)
    try:
        spreadsheet.worksheet(w)
    except Exception:
        continue
    available_worksheets.append(w)

if not available_worksheets:
    st.error(
        "No expected worksheets found. Create the tabs from `medicinali_google_sheet_template.md` "
        "or set `google_sheets.worksheet` to an existing tab name."
    )
    st.stop()

st.title("🏠 Casadisteo Supplies Portal")
st.caption("Google Sheets editor (tabs: FARMACI, POSOLOGIA, INVENTARIO, REGISTRO, LISTE).")

tabs = st.tabs(available_worksheets)
for tab, worksheet_name in zip(tabs, available_worksheets, strict=True):
    with tab:
        ws, df = _load_worksheet(spreadsheet, worksheet_name)

        if df.empty:
            st.info("No rows found yet. Add rows to this tab in Google Sheets.")
            # Still show an empty editor with the headers (if any) so users can add rows from the app.
            headers = ws.row_values(1)
            if headers:
                df = pd.DataFrame(columns=headers)

        edited = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
        )

        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button(f"Save {worksheet_name}", type="primary"):
                _save_worksheet(ws, edited)
                st.success("Saved to Google Sheets.")
                st.rerun()
        with col2:
            st.info("Tip: keep the first row in Sheets as the header row.")

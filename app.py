import streamlit as st
import streamlit_authenticator as stauth
import json
from typing import Any

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Casadisteo Portal", layout="wide")

def _to_plain_dict(obj: Any) -> Any:
    """
    Streamlit secrets objects are immutable mappings. Some libraries (like
    streamlit-authenticator) expect a mutable dict and may write into it.
    Convert nested mappings/lists into plain Python types.
    """
    if isinstance(obj, dict):
        return {k: _to_plain_dict(v) for k, v in obj.items()}
    if hasattr(obj, "items"):
        # Covers Streamlit's Secrets / AttrDict-like mappings
        return {k: _to_plain_dict(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_plain_dict(v) for v in obj]
    if isinstance(obj, tuple):
        return tuple(_to_plain_dict(v) for v in obj)
    return obj

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

def _authenticator() -> stauth.Authenticate:
    auth = st.secrets["auth"]
    cookie_name = auth.get("cookie_name", "casadisteo_portal")
    cookie_key = auth.get("cookie_key")
    if not cookie_key or cookie_key == "CHANGE_ME_TO_A_LONG_RANDOM_STRING":
        st.error("`auth.cookie_key` is not set. Update it in secrets.")
        st.stop()

    credentials = auth.get("credentials")
    if not credentials:
        st.error("`auth.credentials` is not set. Update it in secrets.")
        st.stop()

    credentials = _to_plain_dict(credentials)

    return stauth.Authenticate(
        credentials,
        cookie_name,
        cookie_key,
        cookie_expiry_days=int(auth.get("cookie_expiry_days", 7)),
    )

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

def _load_inventory() -> tuple[gspread.Worksheet, pd.DataFrame]:
    gs = st.secrets["google_sheets"]
    sheet_id = gs.get("sheet_id")
    worksheet_name = gs.get("worksheet", "inventory")
    if not sheet_id:
        st.error("`google_sheets.sheet_id` is not set. Update it in secrets.")
        st.stop()

    client = _sheet_client()
    ws = client.open_by_key(sheet_id).worksheet(worksheet_name)
    records = ws.get_all_records()
    df = pd.DataFrame(records)
    return ws, df

def _save_inventory(ws: gspread.Worksheet, df: pd.DataFrame) -> None:
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

def _coerce_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


_require_secrets()
authenticator = _authenticator()

name, authentication_status, username = authenticator.login(location="main", key="Login")

if authentication_status:
    st.sidebar.success(f"Welcome {name}")
    authenticator.logout(button_name="Logout", location="sidebar", key="Logout")

    st.title("🏠 Casadisteo Supplies Portal")

    ws, df = _load_inventory()
    df = _coerce_numeric(df, ["current_qty", "reorder_at"])

    if df.empty:
        st.info("No inventory rows found yet. Add rows to your Google Sheet tab first.")
        st.stop()

    required_cols = {"item", "current_qty", "reorder_at"}
    missing_cols = sorted(list(required_cols - set(df.columns)))
    if missing_cols:
        st.error(
            "Your sheet is missing required columns: "
            + ", ".join(missing_cols)
            + ". Add them to row 1 (headers)."
        )
        st.stop()

    low = df[df["current_qty"].fillna(0) <= df["reorder_at"].fillna(0)].copy()
    low = low.sort_values(["item"], kind="stable") if "item" in low.columns else low

    tab_low, tab_all = st.tabs(["About to end", "All inventory"])

    with tab_low:
        st.subheader("About to end")
        st.caption("Items where current_qty <= reorder_at")
        st.dataframe(low, use_container_width=True)

    with tab_all:
        st.subheader("All inventory")
        st.caption("Edit quantities/thresholds and save back to the Google Sheet.")

        edited = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
            disabled=[c for c in ["updated_at"] if c in df.columns],
        )

        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("Save changes", type="primary"):
                _save_inventory(ws, edited)
                st.success("Saved to Google Sheets.")
                st.rerun()
        with col2:
            st.write("")
            st.write("")
            st.info("Tip: keep the first row in Sheets as the header row.")
elif authentication_status is False:
    st.error("Invalid credentials")
else:
    st.warning("Please log in")

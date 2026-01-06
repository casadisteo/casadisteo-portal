import streamlit as st
import json
from typing import Any

import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import bcrypt

st.set_page_config(page_title="Portale Casadisteo", layout="wide")

TEMPLATE_WORKSHEETS = ["FARMACI", "POSOLOGIA", "INVENTARIO", "REGISTRO", "LISTE"]

def _to_bool(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    s = str(v or "").strip().lower()
    return s in {"true", "1", "yes", "y", "si", "sì", "vero"}

def _to_float(v: Any) -> float | None:
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None

def _values_to_df(values: list[list[str]]) -> pd.DataFrame:
    if not values:
        return pd.DataFrame()
    headers = values[0] if values else []
    rows = values[1:] if len(values) > 1 else []
    if not headers:
        return pd.DataFrame()
    return pd.DataFrame(rows, columns=headers)

def _match_worksheet(titles: list[str], desired: str) -> str | None:
    if desired in titles:
        return desired
    desired_l = desired.strip().lower()
    for t in titles:
        if t.strip().lower() == desired_l:
            return t
    return None

def _giorni_settimana_count(raw: Any) -> int:
    s = str(raw or "").strip()
    if not s:
        return 1
    parts = [p.strip() for p in s.split(",") if p.strip()]
    return max(1, len(parts))

def _require_secrets() -> None:
    missing = []
    if "auth" not in st.secrets:
        missing.append("auth")
    if "google_sheets" not in st.secrets:
        missing.append("google_sheets")
    if missing:
        st.error(
            "Secrets Streamlit mancanti: "
            + ", ".join(missing)
            + ". Aggiungili su Render (Environment → Secret Files) oppure in locale in `.streamlit/secrets.toml`."
        )
        st.info("Usa `.streamlit/secrets.toml.example` come template.")
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
        st.error("Nessun utente trovato in `auth.credentials.usernames` nei secrets.")
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

    st.title("🏠 Portale scorte Casadisteo")
    st.info("Accedi per continuare")

    with st.form("login_form", clear_on_submit=False):
        username = st.text_input("Nome utente")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Accedi")

    if submitted:
        user = users.get(username)
        if user and _check_password(password, user.get("password", "")):
            st.session_state["auth_username"] = username
            st.session_state["auth_name"] = user.get("name", username)
            st.rerun()
        else:
            st.error("Credenziali non valide")

    st.stop()

@st.cache_resource(show_spinner=False)
def _sheet_client() -> gspread.Client:
    gs = st.secrets["google_sheets"]
    raw = gs.get("gcp_service_account_json")
    if not raw:
        st.error("`google_sheets.gcp_service_account_json` non è impostato. Aggiornalo nei secrets.")
        st.stop()

    try:
        info: dict[str, Any] = json.loads(raw)
    except Exception:
        st.error("`google_sheets.gcp_service_account_json` deve essere JSON valido.")
        st.stop()

    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(info, scopes=scopes)
    return gspread.authorize(creds)

@st.cache_resource(show_spinner=False)
def _open_spreadsheet(sheet_id: str) -> gspread.Spreadsheet:
    gs = st.secrets["google_sheets"]
    if not sheet_id:
        st.error("`google_sheets.sheet_id` non è impostato. Aggiornalo nei secrets.")
        st.stop()

    client = _sheet_client()
    return client.open_by_key(sheet_id)

@st.cache_data(ttl=30, show_spinner=False)
def _list_worksheet_titles(sheet_id: str) -> list[str]:
    spreadsheet = _open_spreadsheet(sheet_id)
    return [ws.title for ws in spreadsheet.worksheets()]

@st.cache_data(ttl=30, show_spinner=False)
def _read_worksheet_values(sheet_id: str, worksheet_name: str) -> list[list[str]]:
    """
    Returns all worksheet values (including header row) as strings.
    Cached to avoid hitting Google Sheets read quota on Streamlit reruns.
    """
    spreadsheet = _open_spreadsheet(sheet_id)
    ws = spreadsheet.worksheet(worksheet_name)
    return ws.get_all_values()

def _save_worksheet(ws: gspread.Worksheet, df: pd.DataFrame) -> None:
    headers = ws.row_values(1)
    if not headers:
        st.error("La riga intestazione (riga 1) del foglio è vuota.")
        st.stop()

    for col in headers:
        if col not in df.columns:
            df[col] = ""

    out = df[headers].fillna("")
    values = [headers] + out.values.tolist()
    ws.update(values)


_require_secrets()
username, display_name = _login_gate()

st.sidebar.success(f"Ciao {display_name}")
if st.sidebar.button("Esci"):
    st.session_state.pop("auth_username", None)
    st.session_state.pop("auth_name", None)
    st.rerun()

gs_cfg = st.secrets["google_sheets"]
sheet_id = gs_cfg.get("sheet_id")
spreadsheet = _open_spreadsheet(sheet_id)

titles = _list_worksheet_titles(sheet_id)
configured_ws = (gs_cfg.get("worksheet") or "").strip()

preferred_order: list[str] = []
if configured_ws:
    preferred_order.append(configured_ws)
preferred_order.extend(TEMPLATE_WORKSHEETS)
preferred_order.extend([w.lower() for w in TEMPLATE_WORKSHEETS])

available_worksheets: list[str] = []
seen = set()
for name in preferred_order:
    if name and name in titles and name not in seen:
        available_worksheets.append(name)
        seen.add(name)

if not available_worksheets:
    st.error(
        "Non ho trovato nessun foglio atteso. Crea i tab da `medicinali_google_sheet_template.md` "
        "oppure imposta `google_sheets.worksheet` con il nome di un tab esistente."
    )
    st.stop()

st.title("🏠 Portale scorte Casadisteo")
st.caption("Editor Google Sheets + previsione esaurimento farmaci.")

tab_editor, tab_forecast = st.tabs(["🗂️ Editor fogli", "📅 Previsione farmaci"])

with st.sidebar:
    st.subheader("Editor foglio")
    worksheet_name = st.selectbox("Scegli un foglio", options=available_worksheets, index=0)
    if st.button("Aggiorna dati"):
        _list_worksheet_titles.clear()
        _read_worksheet_values.clear()
        st.rerun()

with tab_editor:
    values = _read_worksheet_values(sheet_id, worksheet_name)
    if not values:
        st.info("Questo foglio è vuoto. Aggiungi una riga intestazione in Google Sheets (riga 1).")
        st.stop()

    headers = values[0]
    rows = values[1:]
    df = pd.DataFrame(rows, columns=headers) if headers else pd.DataFrame()

    edited = st.data_editor(
        df,
        use_container_width=True,
        num_rows="dynamic",
    )

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("Salva modifiche", type="primary"):
            ws = spreadsheet.worksheet(worksheet_name)
            _save_worksheet(ws, edited)
            _read_worksheet_values.clear()
            st.success("Salvato su Google Sheets.")
            st.rerun()
    with col2:
        st.info("Suggerimento: tieni la prima riga (riga 1) come intestazione.")

with tab_forecast:
    ws_farmaci = _match_worksheet(titles, "FARMACI")
    ws_posologia = _match_worksheet(titles, "POSOLOGIA")
    ws_inventario = _match_worksheet(titles, "INVENTARIO")

    missing_tabs = [name for name, ws in [("FARMACI", ws_farmaci), ("POSOLOGIA", ws_posologia), ("INVENTARIO", ws_inventario)] if not ws]
    if missing_tabs:
        st.warning(
            "Mancano i fogli necessari per la previsione: "
            + ", ".join(missing_tabs)
            + ". Creali usando `medicinali_google_sheet_template.md`."
        )
        st.stop()

    col_a, col_b, col_c = st.columns([2, 2, 3])
    with col_a:
        lead_time_days = st.number_input("Compra in anticipo (giorni)", min_value=0, max_value=90, value=7, step=1)
    with col_b:
        warn_within_days = st.number_input("Evidenzia se finisce entro (giorni)", min_value=1, max_value=365, value=14, step=1)
    with col_c:
        st.caption(
            "Assunzione: `quantita` in inventario è già nella stessa unità della dose, "
            "oppure rappresenta confezioni convertibili tramite `pezzi_per_confezione`."
        )

    farmaci_df = _values_to_df(_read_worksheet_values(sheet_id, ws_farmaci))
    posologia_df = _values_to_df(_read_worksheet_values(sheet_id, ws_posologia))
    inventario_df = _values_to_df(_read_worksheet_values(sheet_id, ws_inventario))

    required_cols = {
        "farmaci": {"farmaco_id", "nome_commerciale"},
        "posologia": {"farmaco_id", "dose", "unita", "frequenza", "giorni_settimana", "attivo"},
        "inventario": {"farmaco_id", "data_acquisto", "quantita", "pezzi_per_confezione"},
    }
    missing_cols = []
    for key, cols in required_cols.items():
        df0 = {"farmaci": farmaci_df, "posologia": posologia_df, "inventario": inventario_df}[key]
        for c in cols:
            if c not in df0.columns:
                missing_cols.append(f"{key}.{c}")
    if missing_cols:
        st.warning("Impossibile calcolare la previsione: mancano queste colonne: " + ", ".join(missing_cols))
        st.stop()

    pos = posologia_df.copy()
    pos["attivo_bool"] = pos["attivo"].map(_to_bool)
    pos = pos[pos["attivo_bool"]]
    pos["dose_f"] = pos["dose"].map(_to_float)

    def _weekly_multiplier(row: pd.Series) -> float | None:
        freq = str(row.get("frequenza") or "").strip().lower()
        if freq == "giornaliera":
            return 7.0
        if freq == "settimanale":
            return float(_giorni_settimana_count(row.get("giorni_settimana")))
        return None

    pos["weekly_mult"] = pos.apply(_weekly_multiplier, axis=1)
    unknown = pos[pos["weekly_mult"].isna()]
    if not unknown.empty:
        st.warning(
            "Alcune righe in POSOLOGIA hanno una `frequenza` non supportata (supportate: giornaliera, settimanale). "
            "Queste righe vengono ignorate nella previsione."
        )

    pos = pos.dropna(subset=["dose_f", "weekly_mult"])
    pos["weekly_units"] = pos["dose_f"] * pos["weekly_mult"]

    consumption = (
        pos.groupby(["farmaco_id", "unita"], as_index=False)
        .agg(weekly_units=("weekly_units", "sum"))
    )
    consumption["daily_units"] = consumption["weekly_units"] / 7.0

    today = pd.Timestamp.today().normalize()

    inv = inventario_df.copy()
    inv["data_acquisto_dt"] = pd.to_datetime(inv["data_acquisto"], errors="coerce").dt.normalize()
    inv["quantita_f"] = inv["quantita"].map(_to_float)
    inv["pezzi_f"] = inv["pezzi_per_confezione"].map(_to_float)
    inv["stock_units"] = inv.apply(
        lambda r: (r["quantita_f"] or 0.0) * (r["pezzi_f"] if (r["pezzi_f"] and r["pezzi_f"] > 0) else 1.0),
        axis=1,
    )

    def _stock_as_of_today_for_med(inv_med: pd.DataFrame, daily_units: float) -> float:
        """
        INVENTARIO is treated as a purchase log (ingressi).
        We replay purchases over time and subtract expected consumption from purchase dates to today,
        without letting stock go below 0 (handles gaps + later re-buys).
        """
        if inv_med.empty:
            return 0.0

        inv_med = inv_med.copy()
        inv_med["data_acquisto_dt"] = inv_med["data_acquisto_dt"].fillna(today)
        inv_med = inv_med[inv_med["data_acquisto_dt"] <= today]
        if inv_med.empty:
            return 0.0

        inv_med = inv_med.groupby("data_acquisto_dt", as_index=False).agg(stock_units=("stock_units", "sum"))
        inv_med = inv_med.sort_values("data_acquisto_dt")

        if not daily_units or daily_units <= 0:
            return float(inv_med["stock_units"].sum())

        stock_units = 0.0
        last_date: pd.Timestamp | None = None
        for _, r in inv_med.iterrows():
            d = r["data_acquisto_dt"]
            q = float(r["stock_units"] or 0.0)
            if last_date is None:
                last_date = d
            elif d > last_date:
                days = (d - last_date).days
                stock_units = max(0.0, stock_units - (daily_units * float(days)))
                last_date = d
            stock_units += q

        if last_date is not None and today > last_date:
            days = (today - last_date).days
            stock_units = max(0.0, stock_units - (daily_units * float(days)))

        return stock_units

    inv_by_med = {k: g for k, g in inv.groupby("farmaco_id")}
    stock_today_rows = []
    for _, r in consumption.iterrows():
        fid = r["farmaco_id"]
        daily = float(r["daily_units"] or 0.0)
        inv_med = inv_by_med.get(fid)
        stock_today_rows.append(
            {
                "farmaco_id": fid,
                "unita": r["unita"],
                "stock_units": _stock_as_of_today_for_med(inv_med if inv_med is not None else pd.DataFrame(), daily),
            }
        )
    stock_today = pd.DataFrame(stock_today_rows)

    out = consumption.merge(stock_today, on=["farmaco_id", "unita"], how="left")
    out["stock_units"] = out["stock_units"].fillna(0.0)
    out["days_left"] = out.apply(
        lambda r: (r["stock_units"] / r["daily_units"]) if (r["daily_units"] and r["daily_units"] > 0) else None,
        axis=1,
    )

    out["run_out_date"] = out["days_left"].map(lambda d: (today + pd.to_timedelta(d, unit="D")) if d is not None else pd.NaT)
    out["buy_by_date"] = out["run_out_date"].map(
        lambda d: (d - pd.Timedelta(days=int(lead_time_days))) if pd.notna(d) else pd.NaT
    )

    out = out.merge(
        farmaci_df[["farmaco_id", "nome_commerciale"]],
        on="farmaco_id",
        how="left",
    )

    out = out[["farmaco_id", "nome_commerciale", "unita", "stock_units", "daily_units", "days_left", "buy_by_date", "run_out_date"]]
    out = out.sort_values(["run_out_date", "nome_commerciale"], na_position="last")

    soon_mask = out["run_out_date"].notna() & (out["run_out_date"] <= (today + pd.Timedelta(days=int(warn_within_days))))
    soon_count = int(soon_mask.sum())
    earliest = out["run_out_date"].dropna().min()

    k1, k2, k3 = st.columns(3)
    with k1:
        st.metric("Farmaci con esaurimento calcolato", int(out["run_out_date"].notna().sum()))
    with k2:
        st.metric(f"Esaurimento entro {int(warn_within_days)} giorni", soon_count)
    with k3:
        st.metric("Primo esaurimento", earliest.date().isoformat() if pd.notna(earliest) else "—")

    out_display = out.rename(
        columns={
            "farmaco_id": "ID farmaco",
            "nome_commerciale": "Nome",
            "unita": "Unità",
            "stock_units": "Scorte (unità)",
            "daily_units": "Consumo/giorno",
            "days_left": "Giorni rimasti",
            "buy_by_date": "Comprare entro",
            "run_out_date": "Esaurimento previsto",
        }
    )
    st.dataframe(
        out_display.style.format(
            {
                "Scorte (unità)": "{:.2f}",
                "Consumo/giorno": "{:.3f}",
                "Giorni rimasti": "{:.1f}",
                "Comprare entro": lambda x: "" if pd.isna(x) else x.date().isoformat(),
                "Esaurimento previsto": lambda x: "" if pd.isna(x) else x.date().isoformat(),
            }
        ).apply(
            lambda s: ["background-color: rgba(255, 165, 0, 0.25)"] * len(s) if soon_mask.loc[s.name] else [""] * len(s),
            axis=1,
        ),
        use_container_width=True,
    )

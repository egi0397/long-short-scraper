import streamlit as st
import pandas as pd
import plotly.express as px
from supabase_utils import load_data
from datetime import datetime

st.set_page_config(page_title="Market Dashboard", layout="wide")

def check_login():
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if username == st.secrets["auth"]["username"] and password == st.secrets["auth"]["password"]:
        return True
    else:
        st.warning("Inserisci credenziali per accedere")
        return False

if not check_login():
    st.stop()

st.title("📊 Market Long/Short Dashboard")

try:
    df = load_data()
    if df.empty or "asset_name" not in df.columns:
        st.error("⚠️ Nessun dato valido trovato. Controlla che Supabase abbia la colonna `asset_name` e che contenga dati.")
        st.stop()

    df["timestamp"] = pd.to_datetime(df["timestamp"])

    asset_names = df["asset_name"].dropna().unique()

    asset = st.selectbox("Seleziona asset:", sorted(asset_names))

    # 📅 Selezione intervallo di date
    min_date = df["timestamp"].min().date()
    max_date = df["timestamp"].max().date()

    start_date = st.date_input("Data inizio", value=min_date, min_value=min_date, max_value=max_date)
    end_date = st.date_input("Data fine", value=max_date, min_value=min_date, max_value=max_date)

    if start_date > end_date:
        st.warning("⚠️ La data di inizio non può essere successiva alla data di fine.")
        st.stop()

    filtered = df[
        (df["asset_name"] == asset) &
        (df["timestamp"].dt.date >= start_date) &
        (df["timestamp"].dt.date <= end_date)
    ]

    if filtered.empty:
        st.warning("⚠️ Nessun dato per l’intervallo selezionato.")
        st.stop()

    st.metric("Ultimo valore BUY (%)", f'{filtered.iloc[-1]["buy"]:.2f}')
    st.metric("Ultimo valore SELL (%)", f'{filtered.iloc[-1]["sell"]:.2f}')

    fig = px.line(filtered.sort_values("timestamp"), x="timestamp", y="buy", title=f"Trend BUY – {asset}")
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"❌ Errore nella dashboard: {e}")

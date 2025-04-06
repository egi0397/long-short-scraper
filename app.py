import streamlit as st
import pandas as pd
import plotly.express as px
from supabase_utils import load_data

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
    st.write(df)

    if df.empty or "asset_name" not in df.columns:
        st.warning("⚠️ Nessun dato disponibile per visualizzare. Assicurati che Supabase abbia caricato i dati.")
        st.stop()

    asset_names = df["asset_name"].dropna().unique()

    if len(asset_names) == 0:
        st.warning("⚠️ Nessun asset disponibile.")
        st.stop()

    asset = st.selectbox("Seleziona asset:", sorted(asset_names))
    filtered = df[df["asset_name"] == asset]

    st.metric("Ultimo valore BUY (%)", f'{filtered.iloc[-1]["buy"]:.2f}')
    st.metric("Ultimo valore SELL (%)", f'{filtered.iloc[-1]["sell"]:.2f}')

    fig = px.line(filtered.sort_values("timestamp"), x="timestamp", y="buy", title=f"Trend BUY – {asset}")
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Errore nella dashboard: {e}")

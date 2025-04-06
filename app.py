import streamlit as st
import pandas as pd
import plotly.express as px
from supabase_utils import load_data

st.set_page_config(page_title="Market Dashboard", layout="wide")

# 🔐 Login
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

# 🚀 Main Title
st.title("📊 Market Long/Short Dashboard")

try:
    df = load_data()

    if df.empty or "asset_name" not in df.columns:
        st.warning("⚠️ Nessun dato valido trovato.")
        st.stop()

    # 🕒 Assicura che timestamp sia datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    # 🔍 Asset selection
    asset = st.selectbox("Seleziona asset:", sorted(df["asset_name"].dropna().unique()))
    filtered = df[df["asset_name"] == asset].sort_values("timestamp", ascending=True)

    # 📅 Filtro intervallo temporale
    min_date = filtered["timestamp"].min().date()
    max_date = filtered["timestamp"].max().date()
    start_date, end_date = st.date_input("Intervallo di tempo", [min_date, max_date], min_value=min_date, max_value=max_date)

    filtered = filtered[
        (filtered["timestamp"].dt.date >= start_date) &
        (filtered["timestamp"].dt.date <= end_date)
    ]

    # 🧮 Calcolo medie mobili
    filtered["SMA 24"] = filtered["buy"].rolling(window=24).mean()
    filtered["SMA 120"] = filtered["buy"].rolling(window=120).mean()

    # 📈 Grafico BUY vs SELL
    fig = px.line(filtered, x="timestamp", y=["buy", "sell"], title=f"BUY vs SELL – {asset}")
    fig.update_traces(selector=dict(name='buy'), line=dict(color='green'))
    fig.update_traces(selector=dict(name='sell'), line=dict(color='red'))
    st.plotly_chart(fig, use_container_width=True)

    # 📉 Medie mobili
    fig_ma = px.line(filtered, x="timestamp", y=["buy", "SMA 24", "SMA 120"], title=f"BUY + Medie Mobili – {asset}")
    fig_ma.update_traces(selector=dict(name='buy'), line=dict(color='green'))
    fig_ma.update_traces(selector=dict(name='SMA 24'), line=dict(color='orange'))
    fig_ma.update_traces(selector=dict(name='SMA 120'), line=dict(color='blue'))
    st.plotly_chart(fig_ma, use_container_width=True)

    # 📤 Export
    st.download_button("⬇️ Scarica CSV", data=filtered.to_csv(index=False), file_name=f"{asset}_data.csv", mime="text/csv")
    st.download_button("⬇️ Scarica Excel", data=filtered.to_excel(index=False, engine='openpyxl'), file_name=f"{asset}_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

except Exception as e:
    st.error(f"Errore nella dashboard: {e}")

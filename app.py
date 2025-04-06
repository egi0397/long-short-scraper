import streamlit as st
import pandas as pd
import plotly.graph_objects as go
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
    st.write(df)  # 👀 Mostra il contenuto del DataFrame nella dashboard

    if df.empty or "asset_name" not in df.columns:
        st.error("⚠️ Nessun dato valido trovato. Controlla che Supabase abbia la colonna `asset_name` e che contenga dati.")
        st.stop()

    asset_names = df["asset_name"].dropna().unique()

    if len(asset_names) == 0:
        st.warning("⚠️ Nessun asset disponibile.")
        st.stop()

    asset = st.selectbox("Seleziona asset:", sorted(asset_names))
    filtered = df[df["asset_name"] == asset].sort_values("timestamp", ascending=True)

    st.metric("Ultimo valore BUY (%)", f'{filtered.iloc[-1]["buy"]:.2f}')
    st.metric("Ultimo valore SELL (%)", f'{filtered.iloc[-1]["sell"]:.2f}')

    # 📊 Grafico BUY vs SELL con colori personalizzati
    line_chart = go.Figure()

    line_chart.add_trace(go.Scatter(
        x=filtered["timestamp"],
        y=filtered["buy"],
        mode="lines+markers",
        name="BUY",
        line=dict(color="green")
    ))

    line_chart.add_trace(go.Scatter(
        x=filtered["timestamp"],
        y=filtered["sell"],
        mode="lines+markers",
        name="SELL",
        line=dict(color="red")
    ))

    line_chart.update_layout(
        title=f"Andamento BUY vs SELL – {asset}",
        xaxis_title="Timestamp",
        yaxis_title="Percentuale",
        legend_title="Tipo",
    )

    st.plotly_chart(line_chart, use_container_width=True)

except Exception as e:
    st.error(f"❌ Errore nella dashboard: {e}")

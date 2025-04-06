import streamlit as st
import pandas as pd
import plotly.graph_objects as go
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

st.title("📊 Market Long/Short Dashboard")

# 📥 Carica dati da Supabase
try:
    df = load_data()

    if df.empty or "asset_name" not in df.columns:
        st.error("⚠️ Nessun dato valido trovato. Controlla che Supabase abbia la colonna `asset_name`.")
        st.stop()

    # 📆 Conversione timestamp
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

    asset_names = df["asset_name"].dropna().unique()
    asset = st.selectbox("Seleziona asset:", sorted(asset_names))
    filtered = df[df["asset_name"] == asset].copy()

    if filtered.empty:
        st.warning("⚠️ Nessun dato disponibile per questo asset.")
        st.stop()

    # ⏳ Intervallo temporale
    min_date = filtered["timestamp"].min().date()
    max_date = filtered["timestamp"].max().date()
    date_range = st.date_input("Filtra per data", [min_date, max_date])

    if len(date_range) == 2:
        start_date = pd.to_datetime(date_range[0])
        end_date = pd.to_datetime(date_range[1])
        filtered = filtered[(filtered["timestamp"] >= start_date) & (filtered["timestamp"] <= end_date)]

    if filtered.empty:
        st.warning("⚠️ Nessun dato disponibile nell'intervallo selezionato.")
        st.stop()

    # 📈 Medie mobili
    filtered["buy_MA_24"] = filtered["buy"].rolling(window=24).mean()
    filtered["buy_MA_120"] = filtered["buy"].rolling(window=120).mean()

    # 📊 Grafico
    fig = go.Figure()

    fig.add_trace(go.Scatter(x=filtered["timestamp"], y=filtered["buy"], mode='lines', name='BUY %', line=dict(color='green')))
    fig.add_trace(go.Scatter(x=filtered["timestamp"], y=filtered["sell"], mode='lines', name='SELL %', line=dict(color='red')))
    fig.add_trace(go.Scatter(x=filtered["timestamp"], y=filtered["buy_MA_24"], mode='lines', name='MA 24', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=filtered["timestamp"], y=filtered["buy_MA_120"], mode='lines', name='MA 120', line=dict(color='blue')))

    fig.update_layout(
        title=f"Trend BUY/SELL – {asset}",
        xaxis_title="Orario",
        yaxis_title="Percentuale",
        hovermode="x unified",
        height=500
    )

    st.plotly_chart(fig, use_container_width=True)

    # 📌 Ultimo valore
    latest = filtered.iloc[0]
    st.markdown("### 📌 Ultimo dato disponibile")
    st.write(f"🕒 Timestamp: `{latest['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}`")
    st.write(f"🟩 BUY: **{latest['buy']:.2f}%** | 🟥 SELL: **{latest['sell']:.2f}%**")
    if not pd.isna(latest['buy_MA_24']):
        st.write(f"🔸 MA 24: {latest['buy_MA_24']:.2f}%")
    if not pd.isna(latest['buy_MA_120']):
        st.write(f"🔹 MA 120: {latest['buy_MA_120']:.2f}%")

    # 📤 Download CSV
    st.markdown("### 📥 Scarica i dati")
    csv = filtered.drop(columns=["buy_MA_24", "buy_MA_120"]).copy()
    csv["timestamp"] = csv["timestamp"].dt.strftime('%Y-%m-%d %H:%M:%S')
    st.download_button("📄 Scarica CSV", csv.to_csv(index=False).encode('utf-8'), file_name=f"{asset}_dati.csv", mime='text/csv')

except Exception as e:
    st.error(f"Errore nella dashboard: {e}")

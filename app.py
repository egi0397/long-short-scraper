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
    st.write("✅ Dati caricati con successo")

    if df.empty or "asset_name" not in df.columns:
        st.warning("⚠️ Nessun dato disponibile.")
        st.stop()

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    asset = st.selectbox("Seleziona asset:", sorted(df["asset_name"].dropna().unique()))
    filtered = df[df["asset_name"] == asset].sort_values("timestamp", ascending=True)

    # 📅 Filtro intervallo temporale
    min_date = filtered["timestamp"].min()
    max_date = filtered["timestamp"].max()
    start_date, end_date = st.slider("Filtra per intervallo di tempo:", min_value=min_date, max_value=max_date, value=(min_date, max_date))
    filtered = filtered[(filtered["timestamp"] >= start_date) & (filtered["timestamp"] <= end_date)]

    # ➕ Medie mobili
    filtered["SMA_24"] = filtered["buy"].rolling(window=24).mean()
    filtered["SMA_120"] = filtered["buy"].rolling(window=120).mean()

    # ➕ Variazione percentuale BUY
    filtered["buy_change_%"] = filtered["buy"].pct_change() * 100

    # 📈 Line chart BUY + SELL + SMA
    fig = px.line()
    fig.add_scatter(x=filtered["timestamp"], y=filtered["buy"], mode="lines", name="BUY", line=dict(color="green"))
    fig.add_scatter(x=filtered["timestamp"], y=filtered["sell"], mode="lines", name="SELL", line=dict(color="red"))
    fig.add_scatter(x=filtered["timestamp"], y=filtered["SMA_24"], mode="lines", name="SMA 24", line=dict(color="orange", dash="dot"))
    fig.add_scatter(x=filtered["timestamp"], y=filtered["SMA_120"], mode="lines", name="SMA 120", line=dict(color="blue", dash="dot"))
    fig.update_layout(title=f"Trend BUY/SELL – {asset}", xaxis_title="Data", yaxis_title="%")

    st.plotly_chart(fig, use_container_width=True)

    # 📤 Esporta CSV o Excel
    st.subheader("⬇️ Esporta dati")
    export_format = st.radio("Scegli formato:", ["CSV", "Excel"])
    if export_format == "CSV":
        st.download_button("Scarica CSV", filtered.to_csv(index=False), file_name=f"{asset}_dati.csv", mime="text/csv")
    else:
        from io import BytesIO
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            filtered.to_excel(writer, index=False, sheet_name='Dati')
        st.download_button("Scarica Excel", buffer.getvalue(), file_name=f"{asset}_dati.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

except Exception as e:
    st.error(f"Errore nella dashboard: {e}")

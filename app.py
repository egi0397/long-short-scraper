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
    st.write(df)  # 👀 Mostra anteprima

    if df.empty or "asset_name" not in df.columns:
        st.error("⚠️ Nessun dato valido trovato.")
        st.stop()

    asset_names = df["asset_name"].dropna().unique()

    if len(asset_names) == 0:
        st.warning("⚠️ Nessun asset disponibile.")
        st.stop()

    asset = st.selectbox("Seleziona asset:", sorted(asset_names))
    filtered = df[df["asset_name"] == asset].copy()

    # 📅 Gestione timestamp
    filtered["timestamp"] = pd.to_datetime(filtered["timestamp"], utc=True)
    min_date = filtered["timestamp"].min().date()
    max_date = filtered["timestamp"].max().date()
    date_range = st.date_input("Intervallo temporale", [min_date, max_date])

    if len(date_range) == 2:
        # 👇 Converto date input in UTC datetime
        start = pd.to_datetime(date_range[0]).tz_localize("UTC")
        end = pd.to_datetime(date_range[1]).tz_localize("UTC")
        filtered = filtered[(filtered["timestamp"] >= start) & (filtered["timestamp"] <= end)]

    st.metric("Ultimo valore BUY (%)", f'{filtered.iloc[0]["buy"]:.2f}')
    st.metric("Ultimo valore SELL (%)", f'{filtered.iloc[0]["sell"]:.2f}')

    # 📊 Grafico con medie mobili
    filtered["buy_MA_24"] = filtered["buy"].rolling(window=24).mean()
    filtered["buy_MA_120"] = filtered["buy"].rolling(window=120).mean()

    fig = px.line(filtered, x="timestamp", y=["buy", "sell"], title=f"BUY vs SELL – {asset}")
    fig.add_scatter(x=filtered["timestamp"], y=filtered["buy_MA_24"], mode="lines", name="MA 24", line=dict(color="orange"))
    fig.add_scatter(x=filtered["timestamp"], y=filtered["buy_MA_120"], mode="lines", name="MA 120", line=dict(color="blue"))
    st.plotly_chart(fig, use_container_width=True)

    # 📤 Esportazione
    filtered_export = filtered.copy()
    filtered_export["timestamp"] = filtered_export["timestamp"].dt.tz_localize(None)  # ✅ Rimuove il fuso orario
    st.download_button("📄 Scarica CSV", filtered_export.to_csv(index=False), file_name=f"{asset}_data.csv")

    try:
        import io
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            filtered_export.to_excel(writer, index=False)
        st.download_button("📊 Scarica Excel", data=output.getvalue(), file_name=f"{asset}_data.xlsx")
    except Exception as e:
        st.warning(f"⚠️ Errore esportazione Excel: {e}")

except Exception as e:
    st.error(f"Errore nella dashboard: {e}")

import streamlit as st
import pandas as pd
import plotly.express as px
from supabase_utils import load_data
from io import BytesIO

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
    st.write(df)  # Mostra il contenuto del DataFrame per debug

    if df.empty or "asset_name" not in df.columns:
        st.error("⚠️ Nessun dato valido trovato. Controlla che Supabase abbia la colonna `asset_name` e che contenga dati.")
        st.stop()

    asset_names = df["asset_name"].dropna().unique()

    if len(asset_names) == 0:
        st.warning("⚠️ Nessun asset disponibile.")
        st.stop()

    asset = st.selectbox("Seleziona asset:", sorted(asset_names))
    filtered = df[df["asset_name"] == asset].copy()

    # Assicura che timestamp sia in formato datetime
    filtered["timestamp"] = pd.to_datetime(filtered["timestamp"])
    filtered.sort_values("timestamp", inplace=True)

    # Calcola medie mobili
    filtered["MA_24"] = filtered["buy"].rolling(window=24).mean()
    filtered["MA_120"] = filtered["buy"].rolling(window=120).mean()

    # Ultimo valore
    st.metric("Ultimo valore BUY (%)", f'{filtered.iloc[-1]["buy"]:.2f}')
    st.metric("Ultimo valore SELL (%)", f'{filtered.iloc[-1]["sell"]:.2f}')

    # 📈 Grafico con BUY, SELL, MA_24, MA_120
    fig = px.line(title=f"Trend BUY & SELL – {asset}")
    fig.add_scatter(x=filtered["timestamp"], y=filtered["buy"], mode="lines", name="BUY", line=dict(color="green"))
    fig.add_scatter(x=filtered["timestamp"], y=filtered["sell"], mode="lines", name="SELL", line=dict(color="red"))
    fig.add_scatter(x=filtered["timestamp"], y=filtered["MA_24"], mode="lines", name="MA 24", line=dict(color="blue"))
    fig.add_scatter(x=filtered["timestamp"], y=filtered["MA_120"], mode="lines", name="MA 120", line=dict(color="orange"))
    st.plotly_chart(fig, use_container_width=True)

    # ⬇️ Download CSV
    st.download_button("⬇️ Scarica CSV", data=filtered.to_csv(index=False), file_name=f"{asset}_data.csv", mime="text/csv")

    # ⬇️ Download Excel
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        filtered.to_excel(writer, index=False, sheet_name="Dati")
        writer.save()

    st.download_button(
        label="⬇️ Scarica Excel",
        data=excel_buffer.getvalue(),
        file_name=f"{asset}_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

except Exception as e:
    st.error(f"Errore nella dashboard: {e}")

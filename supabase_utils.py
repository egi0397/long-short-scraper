from supabase import create_client, Client
import pandas as pd
import streamlit as st

url = st.secrets["supabase"]["SUPABASE_URL"]
key = st.secrets["supabase"]["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

def load_data():
    try:
        response = supabase.table("tracked_values").select("*").order("timestamp", desc=True).execute()
        df = pd.DataFrame(response.data)
        return df
    except Exception as e:
        st.error(f"Errore caricando i dati da Supabase: {e}")
        return pd.DataFrame()

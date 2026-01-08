import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px
import requests

# --- ÁRFOLYAM LEKÉRÉS ---
def get_eur_huf():
    try:
        url = "https://open.er-api.com/v6/latest/EUR"
        response = requests.get(url).json()
        return response['rates']['HUF']
    except:
        return 400.0

# --- KONNEKCIÓ LÉTREHOZÁSA ---
conn = st.connection("gsheets", type=GSheetsConnection)

def get_data():
    return conn.read(ttl="0m") # Friss adatok olvasása

# --- BEÁLLÍTÁSOK ---
st.set_page_config(page_title="Andris & Zsóka Kassza", layout="wide")
px.defaults.template = "plotly_dark"
arfolyam = get_eur_huf()

tab1, tab2 = st.tabs(["📝 Könyvelés", "📊 Kimutatások"])

with tab1:
    st.subheader("💸 Új tétel rögzítése")
    with st.form("beviteli_iv", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            datum = st.date_input("Dátum", datetime.now())
            tipus = st.selectbox("Típus", ["📉 Kiadás", "📈 Bevétel", "💰 Megtakarítás"])
            szemely = st.selectbox("Ki rögzítette?", ["👤 Andris", "👤 Zsóka", "👥 Közös"])
        with col2:
            kategoria = st.selectbox("Kategória", ["🏠 Lakás", "🛒 Élelmiszer", "🏦 Hitel", "🚗 Autó", "🎬 Hobbi", "📦 Egyéb"])
            valuta = st.radio("Pénznem", ["HUF", "EUR"], horizontal=True)
            osszeg = st.number_input("Összeg", min_value=0.0)
            
        megjegyzes = st.text_input("Megjegyzés")
        mentes = st.form_submit_button("💾 Mentés")

    if mentes and osszeg > 0:
        final_osszeg = osszeg if valuta == "HUF" else osszeg * arfolyam
        uj_adat = pd.DataFrame([{
            "datum": datum.strftime("%Y-%m-%d"),
            "tipus": tipus,
            "szemely": szemely,
            "kategoria": kategoria,
            "osszeg": final_osszeg,
            "megjegyzes": f"{megjegyzes} [EUR: {osszeg}]" if valuta == "EUR" else megjegyzes
        }])
        
        regi_adatok = get_data()
        friss_df = pd.concat([regi_adatok, uj_adat], ignore_index=True)
        conn.update(data=friss_df)
        st.success("Adat elküldve a Google Táblázatba!")

with tab2:
    df = get_data()
    if not df.empty:
        st.dataframe(df.sort_values("datum", ascending=False), use_container_width=True)
        st.metric("Összes kiadás", f"{df[df['tipus'] == '📉 Kiadás']['osszeg'].sum():,.0f} Ft")

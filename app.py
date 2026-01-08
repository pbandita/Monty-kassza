import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

# --- BEÁLLÍTÁSOK ---
st.set_page_config(page_title="Monty Kassza", layout="wide", page_icon="🐾")

SHEET_ID = "1sk5Lg03WHEq-EtSrK9xSrtAwNAX4fh0_KULE37DraIQ"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# --- ADATOK BETÖLTÉSE ---
def load_data():
    try:
        # Közvetlen olvasás a Google-ből
        df = pd.read_csv(CSV_URL)
        if 'datum' in df.columns:
            df['datum'] = pd.to_datetime(df['datum']).dt.date
        return df
    except:
        return pd.DataFrame(columns=["datum", "tipus", "szemely", "kategoria", "osszeg", "megjegyzes"])

@st.cache_data(ttl=3600)
def get_eur_huf():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/EUR")
        return r.json()['rates']['HUF']
    except: return 410.0

arfolyam = get_eur_huf()
df = load_data()

# --- MEGJELENÍTÉS ---
st.title("🐾 Monty Kassza")

tab1, tab2, tab3 = st.tabs(["📊 Statisztika", "📝 Új tétel", "📅 Adatok"])

with tab1:
    if not df.empty:
        kiadas_sum = df[df['tipus'].str.contains("Kiadás", na=False)]['osszeg'].sum()
        bevetel_sum = df[df['tipus'].str.contains("Bevétel", na=False)]['osszeg'].sum()
        
        c1, c2 = st.columns(2)
        c1.metric("Összes kiadás", f"{kiadas_sum:,.0f} Ft")
        c2.metric("Összes bevétel", f"{bevetel_sum:,.0f} Ft")
        
        if kiadas_sum > 0:
            fig = px.pie(df[df['tipus'].str.contains("Kiadás", na=False)], 
                         values='osszeg', names='kategoria', hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Még nincsenek adatok a Google Táblázatban.")

with tab2:
    st.subheader("💰 Új rögzítés")
    with st.form("adat_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            d = st.date_input("Dátum", datetime.now())
            t = st.selectbox("Típus", ["📉 Kiadás", "📈 Bevétel"])
            s = st.selectbox("Ki?", ["👤 Andris", "👤 Zsóka", "👥 Közös"])
        with col2:
            k = st.selectbox("Kategória", ["🏠 Lakás", "🛒 Élelmiszer", "🚗 Autó", "🎬 Hobbi", "🐶 Monty", "📦 Egyéb"])
            v = st.radio("Pénznem", ["HUF", "EUR"], horizontal=True)
            o = st.number_input("Összeg", min_value=0.0)
            
        m = st.text_input("Megjegyzés")
        submit = st.form_submit_button("Mentés")
        
        if submit:
            final_o = o if v == "HUF" else o * arfolyam
            # Ez egy trükk: generálunk egy linket, amivel csak rá kell kattintani a mentéshez
            st.success(f"Adat előkészítve: {final_o:,.0f} Ft")
            st.info("Kattints a lenti gombra a Google Táblázatba íráshoz:")
            st.link_button("🚀 Végleges Mentés (Google Forms)", "https://docs.google.com/forms/d/e/IDE_JÖN_MAJD_A_FORMS_LINK/viewform")

with tab3:
    st.dataframe(df, use_container_width=True)

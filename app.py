import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

# --- ALAPBEÁLLÍTÁSOK ---
st.set_page_config(page_title="Monty Kassza", layout="wide", page_icon="🐾")

# A te táblázatod adatai
SHEET_ID = "1sk5Lg03WHEq-EtSrK9xSrtAwNAX4fh0_KULE37DraIQ"
# Ez a link közvetlenül CSV-ként hívja le az adatokat
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# --- ADATOK BETÖLTÉSE ---
def load_data():
    try:
        # Közvetlen beolvasás a Google-ből, cache nélkül, hogy mindig friss legyen
        df = pd.read_csv(CSV_URL)
        # Dátum formátum javítása
        if 'datum' in df.columns:
            df['datum'] = pd.to_datetime(df['datum']).dt.date
        return df
    except Exception as e:
        st.error(f"Hiba az adatok beolvasásakor: {e}")
        return pd.DataFrame(columns=["datum", "tipus", "szemely", "kategoria", "osszeg", "megjegyzes"])

# --- ÁRFOLYAM ---
@st.cache_data(ttl=3600)
def get_eur_huf():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/EUR")
        return r.json()['rates']['HUF']
    except:
        return 410.0

arfolyam = get_eur_huf()

# --- MEGJELENÍTÉS ---
st.title("🐾 Monty Kassza - Andris & Zsóka")

tab1, tab2, tab3 = st.tabs(["📊 Statisztika", "📝 Új tétel", "📅 Összes adat"])

df = load_data()

with tab1:
    if not df.empty:
        # Gyors mérőszámok
        kiadas_sum = df[df['tipus'].str.contains("Kiadás", na=False)]['osszeg'].sum()
        bevetel_sum = df[df['tipus'].str.contains("Bevétel", na=False)]['osszeg'].sum()
        
        c1, c2 = st.columns(2)
        c1.metric("Összes kiadás", f"{kiadas_sum:,.0f} Ft")
        c2.metric("Összes bevétel", f"{bevetel_sum:,.0f} Ft")
        
        # Grafikon
        if kiadas_sum > 0:
            fig = px.pie(df[df['tipus'].str.contains("Kiadás", na=False)], 
                         values='osszeg', names='kategoria', 
                         title="Kiadások megoszlása", hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Még nincsenek adatok a táblázatban.")

with tab2:
    st.subheader("💰 Új tranzakció rögzítése")
    st.write(f"ℹ️ Aktuális árfolyam: 1 EUR = {arfolyam:.1f} HUF")
    
    with st.form("adat_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            d = st.date_input("Dátum", datetime.now())
            t = st.selectbox("Típus", ["📉 Kiadás", "📈 Bevétel"])
            s = st.selectbox("Ki?", ["👤 Andris", "👤 Zsóka", "👥 Közös"])
        with col2:
            k = st.

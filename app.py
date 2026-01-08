import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

# --- BEÁLLÍTÁSOK ---
st.set_page_config(page_title="Monty Kassza", layout="wide", page_icon="💸")

# Táblázat adatai
SHEET_ID = "1sk5Lg03WHEq-EtSrK9xSrtAWnAX4fhO_KULE37DraIQ"
CSV_URL = f"https://docs.google.com/spreadsheets/d/1sk5LgO3WHEq-EtSrK9xSrtAWnAX4fhO_KULE37DraIQ/export?format=csv"

# --- FIX KIADÁSOK LISTÁJA ---
# Ide írd be a havi fixeket, amiket ellenőrizni akartok
FIX_KIADASOK = ["Lakbér", "Közös költség", "Internet/TV", "Netflix", "Spotify", "Villany"]

# --- ADATOK BETÖLTÉSE ---
def load_data():
    try:
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
st.title("💸 Monty Kassza")

tab1, tab2, tab3 = st.tabs(["📊 Statisztika", "📝 Új tétel", "📅 Fix kiadások & Adatok"])

with tab1:
    if not df.empty:
        kiadasok = df[df['tipus'].str.contains("Kiadás", na=False)]
        kiadas_sum = kiadasok['osszeg'].sum()
        bevetel_sum = df[df['tipus'].str.contains("Bevétel", na=False)]['osszeg'].sum()
        
        c1, c2 = st.columns(2)
        c1.metric("Összes kiadás (HUF)", f"{kiadas_sum:,.0f} Ft")
        c2.metric("Összes bevétel (HUF)", f"{bevetel_sum:,.0f} Ft")
        
        fig = px.bar(kiadasok.groupby('kategoria')['osszeg'].sum().reset_index(), 
                     x='kategoria', y='osszeg', color='kategoria', title="Kiadások megoszlása")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Még nincsenek adatok a táblázatban.")

with tab2:
    st.subheader("Új tranzakció rögzítése")
    st.write(f"ℹ️ Aktuális árfolyam: 1 EUR = {arfolyam:.1f} HUF")
    
    with st.form("adat_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            d = st.date_input("Dátum", datetime.now())
            t = st.selectbox("Típus", ["📉 Kiadás", "📈 Bevétel"])
            s = st.selectbox("Ki?", ["👤 Andris", "👤 Zsóka", "👥 Közös"])
        with col2:
            k = st.selectbox("Kategória", ["🏠 Lakás", "🛒 Élelmiszer", "🚗 Autó", "🎬 Hobbi", "📦 Egyéb"])
            v = st.radio("Pénznem", ["HUF", "EUR"], horizontal=True)
            o = st.number_input("Összeg", min_value=0.0)
            
        m = st.text_input("Megjegyzés (pl. Netflix)")
        
        if st.form_submit_button("Adat rögzítése"):
            st.info("Kattints a Google Forms linkre a mentéshez!")
            st.link_button("🚀 IRÁNY A MENTÉS", "https://docs.google.com/forms/d/e/A_TE_FORMS_KODOD/viewform")

with tab3:
    st.subheader("📌 Havi fix kiadások ellenőrzése")
    # Megnézzük az aktuális hónapban mi lett már kifizetve
    ma = datetime.now()
    if not df.empty:
        df['datum'] = pd.to_datetime(df['datum'])
        e_havi = df[(df['datum'].dt.month == ma.month) & (df['datum'].dt.year == ma.year)]
        
        # Ellenőrző lista
        cols = st.columns(len(FIX_KIADASOK))
        for i, fix in enumerate(FIX_KIADASOK):
            # Megnézzük a megjegyzésben vagy kategóriában szerepel-e a fix kiadás neve
            pipa = any(e_havi['megjegyzes'].str.contains(fix, case=False, na=False)) or \
                   any(e_havi['kategoria'].str.contains(fix, case=False, na=False))
            
            if pipa:
                cols[i].success(f"✅ {fix}")
            else:
                cols[i].error(f"❌ {fix}")
    
    st.divider()
    st.subheader("📋 Összes tranzakció")
    st.dataframe(df.sort_values(by="datum", ascending=False), use_container_width=True)

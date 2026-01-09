import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta
import sqlite3
import random

# --- 0. ALAPBEÁLLÍTÁSOK ---
st.set_page_config(page_title="Andris & Zsóka Kassza", layout="wide", page_icon="🐲")
px.defaults.template = "plotly_dark"

# Google Táblázat adatok
SHEET_ID = "1sk5Lg03WHEq-EtSrK9xSrtAWnAX4fh0_KULE37DraIQ"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxyHCbk2E4E01AQflCl4K9qYH-GXPSuzHHU0yMS7XhATHkBnb7Gy87EFcdGDrAmrnU68w/exec"

# --- 1. ADATBÁZIS ÉS ADATOK BETÖLTÉSE ---
def init_db():
    conn = sqlite3.connect('tervek.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ismetlodo 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nev TEXT, kategoria TEXT, osszeg REAL, utolso_datum TEXT)''')
    conn.commit()
    conn.close()

def load_data():
    try:
        refresh_url = f"{CSV_URL}&cache_buster={datetime.now().timestamp()}"
        df = pd.read_csv(refresh_url)
        if 'datum' in df.columns:
            df['datum'] = pd.to_datetime(df['datum']).dt.date
        if 'osszeg' in df.columns:
            df['osszeg'] = pd.to_numeric(df['osszeg'], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame(columns=["datum", "tipus", "szemely", "kategoria", "osszeg", "megjegyzes"])

@st.cache_data(ttl=600)
def get_eur_huf():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/EUR")
        return r.json()['rates']['HUF']
    except: return 410.0

init_db()
arfolyam = get_eur_huf()
df = load_data()

# --- 2. AUTOMATIKUS ÜTEMEZÉS ---
def auto_check():
    conn = sqlite3.connect('tervek.db')
    szabalyok = pd.read_sql_query("SELECT * FROM ismetlodo", conn)
    ma = datetime.now().date()
    
    for _, sz in szabalyok.iterrows():
        utolso = datetime.strptime(sz['utolso_datum'], "%Y-%m-%d").date()
        kovetkezo = (utolso.replace(day=1) + timedelta(days=32)).replace(day=min(utolso.day, 28))
        
        if kovetkezo <= ma:
            tipus = "💰 Megtakarítás" if sz['kategoria'] == "💰 Megtakarítás" else "📉 Kiadás"
            adat = {
                "datum": kovetkezo.strftime("%Y-%m-%d"),
                "tipus": tipus,
                "szemely": "Automata",
                "kategoria": sz['kategoria'],
                "osszeg": int(sz['osszeg']),
                "megjegyzes": f"FIX: {sz['nev']}"
            }
            try:
                requests.post(SCRIPT_URL, json=adat)
                conn.execute("UPDATE ismetlodo SET utolso_datum = ? WHERE id = ?", (kovetkezo.strftime("%Y-%m-%d"), sz['id']))
            except: pass
    conn.commit()
    conn.close()

auto_check()

# --- 3. FÜLEK ---
tab1, tab2, tab3 = st.tabs(["⚔️ Könyvelés", "🔮 Kimutatások", "📜 Naptár & Áttekintés"])

with tab1:
    col_bal, col_jobb = st.columns(2)
    
    with col_bal:
        st.subheader("📦 Mimic Láda (Új tétel)")
        with st.form("beviteli_iv", clear_on_submit=True):
            datum = st.date_input("Dátum", datetime.now())
            tipus = st.selectbox("Típus", ["📉 Kiadás", "📈 Bevétel", "💰 Megtakarítás"])
            szemely = st.selectbox("Ki rögzítette?", ["👤 Andris", "👤 Zsóka", "👥 Közös"])
            kategoria = st.selectbox("Kategória", ["🏠 Lakás/Rezsi", "🛒 Élelmiszer", "🏦 Hitel", "🚗 Közlekedés", "🐶 Monty", "💰 Megtakarítás", "📦 Egyéb"])
            v_col1, v_col2 = st.columns([1,2])
            valuta = v_col1.selectbox("Pénznem", ["HUF", "EUR"])
            nyers_osszeg = v_col2.number_input("Összeg", min_value=0.0)
            megjegyzes = st.text_input("Megjegyzés")
            
            # Easter Egg: Mentés gomb Mimic-kel
            if st.form_submit_button("👅 ELNYELI AZ ARANYAT (MENTÉS)", use_container_width=True):
                final_osszeg = int(nyers_osszeg if valuta == "HUF" else nyers_osszeg * arfolyam)

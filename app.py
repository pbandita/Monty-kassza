import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta
import sqlite3

# --- 0. ALAPBEÁLLÍTÁSOK ---
st.set_page_config(page_title="Andris & Zsóka Kassza", layout="wide", page_icon="💰")
px.defaults.template = "plotly_dark"

# Ellenőrizd, hogy ez a ID pontosan egyezik-e a táblázatod URL-jében lévővel!
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
        # Frissítés kényszerítése cache-busterrel
        r_url = f"{CSV_URL}&cb={datetime.now().timestamp()}"
        df = pd.read_csv(r_url)
        # Oszlopnevek tisztítása (szóközök eltávolítása)
        df.columns = [c.strip().lower() for c in df.columns]
        
        if 'datum' in df.columns:
            df['datum'] = pd.to_datetime(df['datum']).dt.date
        if 'osszeg' in df.columns:
            df['osszeg'] = pd.to_numeric(df['osszeg'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        return pd.DataFrame(columns=["datum", "tipus", "szemely", "kategoria", "osszeg", "megjegyzes"])

init_db()
df = load_data()

# --- 2. FÜLEK ---
tab1, tab2, tab3 = st.tabs(["📝 Könyvelés", "📊 Kimutatások", "📅 Naptár & Áttekintés"])

with tab1:
    st.subheader("🖋️ Tétel rögzítése")
    with st.form("beviteli_iv", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            datum = st.date_input("Dátum", datetime.now())
            tipus = st.selectbox("Típus", ["📉 Kiadás", "📈 Bevétel", "💰 Megtakarítás"])
            szemely = st.selectbox("Ki rögzítette?", ["👤 Andris", "👤 Zsóka", "👥 Közös"])
        with col2:
            kategoria = st.selectbox("Kategória", ["🏠 Lakás/Rezsi", "🛒 Élelmiszer", "🏦 Hitel", "🚗 Közlekedés", "🐶 Monty", "💰 Megtakarítás", "📦 Egyéb"])
            nyers_osszeg = st.number_input("Összeg (HUF)", min_value=0.0)
            megjegyzes = st.text_input("Megjegyzés")
            
        if st.form_submit_button("💾 MENTÉS A TÁBLÁZATBA", use_container_width=True):
            if nyers_osszeg > 0:
                adat = {
                    "datum": datum.strftime("%Y-%m-%d"),
                    "tipus": tipus,
                    "szemely": szemely,
                    "kategoria": kategoria,
                    "osszeg": int(nyers_osszeg),
                    "megjegyzes": megjegyzes
                }
                res = requests.post(SCRIPT_URL, json=adat)
                if res.status_code == 200:
                    st.success("Sikeres mentés! Frissítsd az oldalt a látványhoz.")
                    st.balloons()
            else:
                st.warning("Adj meg egy összeget!")

with tab2:
    st.subheader("📊 Kimutatások")
    if st.button("🔄 Adatok frissítése"):
        st.rerun()

    if not df.empty and len(df) > 0:
        kiadas_df = df[df['tipus'].str.contains("Kiadás|Megtakarítás", na=False)]
        if not kiadas_df.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(px.pie(kiadas_df, values='osszeg', names='kategoria', title="Költések aránya", hole=0.4), use_container_width=True)
            with c2:
                # Havi trend
                df['honap'] = pd.to_datetime(df['datum']).dt.strftime('%Y-%m')
                trend = kiadas_df.groupby('kategoria')['osszeg'].sum().reset_index()
                st.plotly_chart(px.bar(trend, x='kategoria', y='osszeg', title="Összesített költés"), use_container_width=True)
        else:
            st.info("Nincs rögzített kiadás.")
    else:
        st.error("Nem sikerült elérni a táblázatot. Ellenőrizd a Google Megosztási beállításokat!")

with tab3:
    st.subheader("📅 Utolsó tételek")
    st.dataframe(df.sort_values('datum', ascending=False).head(20), use_container_width=True)

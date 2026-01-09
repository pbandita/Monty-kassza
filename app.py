import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
import sqlite3
import io

# --- 0. ALAPBEÁLLÍTÁSOK ---
st.set_page_config(page_title="Andris & Zsóka Kassza", layout="wide", page_icon="🐲")
px.defaults.template = "plotly_dark"

# ELÉRÉSEK
SHEET_ID = "2PACX-1vSj9ExuUUiQKDmQBZt7KYfFatjfROEW1dj-Uazcf7zh33UyUzVPxlxeTvQ5n5bVMrPVz8ayFCPk-fJz"
# Közvetlen CSV lekérdezési link
DIRECT_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxyHCbk2E4E01AQflCl4K9qYH-GXPSuzHHU0yMS7XhATHkBnb7Gy87EFcdGDrAmrnU68w/exec"

# --- 1. ADATOK BETÖLTÉSE ---
def load_data():
    try:
        # Cache-buster hozzáadása a friss adatokért
        r_url = f"{DIRECT_CSV_URL}&cb={datetime.now().timestamp()}"
        response = requests.get(r_url)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            # Oszlopnevek tisztítása
            df.columns = [c.strip().lower() for c in df.columns]
            if 'datum' in df.columns:
                df['datum'] = pd.to_datetime(df['datum']).dt.date
            if 'osszeg' in df.columns:
                df['osszeg'] = pd.to_numeric(df['osszeg'], errors='coerce').fillna(0)
            return df
        else:
            return pd.DataFrame()
    except:
        return pd.DataFrame()

def init_db():
    conn = sqlite3.connect('tervek.db')
    conn.execute('CREATE TABLE IF NOT EXISTS ismetlodo (id INTEGER PRIMARY KEY, nev TEXT, kategoria TEXT, osszeg REAL, utolso_datum TEXT)')
    conn.close()

init_db()
df = load_data()

# --- 2. FÜLEK ---
tab1, tab2, tab3 = st.tabs(["⚔️ Könyvelés", "🔮 Kimutatások", "📜 Naptár & Fixek"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🖋️ Tétel rögzítése")
        with st.form("beviteli_iv", clear_on_submit=True):
            datum = st.date_input("Dátum", datetime.now())
            tipus = st.selectbox("Típus", ["📉 Kiadás", "📈 Bevétel", "💰 Megtakarítás"])
            szemely = st.selectbox("Ki rögzítette?", ["👤 Andris", "👤 Zsóka", "👥 Közös"])
            kategoria = st.selectbox("Kategória", ["🏠 Lakás/Rezsi", "🛒 Élelmiszer", "🏦 Hitel", "🚗 Közlekedés", "🐶 Monty", "💰 Megtakarítás", "📦 Egyéb"])
            nyers_osszeg = st.number_input("Összeg (HUF)", min_value=0)
            megjegyzes = st.text_input("Megjegyzés")
            
            if st.form_submit_button("📦 MENTÉS (MIMIC LÁDA)"):
                if nyers_osszeg > 0:
                    adat = {"datum": datum.strftime("%Y-%m-%d"), "tipus": tipus, "szemely": szemely, "kategoria": kategoria, "osszeg": int(nyers_osszeg), "megjegyzes": megjegyzes}
                    res = requests.post(SCRIPT_URL, json=adat)
                    if res.status_code == 200:
                        st.success("A Mimic elnyelte az aranyat! 👅📦")
                else:
                    st.warning("Üres kasszát nem rögzítünk!")

with tab2:
    st.subheader("🔮 Kimutatások")
    if st.button("🔄 Adatok frissítése a Google-ből"):
        st.cache_data.clear()
        st.rerun()

    if not df.empty and len(df) > 0:
        kiadas_df = df[df['tipus'].str.contains("Kiadás|Megtakarítás", na=False)]
        if not kiadas_df.empty:
            c_g1, c_g2 = st.columns(2)
            with c_g1:
                st.plotly_chart(px.pie(kiadas_df, values='osszeg', names='kategoria', hole=0.4, title="Kiadások aránya"), use_container_width=True)
            with c_g2:
                df['honap'] = pd.to_datetime(df['datum']).dt.strftime('%Y-%m')
                trend = kiadas_df.groupby('honap')['osszeg'].sum().reset_index()
                st.plotly_chart(px.line(trend, x='honap', y='osszeg', title="Havi trend", markers=True), use_container_width=True)
        else:
            st.info("Nincs rögzített kiadás.")
    else:
        st.error("A kincstár üres! Állítsd a Google közzétételt CSV formátumra!")

with tab3:
    st.subheader("📜 Naptár & Áttekintés")
    if not df.empty:
        st.dataframe(df.sort_values('datum', ascending=False), use_container_width=True)

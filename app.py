import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import requests
import urllib.parse # ÚJ: A link kódolásához

# --- ÁRFOLYAM ÉS ADATBÁZIS (VÁLTOZATLAN) ---
def get_eur_huf():
    try:
        url = "https://open.er-api.com/v6/latest/EUR"
        return requests.get(url).json()['rates']['HUF']
    except: return 400.0

# --- FORMÁZOTT MENTÉS GOMB ---
with st.form("beviteli_iv", clear_on_submit=True):
    datum = st.date_input("Dátum", datetime.now())
    tipus = st.selectbox("Típus", ["📉 Kiadás", "📈 Bevétel", "💰 Megtakarítás"])
    szemely = st.selectbox("Ki rögzítette?", ["👤 Andris", "👤 Zsóka", "👥 Közös"])
    kategoria = st.selectbox("Kategória", ["🏠 Lakás/Rezsi", "🛒 Élelmiszer", "🚗 Közlekedés", "🐶 Monty", "📦 Egyéb"])
    
    c_p1, c_p2 = st.columns([1, 3])
    valuta = c_p1.selectbox("Pénznem", ["HUF", "EUR"])
    nyers_osszeg = c_p2.number_input("Összeg", min_value=0.0, step=10.0)
    
    megjegyzes = st.text_input("Megjegyzés")
    mentes = st.form_submit_button("💾 Adat előkészítése", use_container_width=True)

if mentes and nyers_osszeg > 0:
    final_osszeg = nyers_osszeg if valuta == "HUF" else nyers_osszeg * get_eur_huf()
    
    # --- GOOGLE FORM ELÉRÉSI KÓD ÉS AUTOMATIZÁLÁS ---
   if mentes and nyers_osszeg > 0:
    final_osszeg = nyers_osszeg if valuta == "HUF" else nyers_osszeg * arfolyam
    
    # ADATOK ÖSSZEKÉSZÍTÉSE
    uj_adat = {
        "datum": datum.strftime("%Y-%m-%d"),
        "tipus": tipus,
        "szemely": szemely,
        "kategoria": kategoria,
        "osszeg": int(final_osszeg),
        "megjegyzes": megjegyzes
    }

    # KÜLDÉS A SCRIPTNEK
    SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzVwCzkVtBBksB81JOA_CAgfWEgO1xIEsVxTd4rZAPmSgTTJuORLCdLM8xyiR4lDKYQ2A/exec"
    
    try:
        response = requests.post(SCRIPT_URL, json=uj_adat)
        if response.status_code == 200:
            st.success(f"✅ Sikeresen mentve a táblázatba: {final_osszeg:,.0f} Ft")
            st.balloons() # Egy kis ünneplés Zsókának és neked :)
        else:
            st.error("Hiba történt a küldéskor.")
    except Exception as e:
        st.error(f"Nem sikerült elérni a Google-t: {e}")
    # Ide írd be az entry kódokat, amiket a pre-filled linkből látsz
    params = {
        "entry.12345678": datum.strftime("%Y-%m-%d"),
        "entry.87654321": tipus,
        "entry.11223344": szemely,
        "entry.55667788": kategoria,
        "entry.99001122": int(final_osszeg),
        "entry.33445566": megjegyzes
    }
    
    # Ez generálja le a kész, kitöltött linket
    full_url = f"{base_url}?{urllib.parse.urlencode(params)}"
    
    st.success(f"✅ Készen áll a mentésre: {final_osszeg:,.0f} Ft")
    
    st.markdown(f"""
        <a href="{full_url}" target="_blank">
            <button style="width:100%; height:60px; background-color:#2e7d32; color:white; border:none; border-radius:10px; font-size:18px; font-weight:bold; cursor:pointer;">
                🚀 KÜLDÉS A KÖZÖS TÁBLÁZATBA
            </button>
        </a>
    """, unsafe_allow_html=True)
    st.caption("A gomb megnyitja az űrlapot, ahol az adatok már be lesznek írva, csak a 'Küldés' gombot kell megnyomnod.")

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import requests

# --- 0. ÁRFOLYAM LEKÉRÉS ---
def get_eur_huf():
    try:
        url = "https://open.er-api.com/v6/latest/EUR"
        response = requests.get(url).json()
        return response['rates']['HUF']
    except:
        return 410.0  # Biztonsági tartalék

arfolyam = get_eur_huf()

# --- 1. BEVITELI FELÜLET ---
st.subheader("💸 Új tétel rögzítése")
with st.form("beviteli_iv", clear_on_submit=True):
    datum = st.date_input("Dátum", datetime.now())
    tipus = st.selectbox("Típus", ["📉 Kiadás", "📈 Bevétel", "💰 Megtakarítás"])
    szemely = st.selectbox("Ki rögzítette?", ["👤 Andris", "👤 Zsóka", "👥 Közös"])
    kategoria = st.selectbox("Kategória", ["🏠 Lakás/Rezsi", "🛒 Élelmiszer", "🚗 Közlekedés", "🐶 Monty", "📦 Egyéb"])
    
    c_p1, c_p2 = st.columns([1, 3])
    valuta = c_p1.selectbox("Pénznem", ["HUF", "EUR"])
    nyers_osszeg = c_p2.number_input("Összeg", min_value=0.0, step=100.0)
    
    megjegyzes = st.text_input("Megjegyzés")
    mentes = st.form_submit_button("💾 MENTÉS A TÁBLÁZATBA", use_container_width=True)

if mentes and nyers_osszeg > 0:
    # Átváltás, ha EUR
    final_osszeg = nyers_osszeg if valuta == "HUF" else nyers_osszeg * arfolyam
    
    # Adatok előkészítése a Google Scriptnek
    uj_adat = {
        "datum": datum.strftime("%Y-%m-%d"),
        "tipus": tipus,
        "szemely": szemely,
        "kategoria": kategoria,
        "osszeg": int(final_osszeg),
        "megjegyzes": megjegyzes
    }

    # A TE SCRIPT URL-ED
    SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzVwCzkVtBBksB81JOA_CAgfWEgO1xIEsVxTd4rZAPmSgTTJuORLCdLM8xyiR4lDKYQ2A/exec"
    
    try:
        # Ez a sor küldi el az adatot a háttérben a Google Táblázatba
        response = requests.post(SCRIPT_URL, json=uj_adat)
        
        if response.status_code == 200:
            st.success(f"✅ Sikeresen mentve a Google Táblázatba: {final_osszeg:,.0f} Ft")
            st.balloons()
            
            # Opcionális: Mentés a helyi adatbázisba is, ha akarod használni a belső statisztikát
            conn = sqlite3.connect('penzugyek.db')
            conn.execute("INSERT INTO tranzakciok (datum, tipus, szemely, kategoria, osszeg, megjegyzes) VALUES (?,?,?,?,?,?)", 
                      (uj_adat["datum"], uj_adat["tipus"], uj_adat["szemely"], uj_adat["kategoria"], uj_adat["osszeg"], uj_adat["megjegyzes"]))
            conn.commit()
            conn.close()
        else:
            st.error(f"Szerver hiba ({response.status_code}). Ellenőrizd a Script 'Deploy' beállításait!")
            
    except Exception as e:
        st.error(f"Hiba történt: {e}")

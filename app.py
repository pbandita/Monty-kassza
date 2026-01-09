import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta
import sqlite3
import io

# --- 0. ALAPBEÁLLÍTÁSOK ---
st.set_page_config(page_title="Andris & Zsóka Kassza", layout="wide", page_icon="💰")
px.defaults.template = "plotly_dark"

SHEET_ID = "1sk5LgO3WHEq-EtSrK9xSrtAWnAX4fhO_KULE37DraIQ"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxyHCbk2E4E01AQflCl4K9qYH-GXPSuzHHU0yMS7XhATHkBnb7Gy87EFcdGDrAmrnU68w/exec"

# --- 1. ADATOK BETÖLTÉSE ---
def load_data():
    try:
        r_url = f"{CSV_URL}&cb={datetime.now().timestamp()}"
        response = requests.get(r_url)
        if response.status_code == 200:
            # Itt adtuk meg az encoding='utf-8'-at az ékezetek miatt
            raw_data = response.content.decode('utf-8')
            df = pd.read_csv(io.StringIO(raw_data))
            
            # Oszlopnevek tisztítása
            df.columns = [c.strip().lower() for c in df.columns]
            
            if 'datum' in df.columns:
                df['datum'] = pd.to_datetime(df['datum']).dt.date
            if 'osszeg' in df.columns:
                df['osszeg'] = pd.to_numeric(df['osszeg'], errors='coerce').fillna(0)
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame(columns=["datum", "tipus", "szemely", "kategoria", "osszeg", "megjegyzes"])

df = load_data()

# --- 2. FÜLEK ---
tab1, tab2, tab3 = st.tabs(["📝 Könyvelés", "📊 Kimutatások", "📅 Naptár"])

with tab1:
    st.subheader("Új tétel rögzítése")
    with st.form("beviteli_iv", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            datum = st.date_input("Dátum", datetime.now())
            tipus_valasztott = st.selectbox("Típus", ["📉 Kiadás", "📈 Bevétel", "💰 Megtakarítás"])
            szemely = st.selectbox("Személy", ["👤 Andris", "👤 Zsóka", "👥 Közös"])
        with col2:
            kategoria = st.selectbox("Kategória", ["🏠 Lakás/Rezsi", "🛒 Élelmiszer", "🏦 Hitel", "🚗 Közlekedés", "🐶 Monty", "💰 Megtakarítás", "📦 Egyéb"])
            osszeg = st.number_input("Összeg (HUF)", min_value=0)
            megjegyzes = st.text_input("Megjegyzés")
            
        if st.form_submit_button("MENTÉS"):
            if osszeg > 0:
                adat = {
                    "datum": datum.strftime("%Y-%m-%d"),
                    "tipus": tipus_valasztott,
                    "szemely": szemely,
                    "kategoria": kategoria,
                    "osszeg": int(osszeg),
                    "megjegyzes": megjegyzes
                }
                requests.post(SCRIPT_URL, json=adat)
                st.success("Adat elküldve! Frissítsd az oldalt 1 perc múlva.")
                st.rerun()

with tab2:
    st.subheader("Pénzügyi kimutatások")
    
    if st.button("🔄 Adatok frissítése"):
        st.rerun()

    if df.empty:
        st.error("A táblázat üres vagy nem elérhető!")
    else:
        df['tipus_clean'] = df['tipus'].astype(str).str.lower()
        kiadas_mask = df['tipus_clean'].str.contains("kiad|megtak", na=False)
        kiadas_df = df[kiadas_mask].copy()

        if not kiadas_df.empty:
            c1, c2 = st.columns(2)
            with c1:
                # Szebb kördiagram
                fig_pie = px.pie(kiadas_df, values='osszeg', names='kategoria', 
                                 title="Kiadások megoszlása",
                                 color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_pie, use_container_width=True)
            with c2:
                # Szebb trendvonal
                kiadas_df['honap'] = pd.to_datetime(kiadas_df['datum']).dt.strftime('%Y-%m')
                trend = kiadas_df.groupby('honap')['osszeg'].sum().reset_index()
                fig_line = px.line(trend, x='honap', y='osszeg', title="Havi költés alakulása", 
                                   markers=True, line_shape="spline")
                st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.warning("Nincs megjeleníthető kiadás.")

with tab3:
    st.subheader("Tranzakciók listája")
    if not df.empty:
        # A dataframe-ben is jobban fognak festeni az ékezetek
        st.dataframe(df.sort_values('datum', ascending=False), use_container_width=True)

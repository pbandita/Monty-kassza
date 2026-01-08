import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
import urllib.parse

# --- 0. ALAPBEÁLLÍTÁSOK ---
st.set_page_config(page_title="Andris & Zsóka Kassza", layout="wide", page_icon="💰")
px.defaults.template = "plotly_dark"

# Google Táblázat CSV elérése (Olvasáshoz)
SHEET_ID = "1sk5Lg03WHEq-EtSrK9xSrtAwNAX4fh0_KULE37DraIQ"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
# A TE APPS SCRIPT URL-ED (Íráshoz)
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzVwCzkVtBBksB81JOA_CAgfWEgO1xIEsVxTd4rZAPmSgTTJuORLCdLM8xyiR4lDKYQ2A/exec""

# --- 1. ADATOK BETÖLTÉSE ---
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

# --- 2. FÜLEK ---
tab1, tab2, tab3 = st.tabs(["📝 Könyvelés", "📊 Kimutatások", "📅 Naptár & Fixek"])

with tab1:
    st.subheader("💸 Új tétel rögzítése")
    with st.form("beviteli_iv", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            datum = st.date_input("Dátum", datetime.now())
            tipus = st.selectbox("Típus", ["📉 Kiadás", "📈 Bevétel", "💰 Megtakarítás"])
            szemely = st.selectbox("Ki rögzítette?", ["👤 Andris", "👤 Zsóka", "👥 Közös"])
        with col2:
            kategoria = st.selectbox("Kategória", ["🏠 Lakás/Rezsi", "🛒 Élelmiszer", "🏦 Hitel", "🚗 Közlekedés", "🐶 Monty", "🎬 Szórakozás", "📦 Egyéb"])
            v_col1, v_col2 = st.columns([1,2])
            valuta = v_col1.selectbox("Pénznem", ["HUF", "EUR"])
            nyers_osszeg = v_col2.number_input("Összeg", min_value=0.0)
        
        megjegyzes = st.text_input("Megjegyzés")
        mentes = st.form_submit_button("💾 MENTÉS A TÁBLÁZATBA", use_container_width=True)

    if mentes and nyers_osszeg > 0:
        final_osszeg = int(nyers_osszeg if valuta == "HUF" else nyers_osszeg * arfolyam)
        uj_adat = {
            "datum": datum.strftime("%Y-%m-%d"),
            "tipus": tipus,
            "szemely": szemely,
            "kategoria": kategoria,
            "osszeg": final_osszeg,
            "megjegyzes": megjegyzes
        }
        try:
            res = requests.post(SCRIPT_URL, json=uj_adat)
            if res.status_code == 200:
                st.success(f"✅ Mentve: {final_osszeg:,.0f} Ft")
                st.balloons()
                st.info("Frissítsd az oldalt a grafikonokhoz!")
        except:
            st.error("Hiba a mentés során!")

with tab2:
    st.subheader("📊 Kimutatások")
    if not df.empty:
        # Időalapú szűréshez
        df['datum'] = pd.to_datetime(df['datum'])
        df['Honap'] = df['datum'].dt.strftime('%Y-%m')
        
        c1, c2, c3 = st.columns(3)
        kiadas_df = df[df['tipus'].str.contains("Kiadás", na=False)]
        bevetel_sum = df[df['tipus'].str.contains("Bevétel", na=False)]['osszeg'].sum()
        kiadas_sum = kiadas_df['osszeg'].sum()
        
        c1.metric("Összes Bevétel", f"{bevetel_sum:,.0f} Ft")
        c2.metric("Összes Kiadás", f"{kiadas_sum:,.0f} Ft")
        c3.metric("Egyenleg", f"{(bevetel_sum - kiadas_sum):,.0f} Ft")

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.write("🍕 **Kiadások aránya**")
            fig_pie = px.pie(kiadas_df, values='osszeg', names='kategoria', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col_g2:
            st.write("📈 **Havi trendek kategóriánként**")
            trend_data = kiadas_df.groupby(['Honap', 'kategoria'])['osszeg'].sum().reset_index()
            fig_line = px.line(trend_data, x="Honap", y="osszeg", color="kategoria", markers=True)
            st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("Még nincsenek adatok a statisztikához.")

with tab3:
    st.subheader("📅 Naptár és Fixek")
    
    # FIX KIADÁSOK ELLENŐRZÉSE
    fix_lista = ["Lakbér", "Hitel", "Internet", "Netflix", "Villany"]
    ma = datetime.now()
    e_havi = df[(pd.to_datetime(df['datum']).dt.month == ma.month)] if not df.empty else pd.DataFrame()
    
    st.write(f"**{ma.strftime('%Y. %B')}** fix tételek állapota:")
    cols = st.columns(len(fix_lista))
    for i, fix in enumerate(fix_lista):
        pipa = any(e_havi['megjegyzes'].str.contains(fix, case=False, na=False)) if not e_havi.empty else False
        if pipa: cols[i].success(f"✅ {fix}")
        else: cols[i].error(f"❌ {fix}")
    
    st.divider()
    
    # EGYSZERŰSÍTETT NAPTÁR LISTA
    st.write("📅 **Időrendi áttekintés**")
    if not df.empty:
        df_sorted = df.sort_values('datum', ascending=False)
        for _, sor in df_sorted.head(10).iterrows():
            st.text(f"{sor['datum'].strftime('%m.%d')} | {sor['osszeg']:,.0f} Ft | {sor['kategoria']} ({sor['megjegyzes']})")
    else:
        st.write("A táblázat üres.")

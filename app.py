import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta
import io

# --- 0. ALAPBEÁLLÍTÁSOK ---
st.set_page_config(page_title="Andris & Zsóka Kassza", layout="wide", page_icon="💰")
px.defaults.template = "plotly_dark"

SHEET_ID = "1sk5LgO3WHEq-EtSrK9xSrtAWnAX4fhO_KULE37DraIQ"
# FONTOS: Ellenőrizd a gid-eket a böngészőben!
CSV_URL_MAIN = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
CSV_URL_FIXEK = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1493472585" 

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxyHCbk2E4E01AQflCl4K9qYH-GXPSuzHHU0yMS7XhATHkBnb7Gy87EFcdGDrAmrnU68w/exec"

def load_sheet(url):
    try:
        r_url = f"{url}&cb={datetime.now().timestamp()}"
        response = requests.get(r_url, timeout=10)
        if response.status_code == 200:
            raw_data = response.content.decode('utf-8')
            df = pd.read_csv(io.StringIO(raw_data))
            df.columns = [c.strip().lower() for c in df.columns]
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

df_main = load_sheet(CSV_URL_MAIN)
df_fixek = load_sheet(CSV_URL_FIXEK)

# --- FELÜLET ---
tab1, tab2, tab3 = st.tabs(["📝 Könyvelés", "📊 Kimutatások", "📅 Naptár & Fixek"])

with tab1:
    col_bal, col_jobb = st.columns(2)
    with col_bal:
        st.subheader("🖋️ Egyszeri tétel")
        with st.form("beviteli_iv", clear_on_submit=True):
            datum = st.date_input("Dátum", datetime.now())
            tipus = st.selectbox("Típus", ["📉 Kiadás", "📈 Bevétel", "💰 Megtakarítás"])
            szemely = st.selectbox("Ki?", ["👤 Andris", "👤 Zsóka", "👥 Közös"])
            kategoria = st.selectbox("Kategória", ["🏠 Lakás/Rezsi", "🛒 Élelmiszer", "🏦 Hitel", "🚗 Közlekedés", "🐶 Monty", "💰 Megtakarítás", "📦 Egyéb"])
            osszeg = st.number_input("Összeg (HUF)", min_value=0)
            megjegyzes = st.text_input("Megjegyzés")
            if st.form_submit_button("MENTÉS"):
                res = requests.post(SCRIPT_URL, json={
                    "is_fix": False, "datum": str(datum), "tipus": tipus, 
                    "szemely": szemely, "kategoria": kategoria, "osszeg": int(osszeg), "megjegyzes": megjegyzes
                })
                st.success("Siker!")
                st.rerun()

    with col_jobb:
        st.subheader("🔁 Új fix ütemezése")
        with st.form("fix_form", clear_on_submit=True):
            f_nev = st.text_input("Megnevezés")
            f_kat = st.selectbox("Kategória ", ["🏠 Lakás/Rezsi", "🏦 Hitel", "💰 Megtakarítás", "📦 Egyéb"])
            f_osszeg = st.number_input("Havi összeg", min_value=0)
            f_datum = st.date_input("Kezdőnap", datetime.now())
            if st.form_submit_button("FIX RÖGZÍTÉSE"):
                res = requests.post(SCRIPT_URL, json={
                    "is_fix": True, "nev": f_nev, "kategoria": f_kat, "osszeg": int(f_osszeg), "datum": str(f_datum)
                })
                st.success("Fix tétel mentve!")
                st.rerun()

with tab2:
    st.subheader("📊 Kimutatások")
    if not df_main.empty:
        df_main['tipus_clean'] = df_main['tipus'].astype(str).str.lower()
        kiadas_df = df_main[df_main['tipus_clean'].str.contains("kiad|megtak", na=False)].copy()
        if not kiadas_df.empty:
            c1, c2 = st.columns(2)
            with c1: st.plotly_chart(px.pie(kiadas_df, values='osszeg', names='kategoria'), use_container_width=True)
            with c2:
                kiadas_df['honap'] = pd.to_datetime(kiadas_df['datum']).dt.strftime('%Y-%m')
                trend = kiadas_df.groupby('honap')['osszeg'].sum().reset_index()
                st.plotly_chart(px.line(trend, x='honap', y='osszeg', markers=True), use_container_width=True)

with tab3:
    st.subheader("📅 Adatok")
    st.write("**Fixek a Google-ben (Második fül):**")
    st.dataframe(df_fixek, use_container_width=True)
    st.write("**Tranzakciók (Első fül):**")
    st.dataframe(df_main.sort_values('datum', ascending=False).head(20), use_container_width=True)

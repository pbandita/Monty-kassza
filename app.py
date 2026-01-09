import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
import io
import random

# --- ALAPOK ---
st.set_page_config(page_title="Andris & Zsóka Kassza", layout="wide", page_icon="💰")
px.defaults.template = "plotly_dark"

SHEET_ID = "1sk5LgO3WHEq-EtSrK9xSrtAWnAX4fhO_KULE37DraIQ"
# FONTOS: Ezeket a GID-eket a böngésző URL-jéből másold ki!
CSV_URL_MAIN = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
CSV_URL_FIXEK = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1493472585" 
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxyHCbk2E4E01AQflCl4K9qYH-GXPSuzHHU0yMS7XhATHkBnb7Gy87EFcdGDrAmrnU68w/exec"

@st.cache_data(ttl=600)
def get_eur_huf():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/EUR")
        return r.json()['rates']['HUF']
    except: return 410.0

arfolyam = get_eur_huf()

def load_sheet(url):
    try:
        r_url = f"{url}&cb={datetime.now().timestamp()}"
        response = requests.get(r_url, timeout=10)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.content.decode('utf-8')))
            df.columns = [c.strip().lower() for c in df.columns]
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

df_main = load_sheet(CSV_URL_MAIN)
df_fixek = load_sheet(CSV_URL_FIXEK)

# --- FELÜLET ---
st.title("💰 Andris & Zsóka Közös Kassza")

tab1, tab2, tab3 = st.tabs(["📝 Könyvelés", "📊 Kimutatások", "📅 Adatok"])

with tab1:
    # Felül egy vékony infó sáv
    st.info(f"Aktuális árfolyam: **1 EUR = {arfolyam:.2f} HUF**")
    
    col_bal, col_jobb = st.columns([1, 1], gap="large")
    
    with col_bal:
        st.markdown("### 🖋️ Tranzakció rögzítése")
        with st.container(border=True):
            with st.form("napi_form", clear_on_submit=True):
                d = st.date_input("Dátum", datetime.now())
                t = st.selectbox("Típus", ["📉 Kiadás", "📈 Bevétel", "💰 Megtakarítás", "💵 Fizetés"])
                sz = st.selectbox("Személy", ["👤 Andris", "👤 Zsóka", "👥 Közös"])
                k = st.selectbox("Kategória", ["🏠 Lakás/Rezsi", "🛒 Élelmiszer", "🏦 Hitel", "🚗 Közlekedés", "🐶 Monty", "💰 Megtakarítás", "📦 Egyéb"])
                
                v_c1, v_c2 = st.columns([1, 2])
                valuta = v_c1.selectbox("Pénznem", ["HUF", "EUR"], key="v1")
                osszeg = v_c2.number_input("Összeg", min_value=0.0)
                megj = st.text_input("Megjegyzés")
                
                if st.form_submit_button("👅 MIMIC LÁDA ELNYELI"):
                    if osszeg > 0:
                        final = int(osszeg if valuta == "HUF" else osszeg * arfolyam)
                        requests.post(SCRIPT_URL, json={
                            "is_fix": False, "datum": str(d), "tipus": t, 
                            "szemely": sz, "kategoria": k, "osszeg": final, "megjegyzes": megj
                        })
                        st.balloons()
                        st.rerun()

    with col_jobb:
        st.markdown("### 🔁 Fix kiadás ütemezése")
        with st.container(border=True):
            with st.form("fix_form", clear_on_submit=True):
                f_nev = st.text_input("Megnevezés")
                f_kat = st.selectbox("Kategória", ["🏠 Lakás/Rezsi", "🏦 Hitel", "💰 Megtakarítás", "📦 Egyéb"], key="f1")
                f_osszeg = st.number_input("Havi HUF", min_value=0)
                f_d = st.date_input("Nap", datetime.now())
                
                if st.form_submit_button("📜 PERGAMENRE ÍRÁS (FIX MENTÉS)"):
                    if f_osszeg > 0:
                        requests.post(SCRIPT_URL, json={
                            "is_fix": True, "nev": f_nev, "kategoria": f_kat, "osszeg": int(f_osszeg), "datum": str(f_d)
                        })
                        st.success("A kincstárnok feljegyezte!")
                        st.rerun()

with tab2:
    if not df_main.empty:
        # Itt is érvényesítjük a szűrést
        df_main['tipus_clean'] = df_main['tipus'].astype(str).str.lower()
        kiadas_df = df_main[df_main['tipus_clean'].str.contains("kiad|megtak", na=False)].copy()
        
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(px.pie(kiadas_df, values='osszeg', names='kategoria', title="Mire megy el a pénz?"), use_container_width=True)
        with c2:
            kiadas_df['honap'] = pd.to_datetime(kiadas_df['datum']).dt.strftime('%Y-%m')
            trend = kiadas_df.groupby('honap')['osszeg'].sum().reset_index()
            st.plotly_chart(px.line(trend, x='honap', y='osszeg', title="Havi költés", markers=True), use_container_width=True)

with tab3:
    st.subheader("Tranzakciók")
    st.dataframe(df_main.sort_values('datum', ascending=False), use_container_width=True)
    st.subheader("Aktív Fixek")
    st.dataframe(df_fixek, use_container_width=True)

# --- Zsóka Lovasa ---
knight_msg = ["Jó munkát, Zsóka!", "Az aranyad biztonságban van!", "Vigyázok a kincstárra!", "Monty is büszke rád!"]
st.divider()
st.markdown(f"🏇 **A Lovag üzeni:** _{random.choice(knight_msg)}_")

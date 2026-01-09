import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta
import io
import random # A lovas üzenetekhez

# --- 0. ALAPBEÁLLÍTÁSOK ---
st.set_page_config(page_title="Andris & Zsóka Kassza", layout="wide", page_icon="💰")
px.defaults.template = "plotly_dark"

SHEET_ID = "1sk5LgO3WHEq-EtSrK9xSrtAWnAX4fhO_KULE37DraIQ"
CSV_URL_MAIN = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
CSV_URL_FIXEK = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1493472585" 

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxyHCbk2E4E01AQflCl4K9qYH-GXPSuzHHU0yMS7XhATHkBnb7Gy87EFcdGDrAmrnU68w/exec"

# --- EUR-HUF ÁRFOLYAM LEKÉRDEZÉSE (Gyorsítótárazva) ---
@st.cache_data(ttl=600) # 10 percig tárolja az árfolyamot
def get_eur_huf():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/EUR")
        return r.json()['rates']['HUF']
    except: 
        return 410.0 # Vészhelyzeti árfolyam

arfolyam = get_eur_huf()

# --- ADATOK BETÖLTÉSE ---
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
    col_bal, col_jobb = st.columns(2) # Most csak két oszlop marad itt, mert a fizetést beraktuk a Típusba

    # BAL OLDAL: Normál tranzakció + EUR átváltás
    with col_bal:
        st.subheader("🖋️ Egyszeri tétel")
        with st.form("beviteli_iv", clear_on_submit=True):
            datum = st.date_input("Dátum", datetime.now())
            # Fizetés hozzáadva a típusokhoz
            tipus = st.selectbox("Típus", ["📉 Kiadás", "📈 Bevétel", "💰 Megtakarítás", "💵 Fizetés"])
            szemely = st.selectbox("Ki rögzítette?", ["👤 Andris", "👤 Zsóka", "👥 Közös"])
            kategoria = st.selectbox("Kategória", ["🏠 Lakás/Rezsi", "🛒 Élelmiszer", "🏦 Hitel", "🚗 Közlekedés", "🐶 Monty", "💰 Megtakarítás", "📦 Egyéb"])
            
            # Valuta választó és összeg mező
            v_col1, v_col2 = st.columns([1,2])
            valuta = v_col1.selectbox("Pénznem", ["HUF", "EUR"])
            nyers_osszeg = v_col2.number_input("Összeg", min_value=0.0)
            
            megjegyzes = st.text_input("Megjegyzés")
            
            # Andris Mimic gombja
            if st.form_submit_button("👅 MIMIC LÁDA ELNYELI (MENTÉS)"):
                if nyers_osszeg > 0:
                    final_osszeg = int(nyers_osszeg if valuta == "HUF" else nyers_osszeg * arfolyam)
                    
                    res = requests.post(SCRIPT_URL, json={
                        "is_fix": False,
                        "is_salary": (tipus == "💵 Fizetés"), # Jelöljük, ha fizetés
                        "datum": str(datum), 
                        "tipus": tipus, 
                        "szemely": szemely,
                        "kategoria": kategoria, 
                        "osszeg": final_osszeg, 
                        "megjegyzes": megjegyzes
                    })
                    st.success(f"A Mimic elnyelte az érméket! ({final_osszeg:,.0f} Ft elmentve) 👅💰")
                    st.rerun()

    # JOBB OLDAL: Fix kiadás rögzítése a Sheet2-re
    with col_jobb:
        st.subheader("🔁 Havi fix ütemezése")
        with st.form("fix_form", clear_on_submit=True):
            f_nev = st.text_input("Megnevezés (pl. Netflix)")
            f_kat = st.selectbox("Kategória ", ["🏠 Lakás/Rezsi", "🏦 Hitel", "💰 Megtakarítás", "📦 Egyéb"])
            f_osszeg = st.number_input("Havi fix összeg (HUF)", min_value=0, key="fix_osszeg")
            f_datum = st.date_input("Kezdő dátum", datetime.now()) # Ez lesz az utolso_datum a Sheet2-ben
            
            if st.form_submit_button("ÜTEMEZÉS MENTÉSE A FELHŐBE"):
                if f_osszeg > 0 and f_nev:
                    res = requests.post(SCRIPT_URL, json={
                        "is_fix": True,
                        "is_salary": False, # Fixeknél nem fizetés
                        "nev": f_nev,
                        "kategoria": f_kat,
                        "osszeg": int(f_osszeg),
                        "datum": str(f_datum) # Itt a 'datum' az utolso_datumot jelöli
                    })
                    st.success("Havi fix rögzítve a Google Táblázatban!")
                    st.rerun()

with tab2:
    st.subheader("📊 Kimutatások")
    if st.button("🔄 Adatok frissítése"):
        st.rerun()

    if not df_main.empty:
        df_main['tipus_clean'] = df_main['tipus'].astype(str).str.lower()
        
        # Kiadások szűrése (a fizetés nincs benne)
        kiadas_df = df_main[df_main['tipus_clean'].str.contains("kiad|megtak", na=False)].copy()
        
        if not kiadas_df.empty:
            c1, c2 = st.columns(2)
            with c1:

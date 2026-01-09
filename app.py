import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
import io
import random

# --- 0. ALAPBEÁLLÍTÁSOK ---
st.set_page_config(page_title="Andris & Zsóka Kassza", layout="wide", page_icon="💰")
px.defaults.template = "plotly_dark"

SHEET_ID = "1sk5LgO3WHEq-EtSrK9xSrtAWnAX4fhO_KULE37DraIQ"
# Ellenőrizd a böngészőben a GID-eket! A fő tábla általában 0, a Fixek más szám.
CSV_URL_MAIN = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
CSV_URL_FIXEK = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1493472585" 
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxyHCbk2E4E01AQflCl4K9qYH-GXPSuzHHU0yMS7XhATHkBnb7Gy87EFcdGDrAmrnU68w/exec"

# --- EUR ÁRFOLYAM ---
@st.cache_data(ttl=3600)
def get_rate():
    try: return requests.get("https://open.er-api.com/v6/latest/EUR").json()['rates']['HUF']
    except: return 410.0

rate = get_rate()

def load_data(url):
    try:
        r = requests.get(f"{url}&cb={datetime.now().timestamp()}")
        df = pd.read_csv(io.StringIO(r.content.decode('utf-8')))
        df.columns = [c.strip().lower() for c in df.columns]
        return df
    except: return pd.DataFrame()

df_main = load_data(CSV_URL_MAIN)
df_fixek = load_data(CSV_URL_FIXEK)

# --- FELÜLET ---
st.title("🛡️ Andris & Zsóka Kincstára")

tab1, tab2, tab3 = st.tabs(["📝 Könyvelés", "📊 Kimutatások", "📅 Adatok"])

with tab1:
    st.info(f"Aktuális árfolyam: **1 EUR = {rate:.2f} HUF**")
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("🖋️ Tranzakció")
        with st.form("main_f", clear_on_submit=True):
            d = st.date_input("Dátum", datetime.now())
            t = st.selectbox("Típus", ["📉 Kiadás", "📈 Bevétel", "💰 Megtakarítás", "💵 Fizetés"])
            sz = st.selectbox("Személy", ["👤 Andris", "👤 Zsóka", "👥 Közös"])
            k = st.selectbox("Kategória", ["🏠 Lakás/Rezsi", "🛒 Élelmiszer", "🏦 Hitel", "🚗 Közlekedés", "🐶 Monty", "💰 Megtakarítás", "📦 Egyéb"])
            v_c1, v_c2 = st.columns([1,2])
            valuta = v_c1.selectbox("Pénznem", ["HUF", "EUR"])
            osszeg = v_c2.number_input("Összeg", min_value=0.0)
            megj = st.text_input("Megjegyzés")
            if st.form_submit_button("👅 MIMIC LÁDA ELNYELI"):
                final = int(osszeg if valuta == "HUF" else osszeg * rate)
                requests.post(SCRIPT_URL, json={"is_fix":False, "datum":str(d), "tipus":t, "szemely":sz, "kategoria":k, "osszeg":final, "megjegyzes":megj})
                st.balloons()
                st.rerun()

    with c2:
        st.subheader("🔁 Havi fixek")
        with st.form("fix_f", clear_on_submit=True):
            f_nev = st.text_input("Megnevezés")
            f_kat = st.selectbox("Kategória", ["🏠 Lakás/Rezsi", "🏦 Hitel", "💰 Megtakarítás", "📦 Egyéb"])
            f_osszeg = st.number_input("HUF", min_value=0)
            f_d = st.date_input("Nap", datetime.now())
            if st.form_submit_button("📜 PERGAMENRE ÍRÁS"):
                requests.post(SCRIPT_URL, json={"is_fix":True, "nev":f_nev, "kategoria":f_kat, "osszeg":int(f_osszeg), "datum":str(f_d)})
                st.success("Mentve a Fixek közé!")
                st.rerun()

with tab2:
    if not df_main.empty:
        df_main['tipus_clean'] = df_main['tipus'].astype(str).str.lower()
        kiadas_df = df_main[df_main['tipus_clean'].str.contains("kiad|megtak", na=False)].copy()
        if not kiadas_df.empty:
            c_a, c_b = st.columns(2)
            with c_a: st.plotly_chart(px.pie(kiadas_df, values='osszeg', names='kategoria', title="Kiadások"), use_container_width=True)
            with c_b:
                kiadas_df['honap'] = pd.to_datetime(kiadas_df['datum']).dt.strftime('%Y-%m')
                st.plotly_chart(px.line(kiadas_df.groupby('honap')['osszeg'].sum().reset_index(), x='honap', y='osszeg', markers=True), use_container_width=True)

with tab3:
    st.write("**Fixek (Második fül):**")
    st.dataframe(df_fixek, use_container_width=True)
    st.write("**Tranzakciók (Első fül):**")
    st.dataframe(df_main.sort_values('datum', ascending=False).head(20), use_container_width=True)

# Zsóka Lovasa
msgs = ["Jó munkát, Zsóka!", "A kincstár biztonságban van!", "Monty büszke rád!"]
st.divider()
st.markdown(f"🏇 **A Lovag üzeni:** _{random.choice(msgs)}_")

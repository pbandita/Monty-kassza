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
# Tranzakciók fül (Sheet1)
CSV_URL_MAIN = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
# Fixek fül (Sheet2 - cseréld ki a gid-et, ha a Google-ben látod az URL-ben!)
# Általában az első fül a 0, a másodiknak saját száma van az URL végén: gid=XXXXX
CSV_URL_FIXEK = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1493472585" 

SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxyHCbk2E4E01AQflCl4K9qYH-GXPSuzHHU0yMS7XhATHkBnb7Gy87EFcdGDrAmrnU68w/exec"

# --- 1. ADATOK BETÖLTÉSE ---
def load_sheet(url):
    try:
        r_url = f"{url}&cb={datetime.now().timestamp()}"
        response = requests.get(r_url)
        if response.status_code == 200:
            raw_data = response.content.decode('utf-8')
            df = pd.read_csv(io.StringIO(raw_data))
            df.columns = [c.strip().lower() for c in df.columns]
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

df_main = load_sheet(CSV_URL_MAIN)
df_fixek = load_sheet(CSV_URL_FIXEK)

# --- 2. AUTOMATIKUS ÜTEMEZÉS (Már a Sheet-ből olvassa) ---
def auto_check_cloud():
    if df_fixek.empty: return
    
    ma = datetime.now().date()
    for index, sz in df_fixek.iterrows():
        try:
            # Dátum formázás kezelése
            utolso_str = str(sz['utolso_datum'])
            utolso = pd.to_datetime(utolso_str).date()
            kovetkezo = (utolso.replace(day=1) + timedelta(days=32)).replace(day=min(utolso.day, 28))
            
            if kovetkezo <= ma:
                adat = {
                    "datum": kovetkezo.strftime("%Y-%m-%d"),
                    "tipus": "📉 Kiadás",
                    "szemely": "Automata",
                    "kategoria": sz['kategoria'],
                    "osszeg": int(sz['osszeg']),
                    "megjegyzes": f"FIX: {sz['nev']}"
                }
                # Itt beküldjük a tranzakciót
                requests.post(SCRIPT_URL, json=adat)
                # FIGYELEM: A 'Fixek' tábla frissítéséhez egy másik Script funkció kellene, 
                # vagy manuálisan kell átírni a dátumot a táblázatban rögzítés után.
        except: continue

auto_check_cloud()

# --- 3. FELÜLET ---
tab1, tab2, tab3 = st.tabs(["📝 Könyvelés", "📊 Kimutatások", "📅 Naptár & Fixek"])

with tab1:
    st.subheader("🖋️ Új tétel rögzítése")
    with st.form("beviteli_iv", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            datum = st.date_input("Dátum", datetime.now())
            tipus = st.selectbox("Típus", ["📉 Kiadás", "📈 Bevétel", "💰 Megtakarítás"])
            szemely = st.selectbox("Ki rögzítette?", ["👤 Andris", "👤 Zsóka", "👥 Közös"])
        with col2:
            kategoria = st.selectbox("Kategória", ["🏠 Lakás/Rezsi", "🛒 Élelmiszer", "🏦 Hitel", "🚗 Közlekedés", "🐶 Monty", "💰 Megtakarítás", "📦 Egyéb"])
            nyers_osszeg = st.number_input("Összeg (HUF)", min_value=0)
            megjegyzes = st.text_input("Megjegyzés")
            
        if st.form_submit_button("MENTÉS"):
            if nyers_osszeg > 0:
                res = requests.post(SCRIPT_URL, json={
                    "datum": datum.strftime("%Y-%m-%d"), "tipus": tipus, "szemely": szemely,
                    "kategoria": kategoria, "osszeg": int(nyers_osszeg), "megjegyzes": megjegyzes
                })
                st.success("Mentve!")
                st.rerun()

with tab2:
    st.subheader("📊 Kimutatások")
    if not df_main.empty:
        df_main['tipus_clean'] = df_main['tipus'].astype(str).str.lower()
        kiadas_df = df_main[df_main['tipus_clean'].str.contains("kiad|megtak", na=False)].copy()
        
        if not kiadas_df.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(px.pie(kiadas_df, values='osszeg', names='kategoria', title="Kiadások"), use_container_width=True)
            with c2:
                kiadas_df['honap'] = pd.to_datetime(kiadas_df['datum']).dt.strftime('%Y-%m')
                trend = kiadas_df.groupby('honap')['osszeg'].sum().reset_index()
                st.plotly_chart(px.line(trend, x='honap', y='osszeg', title="Havi trend", markers=True), use_container_width=True)

with tab3:
    st.subheader("📅 Tranzakciók és Felhő-Fixek")
    st.write("**Utolsó tranzakciók (Sheet1):**")
    st.dataframe(df_main.sort_values('datum', ascending=False).head(15), use_container_width=True)
    
    st.divider()
    st.write("**Aktív havi fixek (Sheet2):**")
    if not df_fixek.empty:
        st.dataframe(df_fixek, use_container_width=True)
    else:
        st.info("Nincs rögzített fix tétel a Google Táblázat 'Fixek' fülén.")

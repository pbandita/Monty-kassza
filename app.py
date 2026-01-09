import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta
import sqlite3
import io

# --- 0. ALAPBEÁLLÍTÁSOK ---
# Fontos: Ez kell, hogy az legelső Streamlit parancs legyen!
st.set_page_config(page_title="Andris & Zsóka Kassza", layout="wide", page_icon="💰")
px.defaults.template = "plotly_dark"

# AZONOSÍTÓK
SHEET_ID = "1sk5Lg03WHEq-EtSrK9xSrtAWnAX4fh0_KULE37DraIQ"
# Közvetlen publikus CSV link
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
# A Google Script URL-ed a mentéshez
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxyHCbk2E4E01AQflCl4K9qYH-GXPSuzHHU0yMS7XhATHkBnb7Gy87EFcdGDrAmrnU68w/exec"

# --- 1. ADATBÁZIS ÉS ADATOK BETÖLTÉSE ---
def init_db():
    conn = sqlite3.connect('tervek.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ismetlodo 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nev TEXT, kategoria TEXT, osszeg REAL, utolso_datum TEXT)''')
    conn.commit()
    conn.close()

def load_data():
    try:
        # Frissítés kényszerítése cache-busterrel
        r_url = f"{CSV_URL}&cb={datetime.now().timestamp()}"
        response = requests.get(r_url)
        if response.status_code == 200:
            df = pd.read_csv(io.StringIO(response.text))
            # Oszlopnevek tisztítása (kisbetű, szóközmentes)
            df.columns = [c.strip().lower() for c in df.columns]
            
            if 'datum' in df.columns:
                df['datum'] = pd.to_datetime(df['datum']).dt.date
            if 'osszeg' in df.columns:
                df['osszeg'] = pd.to_numeric(df['osszeg'], errors='coerce').fillna(0)
            return df
        return pd.DataFrame()
    except Exception as e:
        return pd.DataFrame(columns=["datum", "tipus", "szemely", "kategoria", "osszeg", "megjegyzes"])

@st.cache_data(ttl=600)
def get_eur_huf():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/EUR")
        return r.json()['rates']['HUF']
    except: return 410.0

init_db()
arfolyam = get_eur_huf()
df = load_data()

# --- 2. AUTOMATIKUS ÜTEMEZÉS ---
def auto_check():
    conn = sqlite3.connect('tervek.db')
    szabalyok = pd.read_sql_query("SELECT * FROM ismetlodo", conn)
    ma = datetime.now().date()
    
    for _, sz in szabalyok.iterrows():
        try:
            utolso = datetime.strptime(sz['utolso_datum'], "%Y-%m-%d").date()
            kovetkezo = (utolso.replace(day=1) + timedelta(days=32)).replace(day=min(utolso.day, 28))
            
            if kovetkezo <= ma:
                tipus = "💰 Megtakarítás" if sz['kategoria'] == "💰 Megtakarítás" else "📉 Kiadás"
                adat = {
                    "datum": kovetkezo.strftime("%Y-%m-%d"),
                    "tipus": tipus,
                    "szemely": "Automata",
                    "kategoria": sz['kategoria'],
                    "osszeg": int(sz['osszeg']),
                    "megjegyzes": f"FIX: {sz['nev']}"
                }
                requests.post(SCRIPT_URL, json=adat)
                conn.execute("UPDATE ismetlodo SET utolso_datum = ? WHERE id = ?", (kovetkezo.strftime("%Y-%m-%d"), sz['id']))
        except: continue
    conn.commit()
    conn.close()

auto_check()

# --- 3. FELÜLET ---
tab1, tab2, tab3 = st.tabs(["📝 Könyvelés", "📊 Kimutatások", "📅 Naptár & Áttekintés"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Új tétel rögzítése")
        with st.form("beviteli_iv", clear_on_submit=True):
            datum = st.date_input("Dátum", datetime.now())
            tipus = st.selectbox("Típus", ["📉 Kiadás", "📈 Bevétel", "💰 Megtakarítás"])
            szemely = st.selectbox("Ki rögzítette?", ["👤 Andris", "👤 Zsóka", "👥 Közös"])
            kategoria = st.selectbox("Kategória", ["🏠 Lakás/Rezsi", "🛒 Élelmiszer", "🏦 Hitel", "🚗 Közlekedés", "🐶 Monty", "💰 Megtakarítás", "📦 Egyéb"])
            v_col1, v_col2 = st.columns([1,2])
            valuta = v_col1.selectbox("Valuta", ["HUF", "EUR"])
            nyers_osszeg = v_col2.number_input("Összeg", min_value=0.0)
            megjegyzes = st.text_input("Megjegyzés")
            
            if st.form_submit_button("MENTÉS", use_container_width=True):
                final_osszeg = int(nyers_osszeg if valuta == "HUF" else nyers_osszeg * arfolyam)
                res = requests.post(SCRIPT_URL, json={
                    "datum": datum.strftime("%Y-%m-%d"), "tipus": tipus, "szemely": szemely,
                    "kategoria": kategoria, "osszeg": final_osszeg, "megjegyzes": megjegyzes
                })
                if res.status_code == 200:
                    st.success(f"Sikeres mentés: {final_osszeg:,.0f} Ft")
                    st.rerun()

    with col2:
        st.subheader("Havi fix tételek")
        with st.form("fix_form", clear_on_submit=True):
            f_nev = st.text_input("Megnevezés (pl. Netflix)")
            f_kat = st.selectbox("Kategória ", ["🏠 Lakás/Rezsi", "🏦 Hitel", "💰 Megtakarítás"])
            f_osszeg = st.number_input("Havi fix összeg (HUF)", min_value=0)
            f_datum = st.date_input("Kezdő dátum", datetime.now())
            if st.form_submit_button("ÜTEMEZÉS MENTÉSE", use_container_width=True):
                conn = sqlite3.connect('tervek.db')
                conn.execute("INSERT INTO ismetlodo (nev, kategoria, osszeg, utolso_datum) VALUES (?,?,?,?)",
                             (f_nev, f_kat, f_osszeg, f_datum.strftime("%Y-%m-%d")))
                conn.commit()
                conn.close()
                st.info("Fix tétel elmentve.")

with tab2:
    st.subheader("Kimutatások")
    if st.button("Adatok frissítése"):
        st.cache_data.clear()
        st.rerun()

    if not df.empty and len(df) > 0:
        # Szűrés kiadásokra (ikonokkal együtt is)
        kiadas_df = df[df['tipus'].str.contains("Kiadás|Megtakarítás", case=False, na=False)].copy()
        
        if not kiadas_df.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.write("**Kiadások eloszlása**")
                st.plotly_chart(px.pie(kiadas_df, values='osszeg', names='kategoria', hole=0.4), use_container_width=True)
            with c2:
                st.write("**Havi költés alakulása**")
                df['honap'] = pd.to_datetime(df['datum']).dt.strftime('%Y-%m')
                trend = kiadas_df.groupby('honap')['osszeg'].sum().reset_index()
                st.plotly_chart(px.line(trend, x="honap", y="osszeg", markers=True), use_container_width=True)
        else:
            st.info("Nincs rögzített kiadás.")
    else:
        st.warning("Nincs megjeleníthető adat.")

with tab3:
    st.subheader("Tranzakciók")
    if not df.empty:
        st.dataframe(df.sort_values('datum', ascending=False), use_container_width=True)
    
    st.divider()
    st.write("**Aktív havi ütemezések**")
    conn = sqlite3.connect('tervek.db')
    fixek = pd.read_sql_query("SELECT id, nev, osszeg FROM ismetlodo", conn)
    conn.close()
    st.table(fixek)

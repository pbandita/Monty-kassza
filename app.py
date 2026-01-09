import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta
import sqlite3

# --- 0. ALAPBEÁLLÍTÁSOK ---
st.set_page_config(page_title="Andris & Zsóka Kassza", layout="wide", page_icon="💰")
px.defaults.template = "plotly_dark"

SHEET_ID = "1sk5Lg03WHEq-EtSrK9xSrtAwNAX4fh0_KULE37DraIQ"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbxyHCbk2E4E01AQflCl4K9qYH-GXPSuzHHU0yMS7XhATHkBnb7Gy87EFcdGDrAmrnU68w/exec"

# --- 1. HELYI ADATBÁZIS AZ ÜTEMEZÉSHEZ ---
# Az ismétlődő szabályokat helyben tároljuk, hogy ne kelljen érte a Google-be nyúlni
def init_db():
    conn = sqlite3.connect('tervek.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS ismetlodo 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  nev TEXT, kategoria TEXT, osszeg REAL, gyakorisag TEXT, utolso_datum TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 2. ADATOK BETÖLTÉSE ---
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

# --- 3. AUTOMATIKUS RÖGZÍTÉS FUNKCIÓ ---
def auto_check():
    conn = sqlite3.connect('tervek.db')
    szabalyok = pd.read_sql_query("SELECT * FROM ismetlodo", conn)
    ma = datetime.now().date()
    
    for _, sz in szabalyok.iterrows():
        utolso = datetime.strptime(sz['utolso_datum'], "%Y-%m-%d").date()
        # Következő esedékesség kiszámítása (egyszerű havi logika)
        if sz['gyakorisag'] == "Havonta":
            # Következő hónap azonos napja
            kovetkezo = (utolso.replace(day=1) + timedelta(days=32)).replace(day=min(utolso.day, 28))
            
            if kovetkezo <= ma:
                # Beküldés a Google-be
                adat = {
                    "datum": kovetkezo.strftime("%Y-%m-%d"),
                    "tipus": "📉 Kiadás" if "Megtakarítás" not in sz['kategoria'] else "💰 Megtakarítás",
                    "szemely": "Automata",
                    "kategoria": sz['kategoria'],
                    "osszeg": int(sz['osszeg']),
                    "megjegyzes": f"FIX: {sz['nev']}"
                }
                requests.post(SCRIPT_URL, json=adat)
                # Frissítés a helyi db-ben
                conn.execute("UPDATE ismetlodo SET utolso_datum = ? WHERE id = ?", (kovetkezo.strftime("%Y-%m-%d"), sz['id']))
    conn.commit()
    conn.close()

auto_check()

# --- 4. FÜLEK ---
tab1, tab2, tab3 = st.tabs(["📝 Könyvelés", "📊 Kimutatások", "🔁 Fixek & Ütemezés"])

with tab1:
    st.subheader("💸 Új tétel rögzítése")
    with st.form("beviteli_iv", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            datum = st.date_input("Dátum", datetime.now())
            tipus = st.selectbox("Típus", ["📉 Kiadás", "📈 Bevétel", "💰 Megtakarítás"])
            szemely = st.selectbox("Ki rögzítette?", ["👤 Andris", "👤 Zsóka", "👥 Közös"])
        with col2:
            kategoria = st.selectbox("Kategória", ["🏠 Lakás/Rezsi", "🛒 Élelmiszer", "🏦 Hitel", "🚗 Közlekedés", "🐶 Monty", "💰 Megtakarítás", "📦 Egyéb"])
            v_col1, v_col2 = st.columns([1,2])
            valuta = v_col1.selectbox("Pénznem", ["HUF", "EUR"])
            nyers_osszeg = v_col2.number_input("Összeg", min_value=0.0)
        
        megjegyzes = st.text_input("Megjegyzés")
        if st.form_submit_button("💾 MENTÉS A TÁBLÁZATBA", use_container_width=True):
            final_osszeg = int(nyers_osszeg if valuta == "HUF" else nyers_osszeg * arfolyam)
            requests.post(SCRIPT_URL, json={
                "datum": datum.strftime("%Y-%m-%d"), "tipus": tipus, "szemely": szemely,
                "kategoria": kategoria, "osszeg": final_osszeg, "megjegyzes": megjegyzes
            })
            st.success("Mentve!")
            st.rerun()

with tab2:
    # (Itt maradnak a korábbi grafikonok...)
    st.subheader("📊 Kimutatások")
    if not df.empty:
        kiadas_df = df[df['tipus'].str.contains("Kiadás|Megtakarítás", na=False)]
        st.plotly_chart(px.pie(kiadas_df, values='osszeg', names='kategoria', hole=0.4), use_container_width=True)
    else: st.info("Nincs adat.")

with tab3:
    st.subheader("🔁 Ismétlődő Fix kiadások & Megtakarítások")
    
    with st.expander("➕ Új fix tétel felvétele"):
        with st.form("fix_form"):
            f_nev = st.text_input("Megnevezés (pl. Albérlet vagy PMÁP)")
            f_kat = st.selectbox("Kategória", ["🏠 Lakás/Rezsi", "🏦 Hitel", "💰 Megtakarítás", "🎬 Előfizetés"])
            f_osszeg = st.number_input("Havi összeg (HUF)", min_value=0)
            f_datum = st.date_input("Következő levonás napja", datetime.now())
            if st.form_submit_button("Ütemezés mentése"):
                conn = sqlite3.connect('tervek.db')
                conn.execute("INSERT INTO ismetlodo (nev, kategoria, osszeg, gyakorisag, utolso_datum) VALUES (?,?,?,?,?)",
                             (f_nev, f_kat, f_osszeg, "Havonta", f_datum.strftime("%Y-%m-%d")))
                conn.commit()
                conn.close()
                st.success("Ütemezve!")
                st.rerun()

    # Aktuális fixek listázása
    conn = sqlite3.connect('tervek.db')
    fixek = pd.read_sql_query("SELECT id, nev, kategoria, osszeg, utolso_datum FROM ismetlodo", conn)
    conn.close()
    
    if not fixek.empty:
        st.write("### Aktív ütemezések")
        st.dataframe(fixek, use_container_width=True)
        if st.button("🗑️ Legutóbbi ütemezés törlése"):
            conn = sqlite3.connect('tervek.db')
            conn.execute("DELETE FROM ismetlodo WHERE id = (SELECT MAX(id) FROM ismetlodo)")
            conn.commit()
            conn.close()
            st.rerun()

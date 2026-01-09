import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime, timedelta
import sqlite3

# --- 0. ALAPBEÁLLÍTÁSOK ---
st.set_page_config(page_title="Andris & Zsóka Kassza", layout="wide", page_icon="💰")
px.defaults.template = "plotly_dark"

# Google Táblázat adatok (Olvasás és Írás)
SHEET_ID = "1sk5Lg03WHEq-EtSrK9xSrtAWnAX4fh0_KULE37DraIQ"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
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
        # Cache-buster trükk: a URL végére tesszük az időbélyeget, hogy a Google friss adatot adjon
        refresh_url = f"{CSV_URL}&cache_buster={datetime.now().timestamp()}"
        df = pd.read_csv(refresh_url)
        if 'datum' in df.columns:
            df['datum'] = pd.to_datetime(df['datum']).dt.date
        if 'osszeg' in df.columns:
            df['osszeg'] = pd.to_numeric(df['osszeg'], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame(columns=["datum", "tipus", "szemely", "kategoria", "osszeg", "megjegyzes"])

@st.cache_data(ttl=600) # 10 percig cache-elünk csak
def get_eur_huf():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/EUR")
        return r.json()['rates']['HUF']
    except: return 410.0

init_db()
arfolyam = get_eur_huf()
df = load_data()

# --- 2. AUTOMATIKUS ÜTEMEZÉS ELLENŐRZÉSE ---
def auto_check():
    conn = sqlite3.connect('tervek.db')
    szabalyok = pd.read_sql_query("SELECT * FROM ismetlodo", conn)
    ma = datetime.now().date()
    
    for _, sz in szabalyok.iterrows():
        utolso = datetime.strptime(sz['utolso_datum'], "%Y-%m-%d").date()
        # Következő hónap azonos napja (egyszerűsített havi logika)
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
            try:
                requests.post(SCRIPT_URL, json=adat)
                conn.execute("UPDATE ismetlodo SET utolso_datum = ? WHERE id = ?", (kovetkezo.strftime("%Y-%m-%d"), sz['id']))
            except: pass
    conn.commit()
    conn.close()

auto_check()

# --- 3. FÜLEK ---
tab1, tab2, tab3 = st.tabs(["📝 Könyvelés", "📊 Kimutatások", "📅 Naptár & Áttekintés"])

with tab1:
    col_bal, col_jobb = st.columns(2)
    
    with col_bal:
        st.subheader("🖋️ Egyszeri tétel rögzítése")
        with st.form("beviteli_iv", clear_on_submit=True):
            datum = st.date_input("Dátum", datetime.now())
            tipus = st.selectbox("Típus", ["📉 Kiadás", "📈 Bevétel", "💰 Megtakarítás"])
            szemely = st.selectbox("Ki rögzítette?", ["👤 Andris", "👤 Zsóka", "👥 Közös"])
            kategoria = st.selectbox("Kategória", ["🏠 Lakás/Rezsi", "🛒 Élelmiszer", "🏦 Hitel", "🚗 Közlekedés", "🐶 Monty", "💰 Megtakarítás", "📦 Egyéb"])
            v_col1, v_col2 = st.columns([1,2])
            valuta = v_col1.selectbox("Pénznem", ["HUF", "EUR"])
            nyers_osszeg = v_col2.number_input("Összeg", min_value=0.0)
            megjegyzes = st.text_input("Megjegyzés")
            if st.form_submit_button("💾 MENTÉS A TÁBLÁZATBA", use_container_width=True):
                final_osszeg = int(nyers_osszeg if valuta == "HUF" else nyers_osszeg * arfolyam)
                res = requests.post(SCRIPT_URL, json={
                    "datum": datum.strftime("%Y-%m-%d"), "tipus": tipus, "szemely": szemely,
                    "kategoria": kategoria, "osszeg": final_osszeg, "megjegyzes": megjegyzes
                })
                if res.status_code == 200:
                    st.success(f"Sikeresen mentve: {final_osszeg:,.0f} Ft")
                    st.balloons()
                    st.rerun()

    with col_jobb:
        st.subheader("🔁 Ismétlődő (Havi) beállítás")
        with st.form("fix_form", clear_on_submit=True):
            f_nev = st.text_input("Megnevezés (pl. Albérlet)")
            f_kat = st.selectbox("Kategória ", ["🏠 Lakás/Rezsi", "🏦 Hitel", "💰 Megtakarítás", "🎬 Előfizetés"])
            f_osszeg = st.number_input("Havi összeg (HUF)", min_value=0)
            f_datum = st.date_input("Első levonás napja", datetime.now())
            if st.form_submit_button("🔁 ÜTEMEZÉS MENTÉSE", use_container_width=True):
                conn = sqlite3.connect('tervek.db')
                conn.execute("INSERT INTO ismetlodo (nev, kategoria, osszeg, utolso_datum) VALUES (?,?,?,?)",
                             (f_nev, f_kat, f_osszeg, f_datum.strftime("%Y-%m-%d")))
                conn.commit()
                conn.close()
                st.success("Havi ütemezés elmentve!")

with tab2:
    st.subheader("📊 Kimutatások")
    
    if st.button("🔄 Adatok frissítése a Google-ből"):
        st.cache_data.clear()
        st.rerun()

    if not df.empty and len(df) > 0:
        df['datum'] = pd.to_datetime(df['datum'])
        df['Honap'] = df['datum'].dt.strftime('%Y-%m')
        
        kiadas_df = df[df['tipus'].str.contains("Kiadás|Megtakarítás", na=False)]
        
        if not kiadas_df.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.write("🍕 **Kiadások megoszlása**")
                fig_pie = px.pie(kiadas_df, values='osszeg', names='kategoria', hole=0.4)
                st.plotly_chart(fig_pie, use_container_width=True)
            with c2:
                st.write("📈 **Havi trendek**")
                trend_data = kiadas_df.groupby(['Honap', 'kategoria'])['osszeg'].sum().reset_index()
                fig_line = px.line(trend_data, x="Honap", y="osszeg", color="kategoria", markers=True)
                st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.info("Nincs rögzített kiadás vagy megtakarítás.")
    else: 
        st.warning("Nincs megjeleníthető adat. Ellenőrizd a Google Táblázat fejléceit!")

with tab3:
    st.subheader("📅 Naptár és Áttekintés")
    
    # Checkbox szerű lista a havi fixekhez
    fix_nevek = ["Lakbér", "Hitel", "Internet", "Netflix", "Villany", "Sziget"]
    ma = datetime.now()
    e_havi = df[(pd.to_datetime(df['datum']).dt.month == ma.month)] if not df.empty else pd.DataFrame()
    
    st.write(f"📌 **{ma.year}. {ma.strftime('%B')}** havi fix kifizetések állapota:")
    f_cols = st.columns(len(fix_nevek))
    for i, f_nev in enumerate(fix_nevek):
        pipa = any(e_havi['megjegyzes'].str.contains(f_nev, case=False, na=False)) if not e_havi.empty else False
        if pipa: f_cols[i].success(f"✅ {f_nev}")
        else: f_cols[i].error(f"❌ {f_nev}")

    st.divider()
    
    col_n1, col_n2 = st.columns([2, 1])
    with col_n1:
        st.write("🗓️ **Utolsó 15 tranzakció**")
        if not df.empty:
            st.dataframe(df.sort_values('datum', ascending=False).head(15), use_container_width=True)
    with col_n2:
        st.write("⚙️ **Aktív havi ütemezések**")
        conn = sqlite3.connect('tervek.db')
        fixek_list = pd.read_sql_query("SELECT nev, osszeg, utolso_datum FROM ismetlodo", conn)
        conn.close()
        st.table(fixek_list)
        if st.button("🗑️ Legutóbbi ütemezés törlése"):
            conn = sqlite3.connect('tervek.db')
            conn.execute("DELETE FROM ismetlodo WHERE id = (SELECT MAX(id) FROM ismetlodo)")
            conn.commit()
            conn.close()
            st.rerun()

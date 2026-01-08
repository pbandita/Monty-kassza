import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime

# --- BEÁLLÍTÁSOK ---
st.set_page_config(page_title="Monty Kassza", layout="wide", page_icon="🐾")

# Táblázat adatai
SHEET_ID = "1sk5Lg03WHEq-EtSrK9xSrtAwNAX4fh0_KULE37DraIQ"
CSV_URL = f"https://docs.google.com/spreadsheets/d/1sk5LgO3WHEq-EtSrK9xSrtAWnAX4fhO_KULE37DraIQ/export?format=csv"

# --- ADATOK BETÖLTÉSE ---
def load_data():
    try:
        # A 'storage_options' segít elkerülni a cache-elési hibákat
        df = pd.read_csv(CSV_URL)
        if 'datum' in df.columns:
            df['datum'] = pd.to_datetime(df['datum']).dt.date
        return df
    except:
        return pd.DataFrame(columns=["datum", "tipus", "szemely", "kategoria", "osszeg", "megjegyzes"])

@st.cache_data(ttl=600) # 10 percenként frissülő árfolyam
def get_eur_huf():
    try:
        r = requests.get("https://open.er-api.com/v6/latest/EUR")
        return r.json()['rates']['HUF']
    except: return 410.0

arfolyam = get_eur_huf()
df = load_data()

# --- MEGJELENÍTÉS ---
st.title("🐾 Monty Kassza - Pénzügyi Áttekintés")

# Oldalsáv a gyors infóknak
with st.sidebar:
    st.header("⚙️ Beállítások")
    st.write(f"💱 **Árfolyam:** 1 EUR = {arfolyam:.1f} Ft")
    if st.button("🔄 Adatok frissítése"):
        st.cache_data.clear()
        st.rerun()

tab1, tab2, tab3, tab4 = st.tabs(["📊 Statisztika", "📝 Új tétel", "📅 Idővonal", "🐕 Monty"])

with tab1:
    if not df.empty:
        # Számítások
        kiadasok = df[df['tipus'].str.contains("Kiadás", na=False)]
        bevetel_sum = df[df['tipus'].str.contains("Bevétel", na=False)]['osszeg'].sum()
        kiadas_sum = kiadasok['osszeg'].sum()
        egyenleg = bevetel_sum - kiadas_sum

        col1, col2, col3 = st.columns(3)
        col1.metric("Bevétel", f"{bevetel_sum:,.0f} Ft", delta_color="normal")
        col2.metric("Kiadás", f"{kiadas_sum:,.0f} Ft", delta_color="inverse")
        col3.metric("Egyenleg", f"{egyenleg:,.0f} Ft", delta="Aktuális")

        # Kategória szerinti bontás
        st.subheader("🍕 Mire ment el a pénz?")
        fig = px.bar(kiadasok.groupby('kategoria')['osszeg'].sum().reset_index(), 
                     x='kategoria', y='osszeg', color='kategoria',
                     text_auto='.2s', title="Kiadások kategóriánként")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Nincs megjeleníthető adat. Írj be valamit a táblázatba!")

with tab2:
    st.subheader("📝 Új tranzakció rögzítése")
    # Itt marad a Forms-os megoldás vagy egy manuális emlékeztető
    with st.form("bevitel"):
        c1, c2 = st.columns(2)
        with c1:
            datum = st.date_input("Dátum", datetime.now())
            tipus = st.selectbox("Típus", ["📉 Kiadás", "📈 Bevétel", "💰 Megtakarítás"])
            szemely = st.selectbox("Ki?", ["👤 Andris", "👤 Zsóka", "👥 Közös"])
        with c2:
            kat = st.selectbox("Kategória", ["🏠 Lakás", "🛒 Élelmiszer", "🚗 Autó", "🎬 Hobbi", "🐶 Monty", "📦 Egyéb"])
            penznem = st.radio("Pénznem", ["HUF", "EUR"], horizontal=True)
            osszeg = st.number_input("Összeg", min_value=0)
        
        megj = st.text_input("Megjegyzés (pl. bolt neve)")
        
        if st.form_submit_button("Adat rögzítése"):
            # Itt irányítunk a Google Formhoz, amit korábban készítettél
            st.info("Kattints a mentéshez a Google Forms linkre!")
            st.link_button("🚀 IRÁNY A GOOGLE FORMS", "IDE_MÁSOLD_A_FORMS_LINKET")

with tab3:
    st.subheader("📅 Tranzakciók listája")
    st.dataframe(df.sort_values(by='datum', ascending=False), use_container_width=True)

with tab4:
    st.subheader("🐶 Monty különkiadás")
    monty_costs = df[df['kategoria'] == "🐶 Monty"]['osszeg'].sum()
    st.metric("Monty összes költsége eddig", f"{monty_costs:,.0f} Ft")
    st.write("Itt követhetitek, mennyit költötök a kutyusra (táp, állatorvos, játékok).")

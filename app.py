import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime
import plotly.express as px
import requests

# --- ÁRFOLYAM ---
def get_eur_huf():
    try:
        url = "https://open.er-api.com/v6/latest/EUR"
        return requests.get(url).json()['rates']['HUF']
    except: return 400.0

st.set_page_config(page_title="Monty Kassza", layout="wide")
arfolyam = get_eur_huf()

# --- ADATOK ---
conn = st.connection("gsheets", type=GSheetsConnection)
def get_data():
    return conn.read(ttl="0m")

# --- FELÜLET ---
tab1, tab2, tab3 = st.tabs(["📝 Bevitel", "📊 Statisztika", "📅 Lista"])

with tab1:
    st.subheader("💸 Új tétel")
    with st.form("add_form", clear_on_submit=True):
        d = st.date_input("Dátum", datetime.now())
        t = st.selectbox("Típus", ["📉 Kiadás", "📈 Bevétel"])
        s = st.selectbox("Ki?", ["👤 Andris", "👤 Zsóka", "👥 Közös"])
        k = st.selectbox("Kategória", ["🏠 Lakás", "🛒 Élelmiszer", "🚗 Autó", "🎬 Hobbi", "🐶 Monty", "📦 Egyéb"])
        val = st.radio("Pénznem", ["HUF", "EUR"], horizontal=True)
        osszeg = st.number_input("Összeg", min_value=0.0)
        megj = st.text_input("Megjegyzés")
        if st.form_submit_button("Mentés"):
            final_o = osszeg if val == "HUF" else osszeg * arfolyam
            uj = pd.DataFrame([{"datum": d.strftime("%Y-%m-%d"), "tipus": t, "szemely": s, "kategoria": k, "osszeg": final_o, "megjegyzes": megj}])
            df = pd.concat([get_data(), uj], ignore_index=True)
            conn.update(data=df)
            st.success("Mentve a Google Táblázatba!")

with tab2:
    df = get_data()
    if not df.empty:
        st.plotly_chart(px.pie(df[df['tipus']=='📉 Kiadás'], values='osszeg', names='kategoria', title="Kiadások megoszlása"))
        st.metric("Összes kiadás", f"{df[df['tipus']=='📉 Kiadás']['osszeg'].sum():,.0f} Ft")

with tab3:
    df = get_data()
    if not df.empty:
        st.dataframe(df.sort_values("datum", ascending=False), use_container_width=True)

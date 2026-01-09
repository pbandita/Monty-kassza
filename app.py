import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
import io
import random

# --- 0. ALAPBEÁLLÍTÁSOK ---
st.set_page_config(page_title="Andris & Zsóka Kassza", layout="wide", page_icon="💰")

# Google ID-k (Változatlanok)
SHEET_ID = "1sk5LgO3WHEq-EtSrK9xSrtAWnAX4fhO_KULE37DraIQ"
CSV_URL_MAIN = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
CSV_URL_FIXEK = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1493472585" 
# Ide az ÚJ SCRIPT URL-t másold be, amit a legutóbbi Deploymentnél kaptál!
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbw_JfS4awJ-4U3AzDhSt91lM0RmeEfNAxKYjqgk5-AxZ5JWUhwG8Xi_DHqjicCWac5Z/exec"

# --- BELÉPÉSI LOGIKA ---
if 'user' not in st.session_state:
    st.title("🛡️ Kincstári Beléptető Kapu")
    st.subheader("Ki szeretne könyvelni ma?")
    col_a, col_z = st.columns(2)
    
    with col_a:
        if st.button("💻 ANDRIS (Geek mód)", use_container_width=True):
            st.session_state.user = "👤 Andris"
            st.rerun()
            
    with col_z:
        if st.button("🏇 ZSÓKA (Lovas mód)", use_container_width=True):
            st.session_state.user = "👤 Zsóka"
            st.rerun()
    st.stop() # Megállítjuk a kódot, amíg nincs választás

# --- USER SPECIFIKUS DESIGN ---
user = st.session_state.user

if user == "👤 Andris":
    primary_color = "#FF00FF" # Matrix Zöld
    bg_color = "#0000FF"
    st.markdown(f"""
        <style>
        .stApp {{ background-color: {bg_color}; color: {primary_color}; font-family: 'Courier New', monospace; }}
        .stButton>button {{ border: 2px solid {primary_color} !important; color: {primary_color} !important; background-color: black !important; }}
        h1, h2, h3 {{ color: {primary_color} !important; text-shadow: 2px 2px 5px #000; font-family: 'Monaco', monospace !important }}
        </style>
    """, unsafe_allow_html=True)
else:
    # --- Színbeállítások Zsókának ---
    primary_color = "#2E7D32" # Középzöld (Gombok és címek)
    bg_color = "##805603"      # Nagyon sötétzöld (Oldal háttér)
    input_bg = "#1B5E20"      # Világosabb zöld (A beviteli mezők belseje)
    border_color = "#1B5E20"  # Élénkzöld (A külső keret színe)

    st.markdown(f"""
        <style>
        
        .stApp {{ 
            background-color: {bg_color}; 
            color: #FFFFFF;
            border: 10px solid {border_color}; 
            box-sizing: border-box;
        }}

        
        input, div[data-baseweb="select"] > div, textarea, .stNumberInput input {{
            background-color: {input_bg} !important;
            color: white !important;
            border: 1px solid {border_color} !important;
            border-radius: 5px;
        }}

        
        .stButton>button {{ 
            background-color: {primary_color} !important; 
            color: white !important; 
            border-radius: 20px !important; 
            border: 2px solid {border_color} !important;
            font-weight: bold;
        }}

    
        h1, h2, h3 {{ 
            color: #C8E6C9 !important; /* Halványzöld a jobb olvashatóságért */
            font-family: 'Georgia', serif; 
        }}

        /* 5. TÁBLÁZAT ÉS TABS SZÍNEK */
        .stTabs [data-baseweb="tab"] {{ color: #FFFFFF !important; }}
        .stDataFrame {{ background-color: {input_bg} !important; }}
        </style>
    """, unsafe_allow_html=True)

# --- ADATOK BETÖLTÉSE ---
@st.cache_data(ttl=600)
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
st.title(f"{'⚡ TERMINÁL: ' if user == '👤 Andris' else '🏇 KASTÉLY: '} Üdvözlünk, {user}!")
if st.button("🚪 Kijelentkezés"):
    del st.session_state.user
    st.rerun()

tab1, tab2, tab3 = st.tabs(["📝 Könyvelés", "📊 Statisztika", "📅 Adatbázis"])

with tab1:
    st.write(f"💵 **Árfolyam:** 1 EUR = {rate:.2f} HUF")
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("🆕 Új tranzakció")
        with st.form("main_f", clear_on_submit=True):
            d = st.date_input("Dátum", datetime.now())
            t = st.selectbox("Típus", ["📉 Kiadás", "📈 Bevétel", "💰 Megtakarítás", "💵 Fizetés"])
            # NINCS NÉV VÁLASZTÓ - Automatikusan a 'user' változót használjuk lent
            k = st.selectbox("Kategória", ["🏠 Lakás/Rezsi", "🛒 Élelmiszer", "🏦 Hitel", "🚗 Közlekedés", "🐶 Monty", "📦 Egyéb"])
            
            v_c1, v_c2 = st.columns([1,2])
            valuta = v_c1.selectbox("Pénznem", ["HUF", "EUR"])
            osszeg = v_c2.number_input("Összeg", min_value=0.0)
            megj = st.text_input("Megjegyzés")
            
            submit_label = "💾 ADAT BEFŰZÉSE" if user == "👤 Andris" else "✨ KINCSTÁRBA HELYEZÉS"
            if st.form_submit_button(submit_label):
                final = int(osszeg if valuta == "HUF" else osszeg * rate)
                # A 'szemely' mezőbe automatikusan bekerül a bejelentkezett felhasználó
                requests.post(SCRIPT_URL, json={
                    "is_fix": False, "datum": str(d), "tipus": t, 
                    "szemely": user, "kategoria": k, "osszeg": final, "megjegyzes": megj
                })
                st.success("Sikeres mentés!")
                st.rerun()

    with c2:
        st.subheader("🔁 Havi fix rögzítése")
        with st.form("fix_f", clear_on_submit=True):
            f_nev = st.text_input("Fix kiadás neve")
            f_kat = st.selectbox("Kategória", ["🏠 Lakás/Rezsi", "🏦 Hitel", "💰 Megtakarítás", "📦 Egyéb"])
            f_osszeg = st.number_input("HUF", min_value=0)
            f_d = st.date_input("Nap", datetime.now())
            if st.form_submit_button("📜 RÖGZÍTÉS"):
                requests.post(SCRIPT_URL, json={"is_fix":True, "nev":f_nev, "kategoria":f_kat, "osszeg":int(f_osszeg), "datum":str(f_d)})
                st.success("Fix tétel ütemezve!")
                st.rerun()

with tab2:
    if not df_main.empty:
        df_main['tipus_clean'] = df_main['tipus'].astype(str).str.lower()
        kiadas_df = df_main[df_main['tipus_clean'].str.contains("kiad|megtak", na=False)].copy()
        if not kiadas_df.empty:
            c_a, c_b = st.columns(2)
            # A grafikonok színeit is a userhez igazítjuk
            pie_color = px.colors.sequential.Greens if user == "👤 Andris" else px.colors.sequential.RdPu
            with c_a: 
                st.plotly_chart(px.pie(kiadas_df, values='osszeg', names='kategoria', title="Kiadások", color_discrete_sequence=pie_color), use_container_width=True)
            with c_b:
                kiadas_df['honap'] = pd.to_datetime(kiadas_df['datum']).dt.strftime('%Y-%m')
                st.plotly_chart(px.line(kiadas_df.groupby('honap')['osszeg'].sum().reset_index(), x='honap', y='osszeg', title="Havi trend"), use_container_width=True)

with tab3:
    st.write("**Tranzakcióid naplója:**")
    st.dataframe(df_main.sort_values('datum', ascending=False).head(30), use_container_width=True)

# --- LÁTVÁNY ELEMEK ---
if user == "👤 Zsóka":
    msgs = ["Micsoda elegancia!", "A parpák már várnak!", "Ragyogó könyvelés, Zsóka!", "Minden aranyad biztonságban!"]
    st.divider()
    st.markdown(f"<h3 style='text-align: center;'>🏇 {random.choice(msgs)}</h3>", unsafe_allow_html=True)
else:
    st.divider()
    st.markdown("<p style='text-align: center; color: #00FF41;'>[ SYSTEM OK ] _ Data stream integrity: 100% _ Access granted.</p>", unsafe_allow_html=True)

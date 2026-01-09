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
    # --- Retro Gaming / Matrix Színek ---
    retro_zold = "#00FF41" # Neon zöld
    retro_fekete = "#0D0208" # Mély terminál fekete
    grid_szin = "rgba(0, 255, 65, 0.1)" # Halvány neon rácsháló

    st.markdown(f"""
        <style>
        /* 1. RÁCSHÁLÓS HÁTTÉR ÉS ALAPSTÍLUS */
        .stApp {{ 
            background-color: {retro_fekete};
            background-image: 
                linear-gradient({grid_szin} 1px, transparent 1px),
                linear-gradient(90deg, {grid_szin} 1px, transparent 1px);
            background-size: 30px 30px; /* A rács négyzeteinek mérete */
            color: {retro_zold};
            font-family: 'Courier New', Courier, monospace !important;
        }}

        /* 2. TERMINÁL KERETEK ÉS MEZŐK */
        input, .stNumberInput input, div[data-baseweb="select"] > div, [data-testid="stDataFrame"] {{
            background-color: rgba(0, 0, 0, 0.8) !important;
            color: {retro_zold} !important;
            border: 1px solid {retro_zold} !important;
            border-radius: 0px !important; /* Szögletes, retro forma */
            font-family: 'Courier New', Courier, monospace !important;
        }}

        /* 3. NEON GOMBOK */
        .stButton>button {{ 
            background-color: transparent !important; 
            color: {retro_zold} !important; 
            border: 2px solid {retro_zold} !important;
            border-radius: 0px !important;
            text-transform: uppercase;
            font-weight: bold;
            box-shadow: 0 0 10px {retro_zold}; /* Neon ragyogás */
        }}
        
        .stButton>button:hover {{
            background-color: {retro_zold} !important;
            color: {retro_fekete} !important;
            box-shadow: 0 0 20px {retro_zold};
        }}

        /* 4. DIGITÁLIS CÍMEK */
        h1, h2, h3 {{ 
            color: {retro_zold} !important; 
            text-transform: uppercase;
            letter-spacing: 3px;
            border-left: 5px solid {retro_zold};
            padding-left: 10px;
        }}

        /* 5. TABS */
        .stTabs [data-baseweb="tab"] {{ 
            color: {retro_zold} !important;
            background-color: transparent !important;
        }}
        </style>
    """, unsafe_allow_html=True)
else:
    # --- Berni Pásztor: Fekete alap, Fehér gombok, Barna keretek ---
    berni_fekete = "#121212" # Mélyfekete háttér
    berni_barna  = "#A0522D" # Rozsdabarna keretekhez
    berni_feher  = "#FFFFFF" # Fehér gombokhoz és szöveghez
    
    st.markdown(f"""
        <style>
        /* 1. FŐ HÁTTÉR ÉS AZ OLDAL KERETE */
        .stApp {{ 
            background-color: {berni_fekete}; 
            color: {berni_feher};
            border: 10px solid {berni_barna}; 
            box-sizing: border-box;
        }}

        /* 2. BEVITELI MEZŐK ÉS TÁBLÁZATOK KERETEZÉSE */
        input, .stNumberInput input, div[data-baseweb="select"] > div, [data-testid="stDataFrame"] {{
            background-color: #1E1E1E !important; /* Sötétszürke belső */
            color: {berni_feher} !important;
            border: 2px solid {berni_barna} !important; /* BARNA KERET MINDENNEK */
            border-radius: 8px !important;
        }}

        /* 3. FEHÉR GOMBOK BARNA SZEGÉLLYEL */
        .stButton>button {{ 
            background-color: {berni_feher} !important; 
            color: {berni_fekete} !important; 
            border: 3px solid {berni_barna} !important;
            border-radius: 12px !important;
            font-weight: bold;
            width: 100%;
        }}
        
        /* Gomb hover: ha ráviszed az egeret, bebarnul */
        .stButton>button:hover {{
            background-color: {berni_barna} !important;
            color: {berni_feher} !important;
        }}

        /* 4. FEJLÉCEK ÉS SZÖVEGEK */
        h1, h2, h3 {{ 
            color: {berni_feher} !important; 
            text-shadow: 2px 2px {berni_barna}; /* Egy kis barna árnyék a betűknek */
            font-family: 'Georgia', serif;
        }}

        /* 5. TABS (FÜLEK) */
        .stTabs [data-baseweb="tab"] {{ 
            color: {berni_feher} !important;
            border-bottom: 2px solid {berni_barna};
        }}
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
            t = st.selectbox("Típus", ["📉 Kiadás", "📈 Bevétel", "💰 Megtakarítás", ])
            # NINCS NÉV VÁLASZTÓ - Automatikusan a 'user' változót használjuk lent
            k = st.selectbox("Kategória", [ "💵 Fizetés","🏠 Lakás/Rezsi", "🛒 Élelmiszer", "🏦 Hitel"," Egészségügy/Szépségápolás", "🚗 Közlekedés", "🐶 Monty", "📦 Egyéb"])
            
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

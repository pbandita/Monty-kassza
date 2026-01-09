import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
import io
import random
import time

# --- 0. ALAPBEÁLLÍTÁSOK ---
st.set_page_config(page_title="Andris & Zsóka Kassza", layout="wide", page_icon="💰")

# Google ID-k
SHEET_ID = "1sk5LgO3WHEq-EtSrK9xSrtAWnAX4fhO_KULE37DraIQ"
CSV_URL_MAIN = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
CSV_URL_FIXEK = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1493472585"
SCRIPT_URL = "https://script.google.com/macros/s/AKfycbwcVcDv5Y6uTvogFaUqsjI14N51ovegiqXBak6u9Dl7kzGrVf8JuEPZvJmFOE0X7kqffQ/exec"

# --- BELÉPÉSI LOGIKA ---
if 'user' not in st.session_state:
    st.title("🛡️ Kincstári Beléptető Kapu")
    col_a, col_z = st.columns(2)
    
    with col_a:
        if st.button("💻 ANDRIS", use_container_width=True):
            st.session_state.user = "👤 Andris"
            st.rerun()
            
    with col_z:
        if st.button("🏇 ZSÓKA", use_container_width=True):
            st.session_state.user = "👤 Zsóka"
            st.rerun()
    st.stop()

# --- BEJELENTKEZÉSI ANIMÁCIÓ ---
if 'animated' not in st.session_state:
    placeholder = st.empty()
    
    if st.session_state.user == "👤 Andris":
        with placeholder.container():
            lines = [
                "> BOOTING SYSTEM...",
                "> CONNECTING TO SECURE DATABASE...",
                "> ACCESS GRANTED: USER_ANDRIS",
                "> LOADING NEON_INTERFACE.SYS...",
                "> WELCOME TO THE GRID."
            ]
            full_text = ""
            for line in lines:
                current_line = ""
                for char in line:
                    current_line += char
                    placeholder.markdown(f"<code style='color:#00F2FF; font-size:20px;'>{full_text}{current_line}█</code>", unsafe_allow_html=True)
                    time.sleep(0.01)
                full_text += current_line + "<br>"
            time.sleep(0.5)
    else:
        with placeholder.container():
            st.markdown("<h2 style='text-align:center;'>🏰 A kastély kapui megnyílnak...</h2>", unsafe_allow_html=True)
            
            # Ez egy szebb, grafikus tappancs kódja (SVG)
            def get_paws_html(count):
                paw_svg = """
                <svg width="60" height="60" viewBox="0 0 100 100" style="margin: 10px;">
                    <path fill="#A0522D" d="M30 45c5 0 9-4 9-9s-4-9-9-9-9 4-9 9 4 9 9 9zm20-5c5 0 9-4 9-9s-4-9-9-9-9 4-9 9 4 9 9 9zm20 5c5 0 9-4 9-9s-4-9-9-9-9 4-9 9 4 9 9 9zM50 85c10 0 18-8 18-18 0-8-5-15-12-17-2-1-4-1-6-1s-4 0-6 1c-7 2-12 9-12 17 0 10 8 18 18 18z"/>
                </svg>
                """
                return f"<div style='display: flex; justify-content: center;'>{paw_svg * count}</div>"

            t_placeholder = st.empty()
            for i in range(1, 7):
                t_placeholder.markdown(get_paws_html(i), unsafe_allow_html=True)
                time.sleep(0.4)
            
            st.markdown("<h3 style='text-align:center;'>Üdvözlünk itthon, Zsóka!</h3>", unsafe_allow_html=True)
            time.sleep(1)
            
            # A végén egy kis ugráló kutyus üdvözlésnek
            st.markdown("<div style='display: flex; justify-content: center;'><img src='https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJic2t6bmZ6bmZ6bmZ6bmZ6bmZ6bmZ6bmZ6bmZ6bmZ6bmZ6bmZ6JmVwPXYxX2ludGVybmFsX2dpZl9ieV9pZCZjdD1z/5AtX86f3fDfyE/giphy.gif' width='150'></div>", unsafe_allow_html=True)
            st.markdown("<h3 style='text-align:center;'>Üdvözlünk itthon, Zsóka!</h3>", unsafe_allow_html=True)
            time.sleep(0.5)

# --- USER SPECIFIKUS DESIGN ---
user = st.session_state.user

if user == "👤 Andris":
    st.markdown(f"""
        <style>
        .stApp {{ 
            background-color: #050505;
            background-image: linear-gradient(rgba(0, 242, 255, 0.15) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 242, 255, 0.15) 1px, transparent 1px);
            background-size: 40px 40px; color: #00F2FF; font-family: 'Lucida Console', Monaco, monospace !important;
        }}
        .stApp::before {{
            content: ""; position: fixed; top: 0; left: -100%; width: 100%; height: 3px;
            background: linear-gradient(90deg, transparent, #00F2FF, #FFFFFF, #00F2FF, transparent);
            animation: sweep 3s infinite; z-index: 1000;
        }}
        @keyframes sweep {{ 0% {{ left: -100%; }} 50% {{ left: 100%; }} 100% {{ left: 100%; }} }}
        input, .stNumberInput input, div[data-baseweb="select"] > div, [data-testid="stDataFrame"] {{
            background-color: rgba(0, 20, 30, 0.9) !important; color: white !important;
            border: 1px solid #00F2FF !important; box-shadow: inset 0 0 5px #00F2FF;
        }}
        .stButton>button {{ 
            background-color: transparent !important; color: #00F2FF !important; 
            border: 2px solid #00F2FF !important; box-shadow: 0 0 15px #00F2FF;
        }}
        h1, h2, h3 {{ color: white !important; text-shadow: 0 0 10px #00F2FF; }}
        </style>
    """, unsafe_allow_html=True)
else:
    berni_barna = "#A0522D"
    tappancs_svg = f"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40' viewBox='0 0 100 100'%3E%3Cpath fill='%23{berni_barna[1:]}' fill-opacity='0.2' d='M30 45c5 0 9-4 9-9s-4-9-9-9-9 4-9 9 4 9 9 9zm20-5c5 0 9-4 9-9s-4-9-9-9-9 4-9 9 4 9 9 9zm20 5c5 0 9-4 9-9s-4-9-9-9-9 4-9 9 4 9 9 9zM50 85c10 0 18-8 18-18 0-8-5-15-12-17-2-1-4-1-6-1s-4 0-6 1c-7 2-12 9-12 17 0 10 8 18 18 18z'/%3E%3C/svg%3E"
    st.markdown(f"""
        <style>
        .stApp {{ background-color: #121212 !important; background-image: url("{tappancs_svg}"); color: white; border: 10px solid {berni_barna}; }}
        .stButton>button {{ background-color: white !important; color: #121212 !important; border: 3px solid {berni_barna} !important; border-radius: 12px !important; }}
        h1, h2, h3 {{ color: white !important; text-shadow: 2px 2px {berni_barna}; }}
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
    if 'animated' in st.session_state: del st.session_state.animated
    st.rerun()

tab1, tab2, tab3 = st.tabs(["📝 Könyvelés", "📊 Statisztika", "📅 Adatbázis"])

with tab1:
    st.write(f"💵 **Árfolyam:** 1 EUR = {rate:.2f} HUF")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🆕 Új tranzakció")
        with st.form("main_f", clear_on_submit=True):
            d = st.date_input("Dátum", datetime.now())
            t = st.selectbox("Típus", ["📉 Kiadás", "📈 Bevétel", "💰 Megtakarítás"])
            k = st.selectbox("Kategória", ["💵 Fizetés","🏠 Lakás/Rezsi", "🛒 Élelmiszer", "🏦 Hitel", "Egészségügy/Szépségápolás", "🚗 Közlekedés", "🐶 Monty", "📦 Egyéb"])
            v_c1, v_c2 = st.columns([1,2])
            valuta = v_c1.selectbox("Pénznem", ["HUF", "EUR"])
            osszeg = v_c2.number_input("Összeg", min_value=0.0)
            megj = st.text_input("Megjegyzés")
            if st.form_submit_button("Mentés"):
                final = int(osszeg if valuta == "HUF" else osszeg * rate)
                requests.post(SCRIPT_URL, json={"is_fix": False, "datum": str(d), "tipus": t, "szemely": user, "kategoria": k, "osszeg": final, "megjegyzes": megj})
                st.success("Sikeres mentés!")
                st.rerun()

    with c2:
        st.subheader("🔁 Havi fix rögzítése")
        with st.form("fix_f", clear_on_submit=True):
            f_nev = st.text_input("Fix kiadás neve")
            f_kat = st.selectbox("Kategória", ["🏠 Lakás/Rezsi", "🏦 Hitel", "💰 Megtakarítás", "📦 Egyéb"])
            f_osszeg = st.number_input("HUF", min_value=0)
            f_d = st.date_input("Nap", datetime.now())
            if st.form_submit_button("Rögzítés"):
                requests.post(SCRIPT_URL, json={"is_fix":True, "nev":f_nev, "kategoria":f_kat, "osszeg":int(f_osszeg), "datum":str(f_d)})
                st.success("Fix tétel ütemezve!")
                st.rerun()

with tab2:
    if not df_main.empty:
        df_main['tipus_clean'] = df_main['tipus'].astype(str).str.lower()
        kiadas_df = df_main[df_main['tipus_clean'].str.contains("kiad|megtak", na=False)].copy()
        if not kiadas_df.empty:
            c_a, c_b = st.columns(2)
            pie_color = px.colors.sequential.Greens if user == "👤 Andris" else px.colors.sequential.RdPu
            with c_a: st.plotly_chart(px.pie(kiadas_df, values='osszeg', names='kategoria', title="Kiadások", color_discrete_sequence=pie_color), use_container_width=True)
            with c_b:
                kiadas_df['honap'] = pd.to_datetime(kiadas_df['datum']).dt.strftime('%Y-%m')
                st.plotly_chart(px.line(kiadas_df.groupby('honap')['osszeg'].sum().reset_index(), x='honap', y='osszeg', title="Havi trend"), use_container_width=True)

with tab3:
    st.write("**Tranzakcióid naplója:**")
    if not df_main.empty:
        st.dataframe(df_main.head(30), use_container_width=True)
        st.divider()
        st.subheader("🗑️ Sor törlése")
        row_to_delete = st.number_input("Törlendő sor indexe:", min_value=0, max_value=len(df_main)-1, step=1)
        if st.button("❌ VÉGLEGES TÖRLÉS"):
            res = requests.post(SCRIPT_URL, json={"action": "delete", "row_index": int(row_to_delete)})
            if "Törlés" in res.text or res.status_code == 200:
                st.success("Törölve!")
                st.cache_data.clear()
                st.rerun()
    else:
        st.info("Üres a táblázat.")

# --- LÁTVÁNY ELEMEK ---
st.divider()
if user == "👤 Zsóka":
    st.markdown(f"<h3 style='text-align: center;'>🏇 {random.choice(['Micsoda elegancia!', 'Ragyogó könyvelés!', 'Biztonságban az arany!'])}</h3>", unsafe_allow_html=True)
else:
    st.markdown("<p style='text-align: center; color: #00F2FF;'>[ SYSTEM OK ] _ Data stream integrity: 100%</p>", unsafe_allow_html=True)

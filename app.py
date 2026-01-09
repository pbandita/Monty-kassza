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
        if st.button("💻 ANDRIS", use_container_width=True):
            st.session_state.user = "👤 Andris"
            st.rerun()
            
    with col_z:
        if st.button("🏇 ZSÓKA", use_container_width=True):
            st.session_state.user = "👤 Zsóka"
            st.rerun()
    st.stop() # Megállítjuk a kódot, amíg nincs választás

# --- USER SPECIFIKUS DESIGN ---
user = st.session_state.user

if user == "👤 Andris":
    # --- Neon Blue Retro Gaming Színek ---
    retro_feher = "#FFFFFF"
    neon_kek = "#00F2FF"    # Világító ciánkék / Neon kék
    retro_fekete = "#050505" # Majdnem teljes fekete
    grid_szin = "rgba(0, 242, 255, 0.15)" # Neon kék rácsháló

    st.markdown(f"""
        <style>
        /* 1. RÁCSHÁLÓS HÁTTÉR */
        .stApp {{ 
            background-color: {retro_fekete};
            background-image: 
                linear-gradient({grid_szin} 1px, transparent 1px),
                linear-gradient(90deg, {grid_szin} 1px, transparent 1px);
            background-size: 40px 40px; 
            color: {neon_kek};
            font-family: 'Lucida Console', Monaco, monospace !important;
        }}

        /* 2. MEZŐK ÉS TÁBLÁZATOK - KÉK KERETTEL */
        input, .stNumberInput input, div[data-baseweb="select"] > div, [data-testid="stDataFrame"] {{
            background-color: rgba(0, 20, 30, 0.9) !important; /* Mélykék fekete belső */
            color: {retro_feher} !important;
            border: 1px solid {neon_kek} !important;
            border-radius: 0px !important;
            font-family: 'Lucida Console', Monaco, monospace !important;
            box-shadow: inset 0 0 5px {neon_kek}; /* Belső izzás a mezőknek */
        }}

        /* 3. NEON KÉK GOMBOK */
        .stButton>button {{ 
            background-color: transparent !important; 
            color: {neon_kek} !important; 
            border: 2px solid {neon_kek} !important;
            border-radius: 4px !important;
            text-transform: uppercase;
            font-weight: bold;
            box-shadow: 0 0 15px {neon_kek}; /* Kék neon ragyogás */
            transition: all 0.3s ease-in-out;
        }}
        
        .stButton>button:hover {{
            background-color: {neon_kek} !important;
            color: {retro_fekete} !important;
            box-shadow: 0 0 30px {neon_kek};
            transform: translateY(-2px);
        }}

        /* 4. FEJLÉCEK */
        h1, h2, h3 {{ 
            color: {retro_feher} !important; 
            text-transform: uppercase;
            letter-spacing: 5px;
            text-shadow: 0 0 10px {neon_kek};
        }}

        /* 5. TABS */
        .stTabs [data-baseweb="tab"] {{ 
            color: {retro_feher} !important;
        }}

        /* Scrollbar (görgetősáv) testreszabása a kék stílushoz */
        ::-webkit-scrollbar {{ width: 8px; }}
        ::-webkit-scrollbar-track {{ background: {retro_fekete}; }}
        ::-webkit-scrollbar-thumb {{ background: {neon_kek}; border-radius: 10px; }}
        </style>
    """, unsafe_allow_html=True)
else:
    # --- Berni Pásztor: Fekete alap, Barna tappancsok, Fehér gombok ---
    berni_fekete = "#121212" 
    berni_barna  = "#A0522D" 
    berni_feher  = "#FFFFFF" 
    
    # Tappancs minta SVG
    tappancs_svg = f"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40' viewBox='0 0 100 100'%3E%3Cpath fill='%23{berni_barna[1:]}' fill-opacity='0.2' d='M30 45c5 0 9-4 9-9s-4-9-9-9-9 4-9 9 4 9 9 9zm20-5c5 0 9-4 9-9s-4-9-9-9-9 4-9 9 4 9 9 9zm20 5c5 0 9-4 9-9s-4-9-9-9-9 4-9 9 4 9 9 9zM50 85c10 0 18-8 18-18 0-8-5-15-12-17-2-1-4-1-6-1s-4 0-6 1c-7 2-12 9-12 17 0 10 8 18 18 18z'/%3E%3C/svg%3E"

    st.markdown(f"""
        <style>
        .stApp {{ 
            background-color: {berni_fekete} !important; 
            background-image: url("{tappancs_svg}");
            background-repeat: repeat;
            background-size: 70px 70px;
            color: {berni_feher};
            border: 10px solid {berni_barna}; 
            box-sizing: border-box;
        }}

        input, .stNumberInput input, div[data-baseweb="select"] > div, [data-testid="stDataFrame"] {{
            background-color: rgba(30, 30, 30, 0.9) !important;
            color: {berni_feher} !important;
            border: 2px solid {berni_barna} !important;
            border-radius: 8px !important;
        }}

        .stButton>button {{ 
            background-color: {berni_feher} !important; 
            color: {berni_fekete} !important; 
            border: 3px solid {berni_barna} !important;
            border-radius: 12px !important;
            font-weight: bold;
            width: 100%;
        }}
        
        .stButton>button:hover {{
            background-color: {berni_barna} !important;
            color: {berni_feher} !important;
        }}

        h1, h2, h3 {{ 
            color: {berni_feher} !important; 
            text-shadow: 2px 2px {berni_barna};
            font-family: 'Georgia', serif;
            text-align: center;
        }}

        .stTabs [data-baseweb="tab"] {{
            color: {berni_feher} !important;
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
    st.subheader("Sor törlése a Google Sheets-ből")

if not df_main.empty:
    # Kiválasztjuk a sorszámot (a táblázat bal szélén látható szám)
    row_to_delete = st.number_input("Törlendő sor száma:", 
                                    min_value=0, 
                                    max_value=len(df_main)-1, 
                                    step=1)

    if st.button("❌ Végleges törlés a táblázatból"):
        try:
            # 1. Kapcsolódás a Sheets-hez (ezt a conn-t használod felül is)
            # A Google Sheets-ben a fejléc az 1. sor, az adatok a 2. sortól indulnak.
            # Mivel a dataframe indexe 0-tól indul, a Sheets-ben ez a (row_to_delete + 2). sor lesz.
            sheet_row_index = int(row_to_delete) + 2
            
            # 2. Törlés parancs küldése a Google-nek
            # Itt a 'Sheet1' helyére írd a munkalapod pontos nevét, ha más!
            conn.delete_rows("Sheet1", row_indices=[sheet_row_index])
            
            st.success(f"A(z) {row_to_delete}. sorszámú sor sikeresen törölve a Google táblázatból!")
            
            # 3. Gyorsítótár ürítése és oldal újratöltése, hogy az új adatokat lássuk
            st.cache_data.clear()
            st.rerun()
            
        except Exception as e:
            st.error(f"Hiba történt a törlés során: {e}")
else:
    st.info("A táblázat üres, nincs mit törölni.")
# --- LÁTVÁNY ELEMEK ---
if user == "👤 Zsóka":
    msgs = ["Micsoda elegancia!", "A parpák már várnak!", "Ragyogó könyvelés, Zsóka!", "Minden aranyad biztonságban!"]
    st.divider()
    st.markdown(f"<h3 style='text-align: center;'>🏇 {random.choice(msgs)}</h3>", unsafe_allow_html=True)
else:
    st.divider()
    st.markdown("<p style='text-align: center; color: #00FF41;'>[ SYSTEM OK ] _ Data stream integrity: 100% _ Access granted.</p>", unsafe_allow_html=True)

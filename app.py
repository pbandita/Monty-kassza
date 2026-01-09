import streamlit as st
import pandas as pd
import plotly.express as px
import requests
from datetime import datetime
import io
import random

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
    st.stop()

# --- USER SPECIFIKUS DESIGN ---
user = st.session_state.user

if user == "👤 Andris":
    retro_feher = "#FFFFFF"
    neon_kek = "#00F2FF"
    retro_fekete = "#050505"
    grid_szin = "rgba(0, 242, 255, 0.15)"

    st.markdown(f"""
        <style>
        .stApp {{ 
            background-color: {retro_fekete};
            background-image: linear-gradient({grid_szin} 1px, transparent 1px), linear-gradient(90deg, {grid_szin} 1px, transparent 1px);
            background-size: 40px 40px; color: {neon_kek}; font-family: 'Lucida Console', Monaco, monospace !important;
        }}
        input, .stNumberInput input, div[data-baseweb="select"] > div, [data-testid="stDataFrame"] {{
            background-color: rgba(0, 20, 30, 0.9) !important; color: {retro_feher} !important;
            border: 1px solid {neon_kek} !important; border-radius: 0px !important;
            box-shadow: inset 0 0 5px {neon_kek};
        }}
        .stButton>button {{ 
            background-color: transparent !important; color: {neon_kek} !important; 
            border: 2px solid {neon_kek} !important; border-radius: 4px !important;
            text-transform: uppercase; font-weight: bold; box-shadow: 0 0 15px {neon_kek};
        }}
        .stButton>button:hover {{ background-color: {neon_kek} !important; color: {retro_fekete} !important; box-shadow: 0 0 30px {neon_kek}; }}
        h1, h2, h3 {{ color: {retro_feher} !important; text-transform: uppercase; letter-spacing: 5px; text-shadow: 0 0 10px {neon_kek}; }}
        .stTabs [data-baseweb="tab"] {{ color: {retro_feher} !important; }}
        </style>
    """, unsafe_allow_html=True)
else:
    berni_fekete = "#121212" 
    berni_barna  = "#A0522D" 
    berni_feher  = "#FFFFFF" 
    tappancs_svg = f"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='40' height='40' viewBox='0 0 100 100'%3E%3Cpath fill='%23{berni_barna[1:]}' fill-opacity='0.2' d='M30 45c5 0 9-4 9-9s-4-9-9-9-9 4-9 9 4 9 9 9zm20-5c5 0 9-4 9-9s-4-9-9-9-9 4-9 9 4 9 9 9zm20 5c5 0 9-4 9-9s-4-9-9-9-9 4-9 9 4 9 9 9zM50 85c10 0 18-8 18-18 0-8-5-15-12-17-2-1-4-1-6-1s-4 0-6 1c-7 2-12 9-12 17 0 10 8 18 18 18z'/%3E%3C/svg%3E"

    st.markdown(f"""
        <style>
        .stApp {{ background-color: {berni_fekete} !important; background-image: url("{tappancs_svg}"); background-repeat: repeat; background-size: 70px 70px; color: {berni_feher}; border: 10px solid {berni_barna}; box-sizing: border-box; }}
        input, .stNumberInput input, div[data-baseweb="select"] > div, [data-testid="stDataFrame"] {{ background-color: rgba(30, 30, 30, 0.9) !important; color: {berni_feher} !important; border: 2px solid {berni_barna} !important; border-radius: 8px !important; }}
        .stButton>button {{ background-color: {berni_feher} !important; color: {berni_fekete} !important; border: 3px solid {berni_barna} !important; border-radius: 12px !important; font-weight: bold; width: 100%; }}
        .stButton>button:hover {{ background-color: {berni_barna} !important; color: {berni_feher} !important; }}
        h1, h2, h3 {{ color: {berni_feher} !important; text-shadow: 2px 2px {berni_barna}; font-family: 'Georgia', serif; text-align: center; }}
        .stTabs [data-baseweb="tab"] {{ color: {berni_feher} !important; }}
        </style>
    """, unsafe_allow_html=True)

# --- ADATOK BETÖLTÉSE ---
@st.cache_

import streamlit as st
import pandas as pd
import plotly.express as px
import json
import requests

st.set_page_config(page_title="Mapa Exportaciones de Carne", layout="wide")
st.title("🗺️ Exportaciones de Carne por Estado - México")

# ── Cargar datos ──────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("empresas_exportadoras.csv", encoding="utf-8-sig", low_memory=False)
    df["Producto"] = df["Producto"].str.strip()
    df = df.dropna(subset=["Estado", "Producto"])
    df["US FOB"] = pd.to_numeric(df["US FOB"], errors="coerce").fillna(0)
    df["Volumen (kg)"] = pd.to_numeric(df["Volumen (kg)"], errors="coerce").fillna(0)
    return df

df = load_data()

# ── GeoJSON estados de México ─────────────────────────────────────────────────
@st.cache_data
def load_geojson():
    url = "https://raw.githubusercontent.com/angelnmara/geojson/master/mexicoHigh.json"
    try:
        resp = requests.get(url, timeout=15)
        return resp.json()
    except Exception:
        return None

geojson = load_geojson()

# ── Mapeo de nombres Estado → clave GeoJSON ───────────────────────────────────
state_name_map = {
    "Baja California": "Baja California",
    "Baja California Sur": "Baja California Sur",
    "Chihuahua": "Chihuahua",
    "Coahuila": "Coahuila de Zaragoza",
    "Sonora": "Sonora",
    "Nuevo Leon": "Nuevo León",
    "Nuevo León": "Nuevo León",
    "Tamaulipas": "Tamaulipas",
    "Jalisco": "Jalisco",
    "Ciudad de Mexico": "Ciudad de México",
    "Ciudad de México": "Ciudad de México",
    "Sinaloa": "Sinaloa",
    "Durango": "Durango",
    "Guanajuato": "Guanajuato",
    "Michoacan": "Michoacán de Ocampo",
    "Michoacán": "Michoacán de Ocampo",
    "Estado de Mexico": "México",
    "Puebla": "Puebla",
    "Veracruz": "Veracruz de Ignacio de la Llave",
    "Yucatan": "Yucatán",
    "Yucatán": "Yucatán",
}

df["Estado_geo"] = df["Estado"].map(state_name_map).fillna(df["Estado"])

# ── Sidebar: filtr
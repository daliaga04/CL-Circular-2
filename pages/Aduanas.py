# pages/3_Analisis_Aduana.py

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Análisis por Aduana", layout="wide")
st.title("📊 Análisis por Aduana Fronteriza")

# --- Cargar datos ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(
    os.path.join(BASE_DIR, "..", "empresas_exportadoras.csv"),
    encoding="utf-8-sig"
)
df.columns = df.columns.str.strip()

# --- Fechas ---
def excel_to_date(serial):
    if pd.isna(serial):
        return None
    return datetime(1899, 12, 30) + timedelta(days=int(serial))

df["Fecha_dt"] = df["Fecha"].apply(excel_to_date)
df["Mes"] = df["Fecha_dt"].dt.to_period("M").astype(str)

# --- Tipo Carne ---
tipo_map = {
    "Carne Bovino Fresca/Refrigerada": "Bovino",
    "Carne Bovino Congelado": "Bovino",
    "Carne Cerdo": "Cerdo",
}
df["Tipo Carne"] = df["Producto"].map(tipo_map).fillna("Otro")
df["Valor (USD M)"] = df["US FOB"] / 1_000_000
df["Volumen (t)"]   = df["Volumen (kg)"] / 1_000

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.header("⚙️ Filtros")

tipo_seleccion = st.sidebar.radio(
    "Tipo de carne",
    options=["Total", "Bovino", "Cerdo"],
    index=0,
)

meses_disponibles = sorted(df["Mes"].dropna().unique())
rango_meses = st.sidebar.select_slider(
    "Rango de meses",
    options=meses_disponibles,
    value=(meses_disponibles[0], meses_disponibles[-1]),
)

aduanas_disponibles = sorted(df["Aduana"].dropna().unique())
aduanas_seleccion = st.sidebar.multiselect(
    "Filtrar aduanas (vacío = todas)",
    options=aduanas_disponibles,
    default=[],
)

# --- Aplicar filtros ---
df_filtrado = df[
    (df["Mes"] >= rango_meses[0]) & (

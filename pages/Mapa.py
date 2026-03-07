import os
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json

st.set_page_config(page_title="Mapa de Exportaciones", layout="wide")
st.title("🗺️ Mapa de Exportaciones de Carne Bovina por Estado")

# --- Cargar datos ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(
    os.path.join(BASE_DIR, "..", "empresas_exportadoras.csv"),
    encoding="utf-8-sig"
)
df.columns = df.columns.str.strip()

# --- Agregar por estado ---
agg = df.groupby("Estado").agg({
    "Valor Anual (USD M)": "sum",
    "Volumen Anual  (t)": "sum"
}).reset_index()

# --- Mapeo de nombres del CSV → nombres del GeoJSON ---
# El GeoJSON de angelnmara usa nombres con acentos y formato específico
nombre_geojson = {
    "Aguascalientes": "Aguascalientes",
    "Baja California": "Baja California",
    "Baja California Sur": "Baja California Sur",
    "Campeche": "Campeche",
    "Chiapas": "Chiapas",
    "Chihuahua": "Chihuahua",
    "Coahuila": "Coahuila",
    "Colima": "Colima",
    "Durango": "Durango",
    "Guanajuato": "Guanajuato",
    "Guerrero": "Guerrero",
    "Hidalgo": "Hidalgo",
    "Jalisco": "Jalisco",
    "Michoacán": "Michoacán",
    "Morelos": "Morelos",
    "México": "México",
    "Nayarit": "Nayarit",
    "Nuevo León": "Nuevo León",
    "Oaxaca": "Oaxaca",
    "Puebla": "Puebla",
    "Querétaro": "Querétaro",
    "Quintana Roo": "Quintana Roo",
    "San Luis Potosí": "San Luis Potosí",
    "Sinaloa": "Sinaloa",
    "Sonora": "Sonora",
    "Tabasco": "Tabasco",
    "Tamaulipas": "Tamaulipas",
    "Tlaxcala": "Tlaxcala",
    "Veracruz": "Veracruz",
    "Yucatán": "Yucatán",
    "Zacatecas": "Zacatecas",
    "CDMX": "Distrito Federal",
}

agg["estado_geo"] = agg["Estado"].map(nombre_geojson).fillna(agg["Estado"])

# --- Cargar GeoJSON de México ---
@st.cache_data
def cargar_geojson():
    url = "https://raw.githubusercontent.com/angelnmara/geojson/master/mexicoHigh.json"
    response = requests.get(url)
    return json.loads(response.text)

mx_geo = cargar_geojson()

# --- Filtro ---
st.markdown("### Selecciona la variable a visualizar")
variable = st.radio(
    "Variable:",
    options=["Valor Anual (USD M)", "Volumen Anual  (t)"],
    horizontal=True,
    label_visibility="collapsed"
)

# Configuración según variable seleccionada
if variable == "Valor Anual (USD M)":
    color_label = "Valor (USD M)"
    titulo = "Valor Anual de Exportación por Estado (USD Millones)"
    color_scale = "YlOrRd"
else:
    color_label = "Volumen (t)"
    titulo = "Volumen Anual de Exportación por Estado (Toneladas)"
    color_scale = "Blues"

# --- Mapa Choropleth ---
fig = px.choropleth(
    agg,
    geojson=mx_geo,
    locations="estado_geo",
    featureidkey="properties.name",
    color=variable,
    color_continuous_scale=color_scale,
    hover_name="Estado",
    hover_data={
        "Valor Anual (USD M)": ":,.0f",
        "Volumen Anual  (t)": ":,.0f",
        "estado_geo": False,
    },
    labels={variable: color_label},
    title=titulo,
)

fig.update_geos(
    fitbounds="locations",
    visible=False,
    showcountries=False,
    showcoastlines=True,
    showland=True,
    landcolor="lightgray",
)

fig.update_layout(
    margin={"r": 0, "t": 50, "l": 0, "b": 0},
    height=650,
    coloraxis_colorbar=dict(
        title=color_label,
        thickness=20,
        len=0.6,
    ),
)

st.plotly_chart(fig, use_container_width=True)

# --- Tabla resumen ---
st.markdown("### Detalle por Estado")
tabla = agg[["Estado", "Valor Anual (USD M)", "Volumen Anual  (t)"]].sort_values(
    by=variable, ascending=False
).reset_index(drop=True)
tabla.index = tabla.index + 1
st.dataframe(tabla, use_container_width=True)

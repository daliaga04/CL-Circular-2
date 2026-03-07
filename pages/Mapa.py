import os
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json

st.set_page_config(page_title="Mapa de Exportaciones", layout="wide")
st.title("🗺️ Mapa de Exportaciones de Carne por Estado")

# --- Cargar datos ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(
    os.path.join(BASE_DIR, "..", "empresas_exportadoras.csv"),
    encoding="utf-8-sig"
)
df.columns = df.columns.str.strip()

# Esperamos columnas: "#", "Empresa", "Tipo Carne", "Estado",
# "Valor Anual (USD M)", "Volumen Anual  (t)", ...
# [file:158]

# --- Agregar por estado y tipo de carne ---
agg = df.groupby(["Estado", "Tipo Carne"], as_index=False).agg({
    "Valor Anual (USD M)": "sum",
    "Volumen Anual  (t)": "sum"
})

# Agregado total (todas las carnes) por estado
agg_total = agg.groupby("Estado", as_index=False).agg({
    "Valor Anual (USD M)": "sum",
    "Volumen Anual  (t)": "sum"
})
agg_total["Tipo Carne"] = "Total"

# Unir todo en un solo dataframe
agg_all = pd.concat([agg_total, agg], ignore_index=True)

# --- Mapeo nombres CSV → nombres GeoJSON ---
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

agg_all["estado_geo"] = agg_all["Estado"].map(nombre_geojson).fillna(agg_all["Estado"])

# --- Cargar GeoJSON de México ---
@st.cache_data
def cargar_geojson():
    url = "https://raw.githubusercontent.com/angelnmara/geojson/master/mexicoHigh.json"
    response = requests.get(url)
    return json.loads(response.text)

mx_geo = cargar_geojson()

# --- Controles (filtros) ---
st.markdown("### Filtros")

col_tipo, col_var = st.columns(2)

with col_tipo:
    tipo_seleccion = st.radio(
        "Tipo de carne",
        options=["Total", "Bovino", "Cerdo"],
        index=0,
        horizontal=True
    )

with col_var:
    variable = st.radio(
        "Variable a visualizar",
        options=["Valor Anual (USD M)", "Volumen Anual  (t)"],
        index=0,
        horizontal=True
    )

# Filtrar según tipo de carne
df_plot = agg_all[agg_all["Tipo Carne"] == tipo_seleccion].copy()

# Configuración según variable seleccionada
if variable == "Valor Anual (USD M)":
    color_label = "Valor (USD M)"
    titulo_var = "Valor Anual de Exportación (USD Millones)"
    color_scale = "YlOrRd"
else:
    color_label = "Volumen (t)"
    titulo_var = "Volumen Anual de Exportación (Toneladas)"
    color_scale = "Blues"

titulo = f"{titulo_var} — {tipo_seleccion}"

# --- Mapa Choropleth ---
fig = px.choropleth(
    df_plot,
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
        "Tipo Carne": True,
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

tabla = df_plot[["Estado", "Tipo Carne", "Valor Anual (USD M)", "Volumen Anual  (t)"]] \
    .sort_values(by=variable, ascending=False) \
    .reset_index(drop=True)
tabla.index = tabla.index + 1

st.dataframe(tabla, use_container_width=True)

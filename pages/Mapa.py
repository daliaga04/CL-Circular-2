import os
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
from datetime import datetime, timedelta

st.set_page_config(page_title="Mapa de Exportaciones", layout="wide")
st.title("🗺️ Exportaciones de Carne por Estado")

# --- Cargar datos ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(
    os.path.join(BASE_DIR, "..", "empresas_exportadoras.csv"),
    encoding="utf-8-sig"
)
df.columns = df.columns.str.strip()

# --- Convertir fecha de serial Excel a datetime ---
def excel_to_date(serial):
    if pd.isna(serial):
        return None
    return datetime(1899, 12, 30) + timedelta(days=int(serial))

df["Fecha_dt"] = df["Fecha"].apply(excel_to_date)
df["Mes"] = df["Fecha_dt"].dt.to_period("M").astype(str)

# --- Tipo Carne ---
tipo_map = {
    "Carne Bovino Fresca/Refrigerada": "Bovino Fresco/Refrigerado",
    "Carne Bovino Congelado": "Bovino Congelado",
    "Carne Cerdo": "Cerdo",
}
df["Tipo Carne"] = df["Producto"].str.strip().map(tipo_map).fillna("Otro")

# --- Convertir unidades ---
df["Valor (USD M)"] = df["US FOB"] / 1_000_000
df["Volumen (t)"] = df["Volumen (kg)"] / 1_000

# --- Mapeo nombres CSV → GeoJSON ---
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
    "Michoacan": "Michoacán",
    "Morelos": "Morelos",
    "Estado de Mexico": "México",
    "Ciudad de Mexico": "Distrito Federal",
    "Nayarit": "Nayarit",
    "Nuevo Leon": "Nuevo León",
    "Oaxaca": "Oaxaca",
    "Puebla": "Puebla",
    "Queretaro": "Querétaro",
    "Quintana Roo": "Quintana Roo",
    "San Luis Potosi": "San Luis Potosí",
    "Sinaloa": "Sinaloa",
    "Sonora": "Sonora",
    "Tabasco": "Tabasco",
    "Tamaulipas": "Tamaulipas",
    "Tlaxcala": "Tlaxcala",
    "Veracruz": "Veracruz",
    "Yucatan": "Yucatán",
    "Zacatecas": "Zacatecas",
}

# --- Cargar GeoJSON ---
@st.cache_data
def cargar_geojson():
    url = "https://raw.githubusercontent.com/angelnmara/geojson/master/mexicoHigh.json"
    response = requests.get(url)
    return json.loads(response.text)

mx_geo = cargar_geojson()

# =====================================================
# FILTROS EN PÁGINA
# =====================================================
st.subheader("⚙️ Filtros")

col_f1, col_f2, col_f3 = st.columns([1, 2, 1])

with col_f1:
    tipo_seleccion = st.radio(
        "Tipo de carne",
        options=["Total", "Bovino Fresco/Refrigerado", "Bovino Congelado", "Cerdo"],
        index=0,
    )

meses_disponibles = sorted(df["Mes"].dropna().unique())

with col_f2:
    rango_meses = st.select_slider(
        "Rango de meses",
        options=meses_disponibles,
        value=(meses_disponibles[0], meses_disponibles[-1]),
    )

with col_f3:
    variable = st.radio(
        "Variable a visualizar",
        options=["Valor (USD M)", "Volumen (t)"],
        index=0,
    )

st.divider()

# --- Filtrar datos ---
df_filtrado = df[
    (df["Mes"] >= rango_meses[0]) & (df["Mes"] <= rango_meses[1])
].copy()

if tipo_seleccion != "Total":
    df_filtrado = df_filtrado[df_filtrado["Tipo Carne"] == tipo_seleccion]

# =====================================================
# MAPA COROPLÉTICO
# =====================================================
st.subheader("Exportaciones por Estado")

agg_estado = df_filtrado.groupby("Estado", as_index=False).agg({
    "Valor (USD M)": "sum",
    "Volumen (t)": "sum",
    "US FOB": "count",
}).rename(columns={"US FOB": "Embarques"})

agg_estado["estado_geo"] = agg_estado["Estado"].map(nombre_geojson).fillna(agg_estado["Estado"])

if variable == "Valor (USD M)":
    color_label = "Valor (USD M)"
    titulo_var = "Valor de Exportación (USD Millones)"
    color_scale = "YlOrRd"
else:
    color_label = "Volumen (t)"
    titulo_var = "Volumen de Exportación (Toneladas)"
    color_scale = "Blues"

titulo = f"{titulo_var} — {tipo_seleccion} ({rango_meses[0]} a {rango_meses[1]})"

fig_mapa = px.choropleth(
    agg_estado,
    geojson=mx_geo,
    locations="estado_geo",
    featureidkey="properties.name",
    color=variable,
    color_continuous_scale=color_scale,
    hover_name="Estado",
    hover_data={
        "Valor (USD M)": ":,.2f",
        "Volumen (t)": ":,.1f",
        "Embarques": ":,",
        "estado_geo": False,
    },
    labels={variable: color_label},
    title=titulo,
)

fig_mapa.update_geos(
    fitbounds="locations",
    visible=False,
    showcountries=False,
    showcoastlines=True,
    showland=True,
    landcolor="lightgray",
)

fig_mapa.update_layout(
    margin={"r": 0, "t": 50, "l": 0, "b": 0},
    height=650,
    coloraxis_colorbar=dict(title=color_label, thickness=20, len=0.6),
)

st.plotly_chart(fig_mapa, use_container_width=True)

# --- Tabla resumen ---
st.markdown("#### Detalle por Estado")
tabla = agg_estado[["Estado", "Embarques", "Valor (USD M)", "Volumen (t)"]]\
    .sort_values(by=variable, ascending=False)\
    .reset_index(drop=True)
tabla.index = tabla.index + 1
tabla["Valor (USD M)"] = tabla["Valor (USD M)"].map("{:,.2f}".format)
tabla["Volumen (t)"] = tabla["Volumen (t)"].map("{:,.1f}".format)
tabla["Embarques"] = tabla["Embarques"].map("{:,}".format)
st.dataframe(tabla, use_container_width=True)

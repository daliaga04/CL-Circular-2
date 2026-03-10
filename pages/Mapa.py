import os
import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json

st.set_page_config(page_title="Mapa de Exportaciones", layout="wide")
st.title("🗺️ Exportaciones de Carne por Estado")

# --- Cargar datos ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(
    os.path.join(BASE_DIR, "..", "empresas_exportadoras.csv"),
    encoding="utf-8-sig"
)
df.columns = df.columns.str.strip()

# --- Tipo Carne ---
tipo_map = {
    "Carne Bovino Fresca/Refrigerada": "Bovino Fresco/Refrigerado",
    "Carne Bovino Congelado": "Bovino Congelado",
    "Carne Cerdo": "Cerdo",
}
df["Tipo Carne"] = df["Producto"].str.strip().map(tipo_map).fillna("Otro")
df["Valor (USD M)"] = df["US FOB"] / 1_000_000
df["Volumen (t)"]   = df["Volumen (kg)"] / 1_000

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
# SIDEBAR — FILTROS
# =====================================================
st.sidebar.header("⚙️ Filtros")

tipo_seleccion = st.sidebar.radio(
    "Tipo de carne",
    options=["Total", "Bovino Fresco/Refrigerado", "Bovino Congelado", "Cerdo"],
    index=0,
)

variable = st.sidebar.radio(
    "Variable a visualizar en el mapa",
    options=["Valor (USD M)", "Volumen (t)"],
    index=0,
)

# --- Filtrar datos ---
df_filtrado = df.copy()
if tipo_seleccion != "Total":
    df_filtrado = df_filtrado[df_filtrado["Tipo Carne"] == tipo_seleccion]

# =====================================================
# AGREGACIÓN POR ESTADO
# =====================================================
agg_estado = df_filtrado.groupby("Estado", as_index=False).agg({
    "Valor (USD M)": "sum",
    "Volumen (t)":   "sum",
    "US FOB":        "count",
}).rename(columns={"US FOB": "Embarques"})

agg_estado["estado_geo"] = agg_estado["Estado"].map(nombre_geojson).fillna(agg_estado["Estado"])

# =====================================================
# ✅ KPIs — ARRIBA DE TODO
# =====================================================
k1, k2, k3, k4 = st.columns(4)
k1.metric(
    "🏛️ Estados con exportaciones",
    f"{len(agg_estado):,}",
)
k2.metric(
    "🚛 Embarques Totales",
    f"{agg_estado['Embarques'].sum():,}",
)
k3.metric(
    "📦 Volumen Total",
    f"{agg_estado['Volumen (t)'].sum():,.0f} t",
)
k4.metric(
    "💵 Valor Total",
    f"${agg_estado['Valor (USD M)'].sum():,.1f}M USD",
)

st.divider()

# =====================================================
# MAPA COROPLÉTICO
# =====================================================
st.subheader("Exportaciones por Estado")

if variable == "Valor (USD M)":
    color_label = "Valor (USD M)"
    titulo_var  = "Valor de Exportación (USD Millones)"
    color_scale = "YlOrRd"
else:
    color_label = "Volumen (t)"
    titulo_var  = "Volumen de Exportación (Toneladas)"
    color_scale = "Blues"

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
        "Volumen (t)":   ":,.1f",
        "Embarques":     ":,",
        "estado_geo":    False,
    },
    labels={variable: color_label},
    title=f"{titulo_var} — {tipo_seleccion}",
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

# =====================================================
# TRES GRÁFICAS DE BARRAS — TOP 10
# =====================================================
st.subheader("📊 Top 10 Estados")

# --- Top 10 por Embarques ---
top_emb = agg_estado.nlargest(10, "Embarques").sort_values("Embarques", ascending=True)
fig_emb = px.bar(
    top_emb, x="Embarques", y="Estado", orientation="h",
    color="Embarques", color_continuous_scale="Purples",
    title="🚛 Top 10 por Embarques", text="Embarques",
)
fig_emb.update_traces(texttemplate="%{text:,}", textposition="outside")
fig_emb.update_layout(
    height=400, showlegend=False, coloraxis_showscale=False,
    margin={"r": 80, "t": 50, "l": 10, "b": 10},
    xaxis_title="", yaxis_title="",
)
st.plotly_chart(fig_emb, use_container_width=True)

# --- Top 10 por Valor ---
top_val = agg_estado.nlargest(10, "Valor (USD M)").sort_values("Valor (USD M)", ascending=True)
fig_val = px.bar(
    top_val, x="Valor (USD M)", y="Estado", orientation="h",
    color="Valor (USD M)", color_continuous_scale="YlOrRd",
    title="💵 Top 10 por Valor (USD M)", text="Valor (USD M)",
)
fig_val.update_traces(texttemplate="%{text:,.1f}", textposition="outside")
fig_val.update_layout(
    height=400, showlegend=False, coloraxis_showscale=False,
    margin={"r": 80, "t": 50, "l": 10, "b": 10},
    xaxis_title="", yaxis_title="",
)
st.plotly_chart(fig_val, use_container_width=True)

# --- Top 10 por Volumen ---
top_vol = agg_estado.nlargest(10, "Volumen (t)").sort_values("Volumen (t)", ascending=True)
fig_vol = px.bar(
    top_vol, x="Volumen (t)", y="Estado", orientation="h",
    color="Volumen (t)", color_continuous_scale="Blues",
    title="⚖️ Top 10 por Volumen (t)", text="Volumen (t)",
)
fig_vol.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
fig_vol.update_layout(
    height=400, showlegend=False, coloraxis_showscale=False,
    margin={"r": 80, "t": 50, "l": 10, "b": 10},
    xaxis_title="", yaxis_title="",
)
st.plotly_chart(fig_vol, use_container_width=True)

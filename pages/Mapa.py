import streamlit as st
import pandas as pd
import plotly.express as px
import requests

st.set_page_config(page_title="Mapa Exportaciones de Carne", layout="wide")
st.title("🗺️ Exportaciones de Carne por Estado - México")

# ── Cargar datos ───────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("empresas_exportadoras.csv", encoding="utf-8-sig", low_memory=False)
    df["Producto"] = df["Producto"].str.strip()
    df = df.dropna(subset=["Estado", "Producto"])
    df["US FOB"] = pd.to_numeric(df["US FOB"], errors="coerce").fillna(0)
    df["Volumen (kg)"] = pd.to_numeric(df["Volumen (kg)"], errors="coerce").fillna(0)
    return df

df = load_data()

# ── GeoJSON ────────────────────────────────────────────────────────────────────
@st.cache_data
def load_geojson():
    url = "https://raw.githubusercontent.com/angelnmara/geojson/master/mexicoHigh.json"
    return requests.get(url, timeout=15).json()

geojson = load_geojson()

# ── Extraer nombres exactos del GeoJSON ────────────────────────────────────────
geo_names = {f["properties"]["name"] for f in geojson["features"]}

# ── Mapeo de Estado CSV → nombre exacto GeoJSON ────────────────────────────────
state_name_map = {
    "Aguascalientes": "Aguascalientes",
    "Baja California": "Baja California",
    "Baja California Sur": "Baja California Sur",
    "Campeche": "Campeche",
    "Chiapas": "Chiapas",
    "Chihuahua": "Chihuahua",
    "Ciudad de Mexico": "Ciudad de Mexico",
    "Ciudad de México": "Ciudad de Mexico",
    "Coahuila": "Coahuila de Zaragoza",
    "Coahuila de Zaragoza": "Coahuila de Zaragoza",
    "Colima": "Colima",
    "Durango": "Durango",
    "Estado de Mexico": "México",
    "Estado de México": "México",
    "Guanajuato": "Guanajuato",
    "Guerrero": "Guerrero",
    "Hidalgo": "Hidalgo",
    "Jalisco": "Jalisco",
    "Michoacan": "Michoacán de Ocampo",
    "Michoacán": "Michoacán de Ocampo",
    "Morelos": "Morelos",
    "Nayarit": "Nayarit",
    "Nuevo Leon": "Nuevo León",
    "Nuevo León": "Nuevo León",
    "Oaxaca": "Oaxaca",
    "Puebla": "Puebla",
    "Queretaro": "Querétaro de Arteaga",
    "Querétaro": "Querétaro de Arteaga",
    "Quintana Roo": "Quintana Roo",
    "San Luis Potosi": "San Luis Potosí",
    "San Luis Potosí": "San Luis Potosí",
    "Sinaloa": "Sinaloa",
    "Sonora": "Sonora",
    "Tabasco": "Tabasco",
    "Tamaulipas": "Tamaulipas",
    "Tlaxcala": "Tlaxcala",
    "Veracruz": "Veracruz de Ignacio de la Llave",
    "Yucatan": "Yucatán",
    "Yucatán": "Yucatán",
    "Zacatecas": "Zacatecas",
}

df["Estado_geo"] = df["Estado"].map(state_name_map).fillna(df["Estado"])

# ── DEBUG (solo en desarrollo, quitar en producción) ───────────────────────────
sin_match = set(df["Estado_geo"].unique()) - geo_names
if sin_match:
    st.sidebar.warning(f"⚠️ Estados sin match GeoJSON: {sin_match}")

# ── Sidebar filtros ────────────────────────────────────────────────────────────
st.sidebar.header("Filtros")

product_options = {
    "Total": None,
    "Bovino Fresco/Refrigerado": "Carne Bovino Fresca/Refrigerada",
    "Bovino Congelado": "Carne Bovino Congelado",
    "Cerdo": "Carne Cerdo",
}
selected_product_label = st.sidebar.radio("Tipo de producto", list(product_options.keys()))
selected_product = product_options[selected_product_label]

metric_options = {
    "Volumen total (kg)": "Volumen",
    "Valor total (US FOB $)": "Valor",
}
selected_metric_label = st.sidebar.radio("Métrica", list(metric_options.keys()))
col_metric = metric_options[selected_metric_label]

# ── Filtrar y agrupar ──────────────────────────────────────────────────────────
filtered = df[df["Producto"] == selected_product] if selected_product else df.copy()

grouped = (
    filtered.groupby("Estado_geo", as_index=False)
    .agg(
        Volumen=("Volumen (kg)", "sum"),
        Valor=("US FOB", "sum"),
        Empresas=("Exportador", "nunique"),
        Embarques=("Ordinal", "count"),
    )
)

grouped["Volumen_fmt"] = grouped["Volumen"].apply(lambda x: f"{x:,.0f} kg")
grouped["Valor_fmt"] = grouped["Valor"].apply(lambda x: f"${x:,.2f}")

# ── Mapa ───────────────────────────────────────────────────────────────────────
fig = px.choropleth_map(
    grouped,
    geojson=geojson,
    locations="Estado_geo",
    featureidkey="properties.name",
    color=col_metric,
    color_continuous_scale="YlOrRd",
    map_style="carto-positron",
    zoom=4,
    center={"lat": 24.0, "lon": -102.0},
    opacity=0.75,
    hover_name="Estado_geo",
    hover_data={
        "Estado_geo": False,
        col_metric: False,
        "Volumen_fmt": True,
        "Valor_fmt": True,
        "Empresas": True,
        "Embarques": True,
    },
    labels={
        "Volumen_fmt": "Volumen",
        "Valor_fmt": "Valor (US FOB)",
        "Empresas": "Empresas únicas",
        "Embarques": "# Embarques",
    },
    title=f"{selected_metric_label} — {selected_product_label}",
)
fig.update_layout(
    height=600,
    margin={"r": 0, "t": 40, "l": 0, "b": 0},
    coloraxis_colorbar=dict(title=selected_metric_label, tickformat=",.0f"),
)
st.plotly_chart(fig, use_container_width=True)

# ── Tabla ──────────────────────────────────────────────────────────────────────
st.subheader("📋 Detalle por Estado")
display_df = grouped[["Estado_geo", "Volumen_fmt", "Valor_fmt", "Empresas", "Embarques"]].copy()
display_df.columns = ["Estado", "Volumen (kg)", "Valor (US FOB)", "Empresas únicas", "Embarques"]
display_df = display_df.sort_values(col_metric if col_metric in grouped.columns else "Volumen", ascending=False)
st.dataframe(display_df, use_container_width=True, hide_index=True)

# ── KPIs ───────────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Volumen total (kg)", f"{grouped['Volumen'].sum():,.0f}")
k2.metric("Valor total (US FOB)", f"${grouped['Valor'].sum():,.0f}")
k3.metric("Empresas únicas", f"{filtered['Exportador'].nunique():,}")
k4.metric("Embarques", f"{len(filtered):,}")

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ── Configuración de la página ──────────────────────────────────────────────
st.set_page_config(
    page_title="Exportaciones de Carne México → EE.UU.",
    page_icon="🥩",
    layout="wide"
)

st.title("🥩 Exportaciones de Carne: México → Estados Unidos")
st.markdown("Visualización por estado de origen del exportador")

# ── Carga de datos ───────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("empresas_exportadoras.csv", encoding="utf-8-sig")

    # Convertir fecha (Excel serial number a fecha real)
    df["Fecha"] = pd.to_datetime(df["Fecha"], origin="1899-12-30", unit="D")
    df["Año"] = df["Fecha"].dt.year
    df["Mes"] = df["Fecha"].dt.month

    # Limpiar columna Producto
    df["Producto"] = df["Producto"].str.strip()

    return df

df = load_data()

# ── Sidebar: Filtros ─────────────────────────────────────────────────────────
st.sidebar.header("🔧 Filtros")

# Segmento de carne
productos_disponibles = sorted(df["Producto"].dropna().unique())
opciones_producto = ["Total"] + productos_disponibles

segmento = st.sidebar.radio(
    "Tipo de Carne",
    opciones_producto,
    index=0
)

# Métrica
metrica = st.sidebar.radio(
    "Visualizar por",
    ["FOB (USD)", "Volumen (kg)"],
    index=0
)

# Filtro de año
años = sorted(df["Año"].dropna().unique())
año_sel = st.sidebar.multiselect(
    "Año(s)",
    options=años,
    default=años
)

# ── Filtrar datos ────────────────────────────────────────────────────────────
df_filtered = df[df["Año"].isin(año_sel)].copy()

if segmento != "Total":
    df_filtered = df_filtered[df_filtered["Producto"] == segmento]

col_valor = "US FOB" if metrica == "FOB (USD)" else "Volumen (kg)"
label_valor = "US FOB (USD)" if metrica == "FOB (USD)" else "Volumen (kg)"
formato_hover = "$,.0f" if metrica == "FOB (USD)" else ",.0f"

# ── Agrupar por Estado ───────────────────────────────────────────────────────
df_estado = (
    df_filtered
    .groupby("Estado", as_index=False)[col_valor]
    .sum()
    .rename(columns={col_valor: "valor"})
    .sort_values("valor", ascending=False)
)

# ── Mapa coroplético ─────────────────────────────────────────────────────────

# Códigos ISO 3166-2 de estados mexicanos
estado_iso = {
    "Aguascalientes": "MX-AGU", "Baja California": "MX-BCN",
    "Baja California Sur": "MX-BCS", "Campeche": "MX-CAM",
    "Chiapas": "MX-CHP", "Chihuahua": "MX-CHH",
    "Ciudad de Mexico": "MX-CMX", "Coahuila": "MX-COA",
    "Colima": "MX-COL", "Durango": "MX-DUR",
    "Guanajuato": "MX-GUA", "Guerrero": "MX-GRO",
    "Hidalgo": "MX-HID", "Jalisco": "MX-JAL",
    "Mexico": "MX-MEX", "Michoacan": "MX-MIC",
    "Morelos": "MX-MOR", "Nayarit": "MX-NAY",
    "Nuevo Leon": "MX-NLE", "Oaxaca": "MX-OAX",
    "Puebla": "MX-PUE", "Queretaro": "MX-QUE",
    "Quintana Roo": "MX-ROO", "San Luis Potosi": "MX-SLP",
    "Sinaloa": "MX-SIN", "Sonora": "MX-SON",
    "Tabasco": "MX-TAB", "Tamaulipas": "MX-TAM",
    "Tlaxcala": "MX-TLA", "Veracruz": "MX-VER",
    "Yucatan": "MX-YUC", "Zacatecas": "MX-ZAC",
    # Variantes con acento
    "Michoacán": "MX-MIC", "Querétaro": "MX-QUE",
    "Yucatán": "MX-YUC", "México": "MX-MEX",
    "Nuevo León": "MX-NLE", "San Luis Potosí": "MX-SLP",
}

df_estado["iso"] = df_estado["Estado"].map(estado_iso)

fig_map = px.choropleth(
    df_estado,
    locations="iso",
    color="valor",
    hover_name="Estado",
    hover_data={"valor": True, "iso": False},
    color_continuous_scale="YlOrRd",
    scope="north america",
    labels={"valor": label_valor},
    title=f"{segmento} — {label_valor} por Estado",
    fitbounds="locations",
    basemap_visible=True,
)

fig_map.update_geos(
    showcoastlines=True,
    coastlinecolor="lightgrey",
    showland=True,
    landcolor="whitesmoke",
    showborder=True,
    showcountries=True,
    countrycolor="grey",
    visible=True,
)

fig_map.update_layout(
    margin={"r": 0, "t": 40, "l": 0, "b": 0},
    coloraxis_colorbar=dict(title=label_valor),
    height=550,
)

st.plotly_chart(fig_map, use_container_width=True)

# ── Métricas resumen ─────────────────────────────────────────────────────────
col1, col2, col3 = st.columns(3)
total_val = df_estado["valor"].sum()
top_estado = df_estado.iloc[0]["Estado"] if not df_estado.empty else "N/A"
num_estados = df_estado["Estado"].nunique()

with col1:
    st.metric("Total " + metrica, f"${total_val:,.0f}" if "FOB" in metrica else f"{total_val:,.0f} kg")
with col2:
    st.metric("Estado líder", top_estado)
with col3:
    st.metric("Estados activos", num_estados)

# ── Tabla de datos por estado ────────────────────────────────────────────────
st.subheader("📊 Detalle por Estado")

df_tabla = df_estado.drop(columns=["iso"]).copy()
df_tabla.columns = ["Estado", label_valor]
df_tabla = df_tabla.sort_values(label_valor, ascending=False).reset_index(drop=True)
df_tabla.index += 1

st.dataframe(
    df_tabla.style.format({label_valor: "${:,.0f}" if "FOB" in metrica else "{:,.0f}"}),
    use_container_width=True,
    height=400
)

# ── Bar chart complementario ─────────────────────────────────────────────────
st.subheader("📈 Top 15 Estados Exportadores")

top15 = df_tabla.head(15)
fig_bar = px.bar(
    top15,
    x="Estado",
    y=label_valor,
    color=label_valor,
    color_continuous_scale="YlOrRd",
    text_auto=".2s",
    title=f"Top 15 Estados — {segmento} | {label_valor}"
)
fig_bar.update_layout(
    xaxis_tickangle=-35,
    showlegend=False,
    height=450,
    coloraxis_showscale=False
)
st.plotly_chart(fig_bar, use_container_width=True)

# ── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(f"Fuente: Base de datos de exportaciones de carne México → EE.UU. | Actualizado: {datetime.today().strftime('%d/%m/%Y')}")

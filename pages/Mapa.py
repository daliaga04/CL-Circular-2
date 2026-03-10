import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# ── PASO 1: Config página ────────────────────────────────────────────────────
st.set_page_config(page_title="Exportaciones de Carne", page_icon="🥩", layout="wide")
st.title("🥩 Exportaciones de Carne: México → Estados Unidos")

# ── PASO 2: Carga de datos ───────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("empresas_exportadoras.csv", encoding="utf-8-sig")
    df["Fecha"] = pd.to_datetime(df["Fecha"], origin="1899-12-30", unit="D")
    df["Producto"] = df["Producto"].str.strip()
    return df

df = load_data()

# ── PASO 3: Sidebar ──────────────────────────────────────────────────────────
st.sidebar.header("🔧 Filtros")
productos_disponibles = sorted(df["Producto"].dropna().unique())
segmento = st.sidebar.radio("Tipo de Carne", ["Total"] + productos_disponibles, index=0)
metrica = st.sidebar.radio("Visualizar por", ["FOB (USD)", "Volumen (kg)"], index=0)

# ── PASO 4: Filtrar ──────────────────────────────────────────────────────────
df_filtered = df.copy()
if segmento != "Total":
    df_filtered = df_filtered[df_filtered["Producto"] == segmento]

col_valor = "US FOB" if metrica == "FOB (USD)" else "Volumen (kg)"
label_valor = "US FOB (USD)" if metrica == "FOB (USD)" else "Volumen (kg)"

# ── PASO 5: Agrupar por Estado ───────────────────────────────────────────────
df_estado = (
    df_filtered
    .groupby("Estado", as_index=False)[col_valor]
    .sum()
    .rename(columns={col_valor: "valor"})
    .sort_values("valor", ascending=False)
)

# ── PASO 6: ISO mapping ──────────────────────────────────────────────────────
estado_iso = {
    "Aguascalientes": "MX-AGU", "Baja California": "MX-BCN",
    "Baja California Sur": "MX-BCS", "Campeche": "MX-CAM",
    "Chiapas": "MX-CHP", "Chihuahua": "MX-CHH",
    "Ciudad de Mexico": "MX-CMX", "Ciudad de México": "MX-CMX",
    "Coahuila": "MX-COA", "Coahuila de Zaragoza": "MX-COA",
    "Colima": "MX-COL", "Durango": "MX-DUR",
    "Guanajuato": "MX-GUA", "Guerrero": "MX-GRO",
    "Hidalgo": "MX-HID", "Jalisco": "MX-JAL",
    "Mexico": "MX-MEX", "México": "MX-MEX",
    "Michoacan": "MX-MIC", "Michoacán": "MX-MIC",
    "Morelos": "MX-MOR", "Nayarit": "MX-NAY",
    "Nuevo Leon": "MX-NLE", "Nuevo León": "MX-NLE",
    "Oaxaca": "MX-OAX", "Puebla": "MX-PUE",
    "Queretaro": "MX-QUE", "Querétaro": "MX-QUE",
    "Quintana Roo": "MX-ROO", "San Luis Potosi": "MX-SLP",
    "San Luis Potosí": "MX-SLP", "Sinaloa": "MX-SIN",
    "Sonora": "MX-SON", "Tabasco": "MX-TAB",
    "Tamaulipas": "MX-TAM", "Tlaxcala": "MX-TLA",
    "Veracruz": "MX-VER", "Veracruz de Ignacio de la Llave": "MX-VER",
    "Yucatan": "MX-YUC", "Yucatán": "MX-YUC",
    "Zacatecas": "MX-ZAC",
}

df_estado["iso"] = df_estado["Estado"].map(estado_iso)
df_mapa = df_estado.dropna(subset=["iso"])  # ← importante: solo filas con ISO válido

# ── PASO 7: Mapa ─────────────────────────────────────────────────────────────
fig_map = go.Figure(go.Choropleth(      # ← df_mapa ya existe aquí ✅
    locations=df_mapa["iso"],
    z=df_mapa["valor"],
    text=df_mapa["Estado"],
    colorscale="YlOrRd",
    colorbar_title=label_valor,
    hovertemplate="<b>%{text}</b><br>" + label_valor + ": %{z:,.0f}<extra></extra>",
    marker_line_color="white",
    marker_line_width=0.5,
))

fig_map.update_layout(
    title_text=f"{segmento} — {label_valor} por Estado",
    margin=dict(r=0, t=40, l=0, b=0),
    height=560,
    geo=dict(
        scope="north america",
        showcoastlines=True,
        coastlinecolor="lightgrey",
        showland=True,
        landcolor="whitesmoke",
        showborder=True,
        showcountries=True,
        countrycolor="grey",
        showframe=False,
        lataxis_range=[14, 33],
        lonaxis_range=[-118, -86],
    )
)

st.plotly_chart(fig_map, use_container_width=True)

# ── PASO 8: KPIs ─────────────────────────────────────────────────────────────
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

# ── PASO 9: Tabla ─────────────────────────────────────────────────────────────
st.subheader("📊 Detalle por Estado")
df_tabla = df_estado.drop(columns=["iso"]).copy()
df_tabla.columns = ["Estado", label_valor]
df_tabla = df_tabla.reset_index(drop=True)
df_tabla.index += 1

st.dataframe(
    df_tabla.style.format({label_valor: "${:,.0f}" if "FOB" in metrica else "{:,.0f}"}),
    use_container_width=True,
    height=400
)

# ── PASO 10: Bar chart ────────────────────────────────────────────────────────
st.subheader("📈 Top 15 Estados Exportadores")
top15 = df_tabla.head(15)
fig_bar = px.bar(
    top15, x="Estado", y=label_valor,
    color=label_valor, color_continuous_scale="YlOrRd",
    text_auto=".2s",
    title=f"Top 15 — {segmento} | {label_valor}"
)
fig_bar.update_layout(xaxis_tickangle=-35, showlegend=False, height=450, coloraxis_showscale=False)
st.plotly_chart(fig_bar, use_container_width=True)

st.markdown("---")
st.caption(f"Fuente: Base de datos exportaciones carne México → EE.UU. | {datetime.today().strftime('%d/%m/%Y')}")

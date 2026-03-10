import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import json
from datetime import datetime, timedelta

st.set_page_config(page_title="Mapa de Rutas", layout="wide")
st.title("📍 Rutas de Exportación: Origen → Aduana Fronteriza")

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
df["Volumen (t)"] = df["Volumen (kg)"] / 1_000

# --- Coordenadas de ciudades ---
city_coords = {
    "Culiacan": (24.7994, -107.3940),
    "TIJUANA": (32.5149, -117.0382),
    "Tijuana": (32.5149, -117.0382),
    "Hermosillo": (29.0729, -110.9559),
    "Navojoa": (27.0700, -109.4430),
    "Mexicali": (32.6246, -115.4523),
    "MEXICALI": (32.6246, -115.4523),
    "MEXICO": (19.4326, -99.1332),
    "Tampico": (22.2331, -97.8613),
    "Chihuahua": (28.6353, -106.0889),
    "CHIHUAHUA": (28.6353, -106.0889),
    "BOCA DEL RIO, VERACRUZ": (19.1057, -96.1087),
    "Yanga": (18.8303, -96.7978),
    "Merida": (20.9674, -89.5926),
    "COMPLEJO INDUSTRIALCHIHUAHUA": (28.6353, -106.0889),
    "TLALNEPANTLA": (19.5370, -99.1949),
    "AGUASCALIENTES": (21.8818, -102.2916),
    "Apodaca": (25.7817, -100.1885),
    "Nuevo Laredo": (27.4761, -99.5066),
    "NUEVO LAREDO": (27.4761, -99.5066),
    "Cajeme": (27.4896, -109.9414),
    "Navolato": (24.7676, -107.7023),
    "Torreon": (25.5428, -103.4068),
    "Morelia": (19.7060, -101.1950),
    "Allende": (25.2869, -100.0171),
    "Guasave": (25.5694, -108.4671),
    "Tamuin": (22.0005, -98.7724),
    "La Antigua": (19.3270, -96.3144),
    "Satevo": (28.0068, -106.0835),
    "Cuauhtemoc": (28.4057, -106.8652),
    "Juarez": (31.6904, -106.4245),
    "Ciudad Juarez": (31.6904, -106.4245),
    "CUAUTITLAN IZCALLI": (19.6476, -99.2537),
    "VISTA HERMOSA,MONTERREY": (25.6866, -100.3161),
    "MONTERREY": (25.6866, -100.3161),
    "GUADALUPE": (25.6771, -100.2601),
    "COL. CENTRO, GUADALUPENUEVO LEON": (25.6771, -100.2601),
    "COL. ZONA IND. BENITO JUAREZ  QUERETARO": (20.5888, -100.3899),
    "TOLUCAESTADO DE MEXICO": (19.2826, -99.6557),
    "JEREZ": (22.6498, -103.0009),
    "Jesus Maria": (21.9614, -102.3443),
    "Reynosa": (26.0920, -98.2783),
    "Puebla": (19.0414, -98.2063),
    "Penjamo": (20.4316, -101.7262),
    "San Juan de los Lagos": (21.2466, -102.3316),
    "ACATLAN DE JUAREZ": (20.4200, -103.5900),
    "Nogales": (31.3120, -110.9466),
    "Puerto Morelos": (20.8464, -86.8742),
    "No disponible": (23.6345, -102.5528),
}

aduana_coords = {
    "NUEVO LAREDO": (27.4761, -99.5066),
    "TIJUANA": (32.5149, -117.0382),
    "MEXICALI": (32.6246, -115.4523),
    "PUENTE INT. ZARAGOZA-ISLETA": (31.7458, -106.4472),
    "NOGALES": (31.3120, -110.9466),
    "COLOMBIA": (27.6678, -99.7584),
    "CIUDAD REYNOSA": (26.0920, -98.2783),
    "CIUDAD JUAREZ": (31.6904, -106.4245),
    "GUADALUPE-TORNILLO": (31.4425, -106.1500),
    "AEROP. ABRAHAM GONZALEZ": (28.7028, -105.9642),
    "PROGRESO": (21.2817, -89.6625),
    "PUERTO MORELOS": (20.8464, -86.8742),
    "SALINAS VICTORIA A (TER. FERROVIARIA)": (25.9581, -100.3007),
    "ENSENADA": (31.8667, -116.5964),
}

# =====================================================
# SIDEBAR — FILTROS
# =====================================================
st.sidebar.header("⚙️ Filtros")

tipo_seleccion = st.sidebar.radio(
    "Tipo de carne",
    options=["Total", "Bovino Fresco/Refrigerado", "Bovino Congelado", "Cerdo"],
    index=0,
)

mostrar_locales = st.sidebar.checkbox(
    "Incluir rutas locales (distancia = 0 km)",
    value=False,
)

usar_rutas_reales = st.sidebar.checkbox(
    "🛣️ Usar rutas reales de carretera (OSRM)",
    value=False,
    help="Activa para trazar rutas por carretera. Requiere conexión a internet y tarda unos segundos.",
)

# --- Filtrar datos ---
df_filtrado = df.copy()
if tipo_seleccion != "Total":
    df_filtrado = df_filtrado[df_filtrado["Tipo Carne"] == tipo_seleccion]

# =====================================================
# AGREGACIÓN DE RUTAS
# =====================================================
rutas_agg = df_filtrado.dropna(subset=["Ruta"]).groupby(
    ["Localidad", "Aduana", "Ruta", "Distancia Frontera", "Indice Seguridad"],
    as_index=False
).agg({
    "Valor (USD M)": "sum",
    "Volumen (t)": "sum",
    "US FOB": "count",
}).rename(columns={"US FOB": "Embarques"})

if not mostrar_locales:
    rutas_agg = rutas_agg[rutas_agg["Distancia Frontera"] > 0]

rutas_agg["lat_orig"] = rutas_agg["Localidad"].map(lambda x: city_coords.get(x, (None, None))[0])
rutas_agg["lon_orig"] = rutas_agg["Localidad"].map(lambda x: city_coords.get(x, (None, None))[1])
rutas_agg["lat_dest"] = rutas_agg["Aduana"].map(lambda x: aduana_coords.get(x, (None, None))[0])
rutas_agg["lon_dest"] = rutas_agg["Aduana"].map(lambda x: aduana_coords.get(x, (None, None))[1])

rutas_plot = rutas_agg.dropna(subset=["lat_orig", "lon_orig", "lat_dest", "lon_dest"]).copy()

st.sidebar.markdown(f"**Rutas a graficar:** {len(rutas_plot)}")

# =====================================================
# OSRM — RUTAS REALES (solo si el usuario lo activa)
# =====================================================
def get_road_route(orig_lat, orig_lon, dest_lat, dest_lon):
    url = (
        f"http://router.project-osrm.org/route/v1/driving/"
        f"{orig_lon},{orig_lat};{dest_lon},{dest_lat}"
        f"?overview=full&geometries=polyline"
    )
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data.get("code") == "Ok":
            import polyline as pl
            coords = pl.decode(data["routes"][0]["geometry"])
            return coords
    except Exception:
        pass
    return [(orig_lat, orig_lon), (dest_lat, dest_lon)]

route_cache = {}
if usar_rutas_reales:
    pares_unicos = rutas_plot[["Localidad", "Aduana", "lat_orig", "lon_orig", "lat_dest", "lon_dest"]]\
        .drop_duplicates(subset=["Localidad", "Aduana"])
    progress = st.progress(0, text="Calculando rutas reales...")
    total = len(pares_unicos)
    for i, (_, par) in enumerate(pares_unicos.iterrows()):
        key = (par["Localidad"], par["Aduana"])
        route_cache[key] = get_road_route(
            par["lat_orig"], par["lon_orig"],
            par["lat_dest"], par["lon_dest"]
        )
        progress.progress((i + 1) / total, text=f"Ruta {i+1}/{total}: {par['Localidad']} → {par['Aduana']}")
    progress.empty()

# =====================================================
# CONSTRUIR MAPA
# =====================================================
def seguridad_color(idx):
    if idx <= 3:   return "green"
    elif idx <= 5: return "gold"
    elif idx <= 7: return "orange"
    else:          return "red"

fig_rutas = go.Figure()

for _, row in rutas_plot.iterrows():
    key = (row["Localidad"], row["Aduana"])
    if usar_rutas_reales and key in route_cache:
        coords = route_cache[key]
        lats = [c[0] for c in coords]
        lons = [c[1] for c in coords]
    else:
        lats = [row["lat_orig"], row["lat_dest"]]
        lons = [row["lon_orig"], row["lon_dest"]]

    color = seguridad_color(row["Indice Seguridad"])
    ancho = max(1, row["Embarques"] / rutas_plot["Embarques"].max() * 6)

    fig_rutas.add_trace(go.Scattergeo(
        lon=lons,
        lat=lats,
        mode="lines",
        line=dict(width=ancho, color=color),
        opacity=0.7,
        hoverinfo="text",
        text=(
            f"{row['Localidad']} → {row['Aduana']}<br>"
            f"Ruta: {row['Ruta']}<br>"
            f"Distancia: {row['Distancia Frontera']:,.0f} km<br>"
            f"Embarques: {row['Embarques']:,}<br>"
            f"Valor: ${row['Valor (USD M)']:,.2f}M USD<br>"
            f"Seguridad: {row['Indice Seguridad']:.0f}/10"
        ),
        showlegend=False,
    ))

# Puntos origen
fig_rutas.add_trace(go.Scattergeo(
    lon=rutas_plot["lon_orig"],
    lat=rutas_plot["lat_orig"],
    mode="markers",
    marker=dict(size=6, color="steelblue", symbol="circle"),
    text=rutas_plot["Localidad"],
    name="Origen",
    hoverinfo="text",
))

# Puntos aduana
aduanas_unicas = rutas_plot[["Aduana", "lat_dest", "lon_dest"]].drop_duplicates()
fig_rutas.add_trace(go.Scattergeo(
    lon=aduanas_unicas["lon_dest"],
    lat=aduanas_unicas["lat_dest"],
    mode="markers",
    marker=dict(size=12, color="crimson", symbol="star"),
    text=aduanas_unicas["Aduana"],
    name="Aduana",
    hoverinfo="text",
))

fig_rutas.update_geos(
    scope="north america",
    showland=True,
    landcolor="rgb(243, 243, 243)",
    countrycolor="rgb(204, 204, 204)",
    showlakes=True,
    lakecolor="rgb(200, 220, 255)",
    center=dict(lat=24, lon=-102),
    projection_scale=3.5,
    lonaxis_range=[-120, -85],
    lataxis_range=[14, 34],
)

fig_rutas.update_layout(
    height=700,
    margin={"r": 0, "t": 30, "l": 0, "b": 0},
    legend=dict(x=0.01, y=0.99),
    title=f"Rutas de Exportación — {tipo_seleccion} (color = índice de seguridad)",
)

st.plotly_chart(fig_rutas, use_container_width=True)

st.markdown("""
**Código de colores (Índice de Seguridad):**
🟢 0-3: Seguro  |  🟡 4-5: Moderado  |  🟠 6-7: Riesgo Alto  |  🔴 8-10: Muy Peligroso
""")

# =====================================================
# TABLA
# =====================================================
st.subheader("📋 Detalle de Rutas")
tabla_rutas = rutas_agg[
    ["Localidad", "Aduana", "Ruta", "Distancia Frontera", "Indice Seguridad", "Embarques", "Valor (USD M)", "Volumen (t)"]
].sort_values("Valor (USD M)", ascending=False).reset_index(drop=True)
tabla_rutas.index = tabla_rutas.index + 1
tabla_rutas = tabla_rutas.rename(columns={
    "Distancia Frontera": "Distancia (km)",
    "Indice Seguridad": "Seguridad (0-10)",
})
st.dataframe(tabla_rutas, use_container_width=True)

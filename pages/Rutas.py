import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import json

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
# WAYPOINTS MANUALES POR RUTA (simulan carreteras reales)
# Formato: "Nombre Ruta CSV" -> lista de (lat, lon)
# =====================================================
route_waypoints = {
    # Carr. 57D México - Querétaro - SLP - Matehuala - Monterrey - Nuevo Laredo
    "Carr. 57D México - Querétaro - SLP - Matehuala - Monterrey - Nuevo Laredo": [
        (19.4326, -99.1332),   # CDMX
        (20.5888, -100.3899),  # Querétaro
        (21.8818, -101.6833),  # San Luis Potosí
        (23.6478, -100.6572),  # Matehuala
        (25.6866, -100.3161),  # Monterrey
        (27.4761, -99.5066),   # Nuevo Laredo
    ],
    # Carr. 45 Chihuahua - Cd. Juárez
    "Carr. 45 Chihuahua - Cd. Juárez": [
        (28.6353, -106.0889),  # Chihuahua
        (30.0681, -106.8843),  # Villa Ahumada
        (31.6904, -106.4245),  # Ciudad Juárez
    ],
    # Carr. 15 Hermosillo - Nogales
    "Carr. 15 Hermosillo - Nogales": [
        (29.0729, -110.9559),  # Hermosillo
        (30.3285, -110.9742),  # Santa Ana
        (31.3120, -110.9466),  # Nogales
    ],
    # Carr. 2 Mexicali - Tijuana
    "Carr. 2 Mexicali - Tijuana": [
        (32.6246, -115.4523),  # Mexicali
        (32.5547, -116.4030),  # Tecate
        (32.5149, -117.0382),  # Tijuana
    ],
    # Carr. 15 Culiacán - Nogales
    "Carr. 15 Culiacán - Nogales": [
        (24.7994, -107.3940),  # Culiacán
        (25.5694, -108.4671),  # Guasave
        (27.0700, -109.4430),  # Navojoa
        (29.0729, -110.9559),  # Hermosillo
        (30.3285, -110.9742),  # Santa Ana
        (31.3120, -110.9466),  # Nogales
    ],
    # Carr. 85 Apodaca - Monterrey - Nuevo Laredo
    "Carr. 85 Apodaca - Monterrey - Nuevo Laredo": [
        (25.7817, -100.1885),  # Apodaca
        (25.6866, -100.3161),  # Monterrey
        (26.3538, -99.9947),   # Sabinas Hidalgo
        (27.4761, -99.5066),   # Nuevo Laredo
    ],
    # Carr. 40D Saltillo - Monterrey - Nuevo Laredo
    "Carr. 40D Saltillo - Monterrey - Nuevo Laredo": [
        (25.4260, -101.0030),  # Saltillo
        (25.6866, -100.3161),  # Monterrey
        (27.4761, -99.5066),   # Nuevo Laredo
    ],
    # Carr. 15 Navolato - Nogales
    "Carr. 15 Navolato - Nogales": [
        (24.7676, -107.7023),  # Navolato
        (25.5694, -108.4671),  # Guasave
        (27.0700, -109.4430),  # Navojoa
        (29.0729, -110.9559),  # Hermosillo
        (31.3120, -110.9466),  # Nogales
    ],
    # Carr. 15 Cajeme - Nogales
    "Carr. 15 Cajeme - Nogales": [
        (27.4896, -109.9414),  # Cajeme
        (29.0729, -110.9559),  # Hermosillo
        (30.3285, -110.9742),  # Santa Ana
        (31.3120, -110.9466),  # Nogales
    ],
    # Carr. 45 Satevo - Cd. Juárez
    "Carr. 45 Satevo - Cd. Juárez": [
        (28.0068, -106.0835),  # Satevo
        (28.6353, -106.0889),  # Chihuahua
        (30.0681, -106.8843),  # Villa Ahumada
        (31.6904, -106.4245),  # Ciudad Juárez
    ],
    # Carr. 45 Cuauhtémoc - Cd. Juárez
    "Carr. 45 Cuauhtémoc - Cd. Juárez": [
        (28.4057, -106.8652),  # Cuauhtémoc
        (28.6353, -106.0889),  # Chihuahua
        (30.0681, -106.8843),  # Villa Ahumada
        (31.6904, -106.4245),  # Ciudad Juárez
    ],
    # Carr. 57 SLP - Monterrey - Nuevo Laredo
    "Carr. 57 SLP - Monterrey - Nuevo Laredo": [
        (21.8818, -101.6833),  # San Luis Potosí
        (23.6478, -100.6572),  # Matehuala
        (25.6866, -100.3161),  # Monterrey
        (27.4761, -99.5066),   # Nuevo Laredo
    ],
    # Carr. 180 Mérida - Progreso
    "Carr. 180 Mérida - Progreso": [
        (20.9674, -89.5926),   # Mérida
        (21.2817, -89.6625),   # Progreso
    ],
    # Carr. 307 Puerto Morelos
    "Carr. 307 Puerto Morelos": [
        (21.1619, -86.8515),   # Cancún
        (20.8464, -86.8742),   # Puerto Morelos
    ],
    # Carr. 57D Querétaro - Nuevo Laredo
    "Carr. 57D Querétaro - SLP - Matehuala - Monterrey - Nuevo Laredo": [
        (20.5888, -100.3899),  # Querétaro
        (21.8818, -101.6833),  # San Luis Potosí
        (23.6478, -100.6572),  # Matehuala
        (25.6866, -100.3161),  # Monterrey
        (27.4761, -99.5066),   # Nuevo Laredo
    ],
    # Carr. 15D Guadalajara - Tepic - Culiacán - Nogales
    "Carr. 15D Guadalajara - Tepic - Culiacán - Nogales": [
        (20.6597, -103.3496),  # Guadalajara
        (21.5085, -104.8954),  # Tepic
        (24.7994, -107.3940),  # Culiacán
        (27.0700, -109.4430),  # Navojoa
        (29.0729, -110.9559),  # Hermosillo
        (31.3120, -110.9466),  # Nogales
    ],
}

def get_waypoints(ruta_nombre, lat_orig, lon_orig, lat_dest, lon_dest):
    """Busca waypoints por nombre de ruta; si no existe, usa línea recta."""
    for key, wps in route_waypoints.items():
        if key.lower() in ruta_nombre.lower() or ruta_nombre.lower() in key.lower():
            return wps
    return [(lat_orig, lon_orig), (lat_dest, lon_dest)]

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
# CONSTRUIR MAPA con Scattermapbox (fondo real)
# =====================================================
def seguridad_color(idx):
    if idx <= 3:   return "green"
    elif idx <= 5: return "gold"
    elif idx <= 7: return "orange"
    else:          return "red"

fig_rutas = go.Figure()

for _, row in rutas_plot.iterrows():
    coords = get_waypoints(
        row["Ruta"],
        row["lat_orig"], row["lon_orig"],
        row["lat_dest"], row["lon_dest"],
    )
    lats = [c[0] for c in coords] + [None]
    lons = [c[1] for c in coords] + [None]
    color = seguridad_color(row["Indice Seguridad"])
    ancho = max(2, row["Embarques"] / rutas_plot["Embarques"].max() * 8)

    fig_rutas.add_trace(go.Scattermapbox(
        lon=lons,
        lat=lats,
        mode="lines",
        line=dict(width=ancho, color=color),
        opacity=0.75,
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
fig_rutas.add_trace(go.Scattermapbox(
    lon=rutas_plot["lon_orig"].tolist(),
    lat=rutas_plot["lat_orig"].tolist(),
    mode="markers",
    marker=dict(size=8, color="steelblue"),
    text=rutas_plot["Localidad"].tolist(),
    name="Origen",
    hoverinfo="text",
))

# Puntos aduana
aduanas_unicas = rutas_plot[["Aduana", "lat_dest", "lon_dest"]].drop_duplicates()
fig_rutas.add_trace(go.Scattermapbox(
    lon=aduanas_unicas["lon_dest"].tolist(),
    lat=aduanas_unicas["lat_dest"].tolist(),
    mode="markers",
    marker=dict(size=14, color="crimson", symbol="star"),
    text=aduanas_unicas["Aduana"].tolist(),
    name="Aduana",
    hoverinfo="text",
))

fig_rutas.update_layout(
    mapbox=dict(
        style="carto-positron",
        center=dict(lat=24.5, lon=-103.5),
        zoom=4.5,
    ),
    height=700,
    margin={"r": 0, "t": 40, "l": 0, "b": 0},
    legend=dict(x=0.01, y=0.99, bgcolor="rgba(255,255,255,0.8)"),
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

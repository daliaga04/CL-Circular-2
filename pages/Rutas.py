import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

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

ROUTE_WAYPOINTS = {
    "Carr. 57D México - Querétaro - SLP - Matehuala - Monterrey - Nuevo Laredo": [
        (19.4326, -99.1332), (20.5888, -100.3899), (21.8818, -101.6833),
        (23.6478, -100.6572), (25.6866, -100.3161), (27.4761, -99.5066),
    ],
    "Carr. 57D Querétaro - SLP - Matehuala - Monterrey - Nuevo Laredo": [
        (20.5888, -100.3899), (21.8818, -101.6833), (23.6478, -100.6572),
        (25.6866, -100.3161), (27.4761, -99.5066),
    ],
    "Carr. 57D Cuautitlán Izcalli - Querétaro - SLP - Monterrey - Nuevo Laredo": [
        (19.6476, -99.2537), (20.5888, -100.3899), (21.8818, -101.6833),
        (23.6478, -100.6572), (25.6866, -100.3161), (27.4761, -99.5066),
    ],
    "Carr. 57D Tlalnepantla - Querétaro - SLP - Monterrey - Nuevo Laredo": [
        (19.5370, -99.1949), (20.5888, -100.3899), (21.8818, -101.6833),
        (23.6478, -100.6572), (25.6866, -100.3161), (27.4761, -99.5066),
    ],
    "Carr. 57D Tlalnepantla - Querétaro - SLP - Monterrey - Colombia": [
        (19.5370, -99.1949), (20.5888, -100.3899), (21.8818, -101.6833),
        (23.6478, -100.6572), (25.6866, -100.3161), (27.6678, -99.7584),
    ],
    "Carr. 55 Toluca - México - Carr. 57D Querétaro - SLP - Monterrey - Nuevo Laredo": [
        (19.2826, -99.6557), (19.4326, -99.1332), (20.5888, -100.3899),
        (21.8818, -101.6833), (23.6478, -100.6572), (25.6866, -100.3161), (27.4761, -99.5066),
    ],
    "Carr. 150D Puebla - México - Carr. 57D Querétaro - SLP - Monterrey - Nuevo Laredo": [
        (19.0414, -98.2063), (19.4326, -99.1332), (20.5888, -100.3899),
        (21.8818, -101.6833), (23.6478, -100.6572), (25.6866, -100.3161), (27.4761, -99.5066),
    ],
    "Carr. 150D Puebla - México - Carr. 57D Querétaro - SLP - Monterrey - Colombia": [
        (19.0414, -98.2063), (19.4326, -99.1332), (20.5888, -100.3899),
        (21.8818, -101.6833), (23.6478, -100.6572), (25.6866, -100.3161), (27.6678, -99.7584),
    ],
    "Carr. 150D Puebla - México - Carr. 57D Querétaro - SLP - Cd. Victoria - Reynosa": [
        (19.0414, -98.2063), (19.4326, -99.1332), (20.5888, -100.3899),
        (21.8818, -101.6833), (23.7369, -99.1411), (26.0920, -98.2783),
    ],
    "Carr. 145D Yanga - Puebla - México - Carr. 85D Querétaro - SLP - Monterrey - Nuevo Laredo": [
        (18.8303, -96.7978), (19.0414, -98.2063), (19.4326, -99.1332),
        (20.5888, -100.3899), (21.8818, -101.6833), (23.6478, -100.6572),
        (25.6866, -100.3161), (27.4761, -99.5066),
    ],
    "Carr. 180 Boca del Río - Córdoba - Puebla - México - Carr. 85D Monterrey - Nuevo Laredo": [
        (19.1057, -96.1087), (18.8842, -96.9234), (19.0414, -98.2063),
        (19.4326, -99.1332), (20.5888, -100.3899), (21.8818, -101.6833),
        (25.6866, -100.3161), (27.4761, -99.5066),
    ],
    "Carr. 180 La Antigua - Xalapa - México - Carr. 85D Querétaro - SLP - Monterrey - Nuevo Laredo": [
        (19.3270, -96.3144), (19.5261, -96.9249), (19.4326, -99.1332),
        (20.5888, -100.3899), (21.8818, -101.6833), (25.6866, -100.3161), (27.4761, -99.5066),
    ],
    "Carr. 85 Apodaca - Monterrey - Nuevo Laredo": [
        (25.7817, -100.1885), (25.6866, -100.3161), (26.3538, -99.9947), (27.4761, -99.5066),
    ],
    "Carr. 85 Guadalupe - Monterrey - Nuevo Laredo": [
        (25.6771, -100.2601), (25.6866, -100.3161), (26.3538, -99.9947), (27.4761, -99.5066),
    ],
    "Carr. 85 Monterrey - Nuevo Laredo": [
        (25.6866, -100.3161), (26.3538, -99.9947), (27.4761, -99.5066),
    ],
    "Carr. 85 Guadalupe - Monterrey - Colombia": [
        (25.6771, -100.2601), (25.6866, -100.3161), (26.3538, -99.9947), (27.6678, -99.7584),
    ],
    "Carr. 85 Monterrey - Colombia": [
        (25.6866, -100.3161), (26.3538, -99.9947), (27.6678, -99.7584),
    ],
    "Carr. 45 Chihuahua - Cd. Juárez": [
        (28.6353, -106.0889), (30.0681, -106.8843), (31.6904, -106.4245),
    ],
    "Carr. 45 Chihuahua - Cd. Juárez - Guadalupe-Tornillo": [
        (28.6353, -106.0889), (30.0681, -106.8843), (31.6904, -106.4245), (31.4425, -106.1500),
    ],
    "Satevo - Chihuahua - Carr. 45 Cd. Juárez": [
        (28.0068, -106.0835), (28.6353, -106.0889), (30.0681, -106.8843), (31.6904, -106.4245),
    ],
    "Carr. 45 Chihuahua - Gómez Palacio - Saltillo - Monterrey - Nuevo Laredo": [
        (28.6353, -106.0889), (25.5669, -103.4500), (25.4260, -101.0030),
        (25.6866, -100.3161), (27.4761, -99.5066),
    ],
    "Carr. 45 Chihuahua - Torreón - Saltillo - Monterrey - Colombia": [
        (28.6353, -106.0889), (25.5428, -103.4068), (25.4260, -101.0030),
        (25.6866, -100.3161), (27.6678, -99.7584),
    ],
    "Carr. 16 Chihuahua - Hermosillo - Carr. 15 Nogales": [
        (28.6353, -106.0889), (29.0729, -110.9559), (30.3285, -110.9742), (31.3120, -110.9466),
    ],
    "Carr. 16 Cuauhtémoc - Hermosillo - Caborca - Mexicali": [
        (28.4057, -106.8652), (29.0729, -110.9559), (30.7167, -112.1333), (32.6246, -115.4523),
    ],
    "Carr. a Cd. Juárez (Aeropuerto local)": [
        (28.7028, -105.9642), (31.6904, -106.4245),
    ],
    "Blvd. Juan Pablo II - Puente Zaragoza": [
        (31.7200, -106.4000), (31.7458, -106.4472),
    ],
    "Carr. 15 Hermosillo - Nogales": [
        (29.0729, -110.9559), (30.3285, -110.9742), (31.3120, -110.9466),
    ],
    "Carr. 15 Cajeme - Hermosillo - Nogales": [
        (27.4896, -109.9414), (29.0729, -110.9559), (30.3285, -110.9742), (31.3120, -110.9466),
    ],
    "Carr. 15 Navojoa - Hermosillo - Nogales": [
        (27.0700, -109.4430), (29.0729, -110.9559), (30.3285, -110.9742), (31.3120, -110.9466),
    ],
    "Carr. 15 Guasave - Los Mochis - Navojoa - Hermosillo - Nogales": [
        (25.5694, -108.4671), (25.7908, -108.9957), (27.0700, -109.4430),
        (29.0729, -110.9559), (31.3120, -110.9466),
    ],
    "Carr. 15 Culiacán - Los Mochis - Navojoa - Hermosillo - Nogales": [
        (24.7994, -107.3940), (25.7908, -108.9957), (27.0700, -109.4430),
        (29.0729, -110.9559), (31.3120, -110.9466),
    ],
    "Carr. 15 Navolato - Culiacán - Los Mochis - Hermosillo - Nogales": [
        (24.7676, -107.7023), (24.7994, -107.3940), (25.7908, -108.9957),
        (27.0700, -109.4430), (29.0729, -110.9559), (31.3120, -110.9466),
    ],
    "Carr. 15 Navojoa - Hermosillo - Caborca - Carr. 2 Ensenada": [
        (27.0700, -109.4430), (29.0729, -110.9559), (30.7167, -112.1333),
        (32.0000, -114.8000), (31.8667, -116.5964),
    ],
    "Carr. 15 Culiacán - Hermosillo - Caborca - Sonoyta - Mexicali - Tijuana": [
        (24.7994, -107.3940), (29.0729, -110.9559), (30.7167, -112.1333),
        (31.8635, -113.0241), (32.6246, -115.4523), (32.5149, -117.0382),
    ],
    "Carr. 15 Culiacán - Los Mochis - Guaymas - Caborca - Sonoyta - Mexicali": [
        (24.7994, -107.3940), (25.7908, -108.9957), (27.9214, -110.8989),
        (30.7167, -112.1333), (31.8635, -113.0241), (32.6246, -115.4523),
    ],
    "Carr. 15 Guasave - Culiacán - Carr. 40D Durango - Torreón - Saltillo - Monterrey - Nuevo Laredo": [
        (25.5694, -108.4671), (24.7994, -107.3940), (24.0232, -104.6532),
        (25.5428, -103.4068), (25.4260, -101.0030), (25.6866, -100.3161), (27.4761, -99.5066),
    ],
    "Carr. 40D Culiacán - Durango - Torreón - Saltillo - Monterrey - Nuevo Laredo": [
        (24.7994, -107.3940), (24.0232, -104.6532), (25.5428, -103.4068),
        (25.4260, -101.0030), (25.6866, -100.3161), (27.4761, -99.5066),
    ],
    "Carr. 40D Culiacán - Durango - Torreón - Saltillo - Salinas Victoria": [
        (24.7994, -107.3940), (24.0232, -104.6532), (25.5428, -103.4068),
        (25.4260, -101.0030), (25.6866, -100.3161), (25.9581, -100.3007),
    ],
    "Carr. 40 Torreón - Saltillo - Monterrey - Carr. 85 Nuevo Laredo": [
        (25.5428, -103.4068), (25.4260, -101.0030), (25.6866, -100.3161), (27.4761, -99.5066),
    ],
    "Carr. 2 Mexicali - Carr. 15 - Carr. 40 - Carr. 85 Nuevo Laredo": [
        (32.6246, -115.4523), (29.0729, -110.9559), (25.5428, -103.4068),
        (25.6866, -100.3161), (27.4761, -99.5066),
    ],
    "Carr. 45 Aguascalientes - SLP - Carr. 57 Monterrey - Colombia": [
        (21.8818, -102.2916), (21.8818, -101.6833), (23.6478, -100.6572),
        (25.6866, -100.3161), (27.6678, -99.7584),
    ],
    "Carr. 45 Jesús María - Aguascalientes - SLP - Carr. 57 Monterrey - Colombia": [
        (21.9614, -102.3443), (21.8818, -102.2916), (21.8818, -101.6833),
        (25.6866, -100.3161), (27.6678, -99.7584),
    ],
    "Carr. 45 Pénjamo - Salamanca - SLP - Carr. 57 Monterrey - Nuevo Laredo": [
        (20.4316, -101.7262), (20.5700, -101.1950), (21.8818, -101.6833),
        (25.6866, -100.3161), (27.4761, -99.5066),
    ],
    "Carr. 45 Pénjamo - Salamanca - SLP - Carr. 57 Monterrey - Colombia": [
        (20.4316, -101.7262), (20.5700, -101.1950), (21.8818, -101.6833),
        (25.6866, -100.3161), (27.6678, -99.7584),
    ],
    "Carr. 43 Morelia - Salamanca - Carr. 45 SLP - Carr. 57 Monterrey - Nuevo Laredo": [
        (19.7060, -101.1950), (20.5700, -101.1950), (21.8818, -101.6833),
        (25.6866, -100.3161), (27.4761, -99.5066),
    ],
    "Carr. 54 Jerez - Zacatecas - Carr. 49 SLP - Carr. 57 Monterrey - Nuevo Laredo": [
        (22.6498, -103.0009), (22.7709, -102.5832), (21.8818, -101.6833),
        (25.6866, -100.3161), (27.4761, -99.5066),
    ],
    "Carr. 54D Acatlán - Guadalajara - Carr. 80 Aguascalientes - SLP - Monterrey - Nuevo Laredo": [
        (20.4200, -103.5900), (20.6597, -103.3496), (21.8818, -102.2916),
        (21.8818, -101.6833), (25.6866, -100.3161), (27.4761, -99.5066),
    ],
    "Carr. 80 San Juan de los Lagos - Aguascalientes - SLP - Carr. 57 Monterrey - Nuevo Laredo": [
        (21.2466, -102.3316), (21.8818, -102.2916), (21.8818, -101.6833),
        (25.6866, -100.3161), (27.4761, -99.5066),
    ],
    "Carr. 80 Tampico - Ciudad Victoria - Carr. 85 Nuevo Laredo": [
        (22.2331, -97.8613), (23.7369, -99.1411), (27.4761, -99.5066),
    ],
    "Carr. Tamuín - Ciudad Valles - Carr. 85 Ciudad Victoria - Nuevo Laredo": [
        (22.0005, -98.7724), (21.9973, -99.0161), (23.7369, -99.1411), (27.4761, -99.5066),
    ],
    "Carr. 261 Mérida - Progreso": [
        (20.9674, -89.5926), (21.2817, -89.6625),
    ],
    "Carr. 180 Mérida - Villahermosa - Carr. 186 - Cd. Victoria - Nuevo Laredo": [
        (20.9674, -89.5926), (17.9892, -92.9475), (23.7369, -99.1411), (27.4761, -99.5066),
    ],
    "Carr. 180 Mérida - Villahermosa - Carr. 186 - Monterrey - Colombia": [
        (20.9674, -89.5926), (17.9892, -92.9475), (25.6866, -100.3161), (27.6678, -99.7584),
    ],
    "Allende NL - Monterrey - Saltillo - Torreón - Mazatlán - Culiacán - Mexicali": [
        (25.2869, -100.0171), (25.6866, -100.3161), (25.4260, -101.0030),
        (25.5428, -103.4068), (23.2329, -106.4062), (24.7994, -107.3940), (32.6246, -115.4523),
    ],
    "Local": None,
}

def get_waypoints(ruta_nombre, lat_orig, lon_orig, lat_dest, lon_dest):
    wps = ROUTE_WAYPOINTS.get(ruta_nombre)
    if wps:
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
# AGREGACIÓN — sumar volumen por ruta única
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

# --- Escalar grosor por volumen (1 a 12 px) ---
vol_min = rutas_plot["Volumen (t)"].min()
vol_max = rutas_plot["Volumen (t)"].max()

def escalar_grosor(vol, min_v, max_v, min_px=1, max_px=12):
    if max_v == min_v:
        return (min_px + max_px) / 2
    return min_px + (vol - min_v) / (max_v - min_v) * (max_px - min_px)

st.sidebar.markdown(f"**Rutas a graficar:** {len(rutas_plot)}")

# =====================================================
# CONSTRUIR MAPA — fondo minimalista
# =====================================================
def seguridad_color(idx):
    if idx <= 3:   return "#2ecc71"   # verde
    elif idx <= 5: return "#f1c40f"   # amarillo
    elif idx <= 7: return "#e67e22"   # naranja
    else:          return "#e74c3c"   # rojo

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
    grosor = escalar_grosor(row["Volumen (t)"], vol_min, vol_max)

    fig_rutas.add_trace(go.Scattermapbox(
        lon=lons,
        lat=lats,
        mode="lines",
        line=dict(width=grosor, color=color),
        opacity=0.8,
        hoverinfo="text",
        text=(
            f"<b>{row['Localidad']} → {row['Aduana']}</b><br>"
            f"Volumen: {row['Volumen (t)']:,.1f} t<br>"
            f"Valor: ${row['Valor (USD M)']:,.2f}M USD<br>"
            f"Embarques: {row['Embarques']:,}<br>"
            f"Seguridad: {row['Indice Seguridad']:.0f}/10<br>"
            f"Ruta: {row['Ruta']}"
        ),
        showlegend=False,
    ))

# Puntos origen
fig_rutas.add_trace(go.Scattermapbox(
    lon=rutas_plot["lon_orig"].tolist(),
    lat=rutas_plot["lat_orig"].tolist(),
    mode="markers",
    marker=dict(size=7, color="#2980b9"),
    text=rutas_plot["Localidad"].tolist(),
    name="🔵 Origen",
    hoverinfo="text",
))

# Puntos aduana
aduanas_unicas = rutas_plot[["Aduana", "lat_dest", "lon_dest"]].drop_duplicates()
fig_rutas.add_trace(go.Scattermapbox(
    lon=aduanas_unicas["lon_dest"].tolist(),
    lat=aduanas_unicas["lat_dest"].tolist(),
    mode="markers",
    marker=dict(size=13, color="#c0392b", symbol="star"),
    text=aduanas_unicas["Aduana"].tolist(),
    name="⭐ Aduana",
    hoverinfo="text",
))

fig_rutas.update_layout(
    mapbox=dict(
        style="white-bg",           # fondo blanco limpio, sin ruidos
        layers=[{                   # contorno de países/estados desde Natural Earth
            "below": "traces",
            "sourcetype": "raster",
            "source": [
                "https://basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}.png"
            ],
        }],
        center=dict(lat=24.5, lon=-103.5),
        zoom=4.5,
    ),
    height=680,
    margin={"r": 0, "t": 50, "l": 0, "b": 0},
    legend=dict(
        x=0.01, y=0.99,
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor="#cccccc",
        borderwidth=1,
    ),
    title=dict(
        text=f"Rutas de Exportación — {tipo_seleccion}  |  grosor = volumen  |  color = seguridad",
        font=dict(size=15),
    ),
)

st.plotly_chart(fig_rutas, use_container_width=True)

st.markdown("""
**Color de ruta (Índice de Seguridad):** 
🟢 0-3 Seguro &nbsp;|&nbsp; 🟡 4-5 Moderado &nbsp;|&nbsp; 🟠 6-7 Riesgo Alto &nbsp;|&nbsp; 🔴 8-10 Muy Peligroso  
**Grosor de línea:** proporcional al volumen exportado (t)
""")

# =====================================================
# TABLA
# =====================================================
st.subheader("📋 Detalle de Rutas")
tabla_rutas = rutas_agg[
    ["Localidad", "Aduana", "Ruta", "Distancia Frontera", "Indice Seguridad",
     "Embarques", "Valor (USD M)", "Volumen (t)"]
].sort_values("Volumen (t)", ascending=False).reset_index(drop=True)
tabla_rutas.index = tabla_rutas.index + 1
tabla_rutas = tabla_rutas.rename(columns={
    "Distancia Frontera": "Distancia (km)",
    "Indice Seguridad": "Seguridad (0-10)",
})
st.dataframe(tabla_rutas, use_container_width=True)

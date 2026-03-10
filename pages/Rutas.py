import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import json
import polyline  # pip install polyline
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

# --- Coordenadas ---
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
# OSRM — OBTENER RUTA REAL POR CARRETERA
# =====================================================
@st.cache_data(show_spinner=False)
def get_road_route(orig_lat, orig_lon, dest_lat, dest_lon):
    """Consulta OSRM y devuelve lista de (lat, lon) de la ruta real."""
    url = (
        f"http://router.project-osrm.org/route/v1/driving/"
        f"{orig_lon},{orig_lat};{dest_lon},{dest_lat}"
        f"?overview=full&geometries=polyline"
    )
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
        if data.get("code") == "Ok":
            encoded = data["routes"][0]["geometry"]
            coords = polyline.decode(encoded)  # lista de (lat, lon)
            return coords
    except Exception:
        pass
    # Fallback: línea recta si OSRM falla
    return [(orig_lat, orig_lon), (dest_lat, dest_lon)]

# =====================================================
#

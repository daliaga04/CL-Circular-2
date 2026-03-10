import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import json
from datetime import datetime, timedelta

st.set_page_config(page_title="Mapa de Exportaciones", layout="wide")
st.title("🗺️ Mapa de Exportaciones de Carne por Estado")

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

# --- Crear columna Tipo Carne simplificado ---
tipo_map = {
    "Carne Bovino Fresca/Refrigerada": "Bovino",
    "Carne Bovino Congelado": "Bovino",
    "Carne Cerdo": "Cerdo",
}
df["Tipo Carne"] = df["Producto"].map(tipo_map).fillna("Otro")

# --- Convertir unidades ---
df["Valor (USD M)"] = df["US FOB"] / 1_000_000
df["Volumen (t)"] = df["Volumen (kg)"] / 1_000

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

# --- Cargar GeoJSON de México ---
@st.cache_data
def cargar_geojson():
    url = "https://raw.githubusercontent.com/angelnmara/geojson/master/mexicoHigh.json"
    response = requests.get(url)
    return json.loads(response.text)

mx_geo = cargar_geojson()

# --- Coordenadas de ciudades (para mapa de rutas) ---
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
# SIDEBAR - FILTROS GLOBALES
# =====================================================
st.sidebar.header("⚙️ Filtros Globales")

tipo_seleccion = st.sidebar.radio(
    "Tipo de carne",
    options=["Total", "Bovino", "Cerdo"],
    index=0,
)

meses_disponibles = sorted(df["Mes"].dropna().unique())
rango_meses = st.sidebar.select_slider(
    "Rango de meses",
    options=meses_disponibles,
    value=(meses_disponibles[0], meses_disponibles[-1]),
)

# Filtrar datos globalmente
df_filtrado = df[
    (df["Mes"] >= rango_meses[0]) & (df["Mes"] <= rango_meses[1])
].copy()

if tipo_seleccion != "Total":
    df_filtrado = df_filtrado[df_filtrado["Tipo Carne"] == tipo_seleccion]

# =====================================================
# TABS
# =====================================================
tab1, tab2, tab3, tab4 = st.tabs([
    "🗺️ Mapa Coroplético",
    "📍 Mapa de Rutas",
    "📊 Análisis por Aduana",
    "🔒 Índice de Seguridad",
])

# =====================================================
# TAB 1: MAPA COROPLÉTICO POR ESTADO
# =====================================================
with tab1:
    st.subheader("Exportaciones por Estado")

    variable = st.radio(
        "Variable a visualizar",
        options=["Valor (USD M)", "Volumen (t)"],
        index=0,
        horizontal=True,
        key="var_mapa",
    )

    # Agregar por estado
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

    # Tabla resumen
    st.markdown("#### Detalle por Estado")
    tabla = agg_estado[["Estado", "Embarques", "Valor (USD M)", "Volumen (t)"]]\
        .sort_values(by=variable, ascending=False)\
        .reset_index(drop=True)
    tabla.index = tabla.index + 1
    tabla["Valor (USD M)"] = tabla["Valor (USD M)"].map("{:,.2f}".format)
    tabla["Volumen (t)"] = tabla["Volumen (t)"].map("{:,.1f}".format)
    tabla["Embarques"] = tabla["Embarques"].map("{:,}".format)
    st.dataframe(tabla, use_container_width=True)

# =====================================================
# TAB 2: MAPA DE RUTAS (ORIGEN → ADUANA)
# =====================================================
with tab2:
    st.subheader("Rutas de Exportación: Origen → Aduana Fronteriza")

    # Agregar por ruta
    rutas_agg = df_filtrado.dropna(subset=["Ruta"]).groupby(
        ["Localidad", "Aduana", "Ruta", "Distancia Frontera", "Indice Seguridad"],
        as_index=False
    ).agg({
        "Valor (USD M)": "sum",
        "Volumen (t)": "sum",
        "US FOB": "count",
    }).rename(columns={"US FOB": "Embarques"})

    # Filtrar rutas locales opcionalmente
    mostrar_locales = st.checkbox("Incluir rutas locales (distancia = 0 km)", value=False)
    if not mostrar_locales:
        rutas_agg = rutas_agg[rutas_agg["Distancia Frontera"] > 0]

    # Asignar coordenadas
    rutas_agg["lat_orig"] = rutas_agg["Localidad"].map(lambda x: city_coords.get(x, (None, None))[0])
    rutas_agg["lon_orig"] = rutas_agg["Localidad"].map(lambda x: city_coords.get(x, (None, None))[1])
    rutas_agg["lat_dest"] = rutas_agg["Aduana"].map(lambda x: aduana_coords.get(x, (None, None))[0])
    rutas_agg["lon_dest"] = rutas_agg["Aduana"].map(lambda x: aduana_coords.get(x, (None, None))[1])

    rutas_plot = rutas_agg.dropna(subset=["lat_orig", "lon_orig", "lat_dest", "lon_dest"])

    # Colorear por índice de seguridad
    def seguridad_color(idx):
        if idx <= 3:
            return "green"
        elif idx <= 5:
            return "gold"
        elif idx <= 7:
            return "orange"
        else:
            return "red"

    fig_rutas = go.Figure()

    for _, row in rutas_plot.iterrows():
        color = seguridad_color(row["Indice Seguridad"])
        fig_rutas.add_trace(go.Scattergeo(
            lon=[row["lon_orig"], row["lon_dest"]],
            lat=[row["lat_orig"], row["lat_dest"]],
            mode="lines",
            line=dict(width=max(1, row["Embarques"] / rutas_plot["Embarques"].max() * 6), color=color),
            opacity=0.7,
            hoverinfo="text",
            text=f"{row['Localidad']} → {row['Aduana']}<br>"
                 f"Ruta: {row['Ruta']}<br>"
                 f"Distancia: {row['Distancia Frontera']:,.0f} km<br>"
                 f"Embarques: {row['Embarques']:,}<br>"
                 f"Valor: ${row['Valor (USD M)']:,.2f}M USD<br>"
                 f"Seguridad: {row['Indice Seguridad']:.0f}/10",
            showlegend=False,
        ))

    # Puntos de origen
    fig_rutas.add_trace(go.Scattergeo(
        lon=rutas_plot["lon_orig"],
        lat=rutas_plot["lat_orig"],
        mode="markers",
        marker=dict(size=5, color="steelblue", symbol="circle"),
        text=rutas_plot["Localidad"],
        name="Origen",
        hoverinfo="text",
    ))

    # Puntos de aduana
    aduanas_unicas = rutas_plot[["Aduana", "lat_dest", "lon_dest"]].drop_duplicates()
    fig_rutas.add_trace(go.Scattergeo(
        lon=aduanas_unicas["lon_dest"],
        lat=aduanas_unicas["lat_dest"],
        mode="markers",
        marker=dict(size=10, color="crimson", symbol="star"),
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
        title="Rutas de Exportación (color = índice de seguridad)",
    )

    st.plotly_chart(fig_rutas, use_container_width=True)

    # Leyenda de colores
    st.markdown("""
    **Código de colores (Índice de Seguridad):**
    🟢 0-3: Seguro  |  🟡 4-5: Moderado  |  🟠 6-7: Riesgo Alto  |  🔴 8-10: Muy Peligroso
    """)

    # Tabla de rutas
    st.markdown("#### Detalle de Rutas")
    tabla_rutas = rutas_agg[["Localidad", "Aduana", "Ruta", "Distancia Frontera", "Indice Seguridad", "Embarques", "Valor (USD M)", "Volumen (t)"]]\
        .sort_values("Valor (USD M)", ascending=False)\
        .reset_index(drop=True)
    tabla_rutas.index = tabla_rutas.index + 1
    tabla_rutas = tabla_rutas.rename(columns={
        "Distancia Frontera": "Distancia (km)",
        "Indice Seguridad": "Seguridad (0-10)",
    })
    st.dataframe(tabla_rutas, use_container_width=True)

# =====================================================
# TAB 3: ANÁLISIS POR ADUANA
# =====================================================
with tab3:
    st.subheader("Volumen y Valor por Aduana Fronteriza")

    agg_aduana = df_filtrado.groupby("Aduana", as_index=False).agg({
        "Valor (USD M)": "sum",
        "Volumen (t)": "sum",
        "US FOB": "count",
    }).rename(columns={"US FOB": "Embarques"}).sort_values("Valor (USD M)", ascending=False)

    col1, col2 = st.columns(2)

    with col1:
        fig_bar_val = px.bar(
            agg_aduana,
            x="Aduana",
            y="Valor (USD M)",
            color="Valor (USD M)",
            color_continuous_scale="YlOrRd",
            title="Valor de Exportación por Aduana (USD M)",
        )
        fig_bar_val.update_layout(showlegend=False, xaxis_tickangle=-45, height=450)
        st.plotly_chart(fig_bar_val, use_container_width=True)

    with col2:
        fig_bar_vol = px.bar(
            agg_aduana,
            x="Aduana",
            y="Volumen (t)",
            color="Volumen (t)",
            color_continuous_scale="Blues",
            title="Volumen de Exportación por Aduana (t)",
        )
        fig_bar_vol.update_layout(showlegend=False, xaxis_tickangle=-45, height=450)
        st.plotly_chart(fig_bar_vol, use_container_width=True)

    # Evolución mensual por aduana (top 5)
    st.markdown("#### Evolución Mensual (Top 5 Aduanas)")
    top5_aduanas = agg_aduana.head(5)["Aduana"].tolist()
    df_top5 = df_filtrado[df_filtrado["Aduana"].isin(top5_aduanas)]
    evol = df_top5.groupby(["Mes", "Aduana"], as_index=False).agg({"Valor (USD M)": "sum"})

    fig_line = px.line(
        evol,
        x="Mes",
        y="Valor (USD M)",
        color="Aduana",
        title="Evolución Mensual del Valor Exportado (Top 5 Aduanas)",
        markers=True,
    )
    fig_line.update_layout(height=450, xaxis_tickangle=-45)
    st.plotly_chart(fig_line, use_container_width=True)

# =====================================================
# TAB 4: ÍNDICE DE SEGURIDAD
# =====================================================
with tab4:
    st.subheader("🔒 Análisis de Seguridad por Ruta")

    # Agregar por ruta con seguridad
    seg_agg = df_filtrado.dropna(subset=["Ruta", "Indice Seguridad"]).groupby(
        ["Localidad", "Aduana", "Ruta", "Distancia Frontera", "Indice Seguridad"],
        as_index=False
    ).agg({
        "Valor (USD M)": "sum",
        "Volumen (t)": "sum",
        "US FOB": "count",
    }).rename(columns={"US FOB": "Embarques"})

    # Scatter: distancia vs seguridad, tamaño = valor
    fig_scatter = px.scatter(
        seg_agg,
        x="Distancia Frontera",
        y="Indice Seguridad",
        size="Valor (USD M)",
        color="Indice Seguridad",
        color_continuous_scale=["green", "gold", "orange", "red"],
        hover_name="Ruta",
        hover_data={
            "Localidad": True,
            "Aduana": True,
            "Embarques": ":,",
            "Valor (USD M)": ":,.2f",
            "Distancia Frontera": ":,.0f",
        },
        title="Distancia vs Índice de Seguridad (tamaño = valor exportado)",
        labels={
            "Distancia Frontera": "Distancia a Frontera (km)",
            "Indice Seguridad": "Índice de Seguridad (0=seguro, 10=peligroso)",
        },
    )
    fig_scatter.update_layout(height=550)
    st.plotly_chart(fig_scatter, use_container_width=True)

    # Rutas más peligrosas
    st.markdown("#### ⚠️ Rutas de Mayor Riesgo")
    peligrosas = seg_agg[seg_agg["Indice Seguridad"] >= 7]\
        .sort_values("Indice Seguridad", ascending=False)\
        .reset_index(drop=True)
    peligrosas.index = peligrosas.index + 1
    if len(peligrosas) > 0:
        st.dataframe(
            peligrosas[["Localidad", "Aduana", "Ruta", "Distancia Frontera", "Indice Seguridad", "Embarques", "Valor (USD M)"]]\
                .rename(columns={"Distancia Frontera": "Distancia (km)", "Indice Seguridad": "Seguridad (0-10)"}),
            use_container_width=True
        )
    else:
        st.info("No hay rutas con índice ≥ 7 en el rango seleccionado.")

    # Rutas más seguras
    st.markdown("#### ✅ Rutas Más Seguras")
    seguras = seg_agg[seg_agg["Indice Seguridad"] <= 3]\
        .sort_values("Indice Seguridad", ascending=True)\
        .reset_index(drop=True)
    seguras.index = seguras.index + 1
    if len(seguras) > 0:
        st.dataframe(
            seguras[["Localidad", "Aduana", "Ruta", "Distancia Frontera", "Indice Seguridad", "Embarques", "Valor (USD M)"]]\
                .rename(columns={"Distancia Frontera": "Distancia (km)", "Indice Seguridad": "Seguridad (0-10)"}),
            use_container_width=True
        )
    else:
        st.info("No hay rutas con índice ≤ 3 en el rango seleccionado.")

    # Valor expuesto a riesgo
    st.markdown("#### 💰 Valor Expuesto a Riesgo")
    seg_agg["Categoria"] = seg_agg["Indice Seguridad"].apply(
        lambda x: "🟢 Seguro (0-3)" if x <= 3
        else ("🟡 Moderado (4-5)" if x <= 5
        else ("🟠 Alto (6-7)" if x <= 7
        else "🔴 Muy Alto (8-10)"))
    )
    risk_summary = seg_agg.groupby("Categoria", as_index=False).agg({
        "Valor (USD M)": "sum",
        "Volumen (t)": "sum",
        "Embarques": "sum",
    }).sort_values("Valor (USD M)", ascending=False)

    fig_pie = px.pie(
        risk_summary,
        values="Valor (USD M)",
        names="Categoria",
        title="Distribución del Valor Exportado por Nivel de Riesgo",
        color="Categoria",
        color_discrete_map={
            "🟢 Seguro (0-3)": "green",
            "🟡 Moderado (4-5)": "gold",
            "🟠 Alto (6-7)": "orange",
            "🔴 Muy Alto (8-10)": "red",
        },
    )
    fig_pie.update_layout(height=450)
    st.plotly_chart(fig_pie, use_container_width=True)

    st.dataframe(risk_summary, use_container_width=True)
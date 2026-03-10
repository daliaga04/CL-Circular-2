# pages/Clustering.py

import os
import streamlit as st
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import plotly.graph_objects as go
import plotly.express as px
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(page_title="Clustering de Empresas", layout="wide")
st.title("🔬 Segmentación de Empresas Exportadoras")

# --- Cargar datos ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(
    os.path.join(BASE_DIR, "..", "empresas_exportadoras.csv"),
    encoding="utf-8-sig"
)
df.columns = df.columns.str.strip()
df = df[~df["Exportador"].str.strip().isin(["NO DETERMINADO", "Sin Nombre"])]

tipo_map = {
    "Carne Bovino Fresca/Refrigerada": "Bovino_Fresco",
    "Carne Bovino Congelado":          "Bovino_Congelado",
    "Carne Cerdo":                     "Cerdo",
}
df["Tipo Carne"] = df["Producto"].str.strip().map(tipo_map).fillna("Otro")

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.header("⚙️ Parámetros del Modelo")
n_clusters = st.sidebar.slider("Número de clusters (k)", min_value=2, max_value=8, value=4)
excluir_micro = st.sidebar.checkbox("Excluir empresas sin embarques (Micro)", value=False)

# =====================================================
# AGREGACIÓN POR EMPRESA
# =====================================================
@st.cache_data
def construir_features(df_raw, excluir_micro_flag):
    agg = df_raw.groupby("Exportador").agg(
        embarques      = ("Ordinal", "count"),
        valor_total    = ("US FOB", "sum"),
        volumen_total  = ("Volumen (kg)", "sum"),
        distancia_prom = ("Distancia Frontera", "mean"),
        riesgo_prom    = ("Indice Seguridad", "mean"),
        aduanas_unicas = ("Aduana", "nunique"),
        estados_unicos = ("Estado", "nunique"),
        n_productos    = ("Tipo Carne", "nunique"),
    ).reset_index()
    agg["precio_prom_kg"] = (agg["valor_total"] / agg["volumen_total"])\
        .replace([np.inf, -np.inf], 0).fillna(0)

    pivot = df_raw.groupby(["Exportador","Tipo Carne"])["US FOB"].sum().unstack(fill_value=0)
    pivot = pivot.div(pivot.sum(axis=1), axis=0)
    for col in ["Bovino_Fresco","Bovino_Congelado","Cerdo"]:
        if col not in pivot.columns:
            pivot[col] = 0
    agg = agg.merge(
        pivot[["Bovino_Fresco","Bovino_Congelado","Cerdo"]].rename(columns={
            "Bovino_Fresco":    "pct_fresco",
            "Bovino_Congelado": "pct_congelado",
            "Cerdo":            "pct_cerdo",
        }), on="Exportador", how="left"
    ).fillna(0)

    if excluir_micro_flag:
        agg = agg[agg["embarques"] > 0]
    return agg

agg = construir_features(df, excluir_micro)

# =====================================================
# MODELO K-MEANS
# =====================================================
features = ["embarques","valor_total","volumen_total","precio_prom_kg",
            "distancia_prom","riesgo_prom","aduanas_unicas","estados_unicos",
            "n_productos","pct_fresco","pct_congelado","pct_cerdo"]

X = agg[features].copy()
for col in ["embarques","valor_total","volumen_total"]:
    X[col] = np.log1p(X[col])

scaler = StandardScaler()
Xs = scaler.fit_transform(X)

km = KMeans(n_clusters=n_clusters, random_state=42, n_init=20)
agg["Cluster"] = km.fit_predict(Xs)

pca = PCA(n_components=2, random_state=42)
coords = pca.fit_transform(Xs)
agg["PC1"] = coords[:, 0]
agg["PC2"] = coords[:, 1]

# Ordenar clusters por valor mediano y asignar etiquetas
orden = agg.groupby("Cluster")["valor_total"].median().sort_values()
nombres_seg = ["Pequeño","Mediano","Grande","Nivel 5","Nivel 6","Nivel 7","Nivel 8","Nivel 9"]
nombre_map  = {c: nombres_seg[i] for i, c in enumerate(orden.index)}
agg["Segmento"] = agg["Cluster"].map(nombre_map)
seg_order = [nombres_seg[i] for i in range(n_clusters)]

COLORS = px.colors.qualitative.Set2[:n_clusters]
cmap   = dict(zip(seg_order, COLORS))

# Perfil por segmento
perfil = agg.groupby("Segmento").agg(
    n_empresas    = ("Exportador", "count"),
    embarques_med = ("embarques", "median"),
    valor_med     = ("valor_total", "median"),
    volumen_med   = ("volumen_total", "median"),
    precio_med    = ("precio_prom_kg", "median"),
    distancia_med = ("distancia_prom", "median"),
    riesgo_med    = ("riesgo_prom", "median"),
    aduanas_med   = ("aduanas_unicas", "median"),
    pct_fresco    = ("pct_fresco", "mean"),
    pct_congelado = ("pct_congelado", "mean"),
    pct_cerdo     = ("pct_cerdo", "mean"),
).reset_index()

# =====================================================
# KPIs
# =====================================================
k1, k2, k3, k4 = st.columns(4)
k1.metric("🏢 Empresas analizadas", f"{len(agg):,}")
k2.metric("🔬 Clusters generados",  f"{n_clusters}")
k3.metric("💵 Valor total",         f"${agg['valor_total'].sum()/1e6:,.1f}M USD")
k4.metric("🚛 Embarques totales",   f"{agg['embarques'].sum():,}")

st.divider()

# =====================================================
# SECCIÓN 1 — PCA SCATTER
# =====================================================
st.subheader("📍 Distribución de Empresas (PCA 2D)")

fig_pca = go.Figure()
for seg in seg_order:
    sub = agg[agg["Segmento"] == seg]
    fig_pca.add_trace(go.Scatter(
        x=sub["PC1"], y=sub["PC2"],
        mode="markers", name=seg,
        marker=dict(size=9, opacity=0.75, color=cmap[seg]),
        customdata=sub[["Exportador","embarques","valor_total","aduanas_unicas"]].values,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Embarques: %{customdata[1]:,}<br>"
            "Valor: $%{customdata[2]:,.0f}<br>"
            "Aduanas: %{customdata[3]}<extra></extra>"
        ),
    ))
fig_pca.update_layout(
    height=500,
    xaxis_title="Componente Principal 1",
    yaxis_title="Componente Principal 2",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    plot_bgcolor="white",
    xaxis=dict(showgrid=True, gridcolor="#eeeeee"),
    yaxis=dict(showgrid=True, gridcolor="#eeeeee"),
)
st.plotly_chart(fig_pca, use_container_width=True)

st.divider()

# =====================================================
# SECCIÓN 2 — BUBBLE: Embarques vs Valor
# =====================================================
st.subheader("💬 Embarques vs Valor (tamaño = volumen)")

vol_max = agg["volumen_total"].replace(0, np.nan).max()
fig_bub = go.Figure()
for seg in seg_order:
    sub = agg[agg["Segmento"] == seg].copy()
    sub["sz"] = (np.sqrt(sub["volumen_total"].clip(lower=0) / vol_max) * 40 + 5).fillna(5)
    fig_bub.add_trace(go.Scatter(
        x=sub["embarques"], y=sub["valor_total"] / 1e6,
        mode="markers", name=seg,
        marker=dict(size=sub["sz"].tolist(), opacity=0.65, color=cmap[seg]),
        customdata=sub[["Exportador","distancia_prom","riesgo_prom"]].values,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Embarques: %{x:,}<br>"
            "Valor: $%{y:.2f}M USD<br>"
            "Dist. media: %{customdata[1]:,.0f} km<br>"
            "Riesgo: %{customdata[2]:.1f}<extra></extra>"
        ),
    ))
fig_bub.update_layout(
    height=500,
    xaxis=dict(title="Embarques", type="log", showgrid=True, gridcolor="#eeeeee"),
    yaxis=dict(title="Valor (USD M)", type="log", showgrid=True, gridcolor="#eeeeee"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    plot_bgcolor="white",
)
st.plotly_chart(fig_bub, use_container_width=True)

st.divider()

# =====================================================
# SECCIÓN 3 — RADAR + BARRAS (lado a lado)
# =====================================================
st.subheader("📊 Perfil por Segmento")

col1, col2 = st.columns(2)

# Radar
with col1:
    radar_vars   = ["embarques_med","valor_med","distancia_med","riesgo_med",
                    "aduanas_med","pct_fresco","pct_congelado","pct_cerdo"]
    radar_labels = ["Embarques","Valor","Distancia","Riesgo",
                    "Aduanas","% Fresco","% Congelado","% Cerdo"]
    pn = perfil.set_index("Segmento")[radar_vars].copy()
    for col_r in radar_vars:
        mn, mx = pn[col_r].min(), pn[col_r].max()
        pn[col_r] = (pn[col_r] - mn) / (mx - mn) if mx > mn else 0

    fig_radar = go.Figure()
    for i, seg in enumerate(seg_order):
        if seg not in pn.index:
            continue
        vals = pn.loc[seg, radar_vars].tolist() + [pn.loc[seg, radar_vars[0]]]
        lbls = radar_labels + [radar_labels[0]]
        fig_radar.add_trace(go.Scatterpolar(
            r=vals, theta=lbls, fill="toself", name=seg,
            line_color=COLORS[i], opacity=0.55,
        ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
        height=450,
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
        title="Perfil normalizado (0-1)",
    )
    st.plotly_chart(fig_radar, use_container_width=True)

# Barras: nº empresas
with col2:
    perf_ord = perfil.set_index("Segmento").reindex(seg_order).reset_index()
    fig_bar = go.Figure(go.Bar(
        x=perf_ord["Segmento"],
        y=perf_ord["n_empresas"],
        marker_color=COLORS,
        text=perf_ord["n_empresas"],
        textposition="outside",
    ))
    fig_bar.update_layout(
        height=450,
        title="Empresas por segmento",
        xaxis_title="Segmento",
        yaxis_title="Nº Empresas",
        showlegend=False,
        plot_bgcolor="white",
        yaxis=dict(showgrid=True, gridcolor="#eeeeee"),
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# =====================================================
# SECCIÓN 4 — TABLA DETALLE
# =====================================================
st.subheader("📋 Resumen por Segmento")
perf_display = perf_ord[["Segmento","n_empresas","embarques_med","valor_med",
                          "distancia_med","riesgo_med","aduanas_med",
                          "pct_fresco","pct_congelado","pct_cerdo"]].copy()
perf_display.columns = ["Segmento","Empresas","Embarques (med)","Valor (med USD)",
                        "Distancia (km)","Riesgo","Aduanas","% Fresco","% Congelado","% Cerdo"]
perf_display["Valor (med USD)"]  = perf_display["Valor (med USD)"].map("${:,.0f}".format)
perf_display["Distancia (km)"]   = perf_display["Distancia (km)"].map("{:,.0f}".format)
perf_display["% Fresco"]         = perf_display["% Fresco"].map("{:.1%}".format)
perf_display["% Congelado"]      = perf_display["% Congelado"].map("{:.1%}".format)
perf_display["% Cerdo"]          = perf_display["% Cerdo"].map("{:.1%}".format)
st.dataframe(perf_display, use_container_width=True, hide_index=True)

st.subheader("🔍 Empresas por Segmento")
seg_filtro = st.selectbox("Ver empresas del segmento:", seg_order)
empresas_seg = agg[agg["Segmento"] == seg_filtro][
    ["Exportador","embarques","valor_total","volumen_total",
     "precio_prom_kg","distancia_prom","riesgo_prom","aduanas_unicas"]
].sort_values("valor_total", ascending=False).reset_index(drop=True)
empresas_seg.index += 1
empresas_seg["valor_total"]   = empresas_seg["valor_total"].map("${:,.0f}".format)
empresas_seg["volumen_total"] = empresas_seg["volumen_total"].map("{:,.0f} kg".format)
empresas_seg["precio_prom_kg"]= empresas_seg["precio_prom_kg"].map("${:,.2f}".format)
st.dataframe(empresas_seg, use_container_width=True)

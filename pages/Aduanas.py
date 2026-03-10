# pages/3_Analisis_Aduana.py

import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Análisis por Aduana", layout="wide")
st.title("📊 Análisis por Aduana Fronteriza")

# --- Cargar datos ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(
    os.path.join(BASE_DIR, "..", "empresas_exportadoras.csv"),
    encoding="utf-8-sig"
)
df.columns = df.columns.str.strip()

# --- Fechas ---
def excel_to_date(serial):
    if pd.isna(serial):
        return None
    return datetime(1899, 12, 30) + timedelta(days=int(serial))

df["Fecha_dt"] = df["Fecha"].apply(excel_to_date)
df["Mes"] = df["Fecha_dt"].dt.to_period("M").astype(str)

# --- Tipo Carne ---
tipo_map = {
    "Carne Bovino Fresca/Refrigerada": "Bovino",
    "Carne Bovino Congelado": "Bovino",
    "Carne Cerdo": "Cerdo",
}
df["Tipo Carne"] = df["Producto"].map(tipo_map).fillna("Otro")
df["Valor (USD M)"] = df["US FOB"] / 1_000_000
df["Volumen (t)"] = df["Volumen (kg)"] / 1_000

# =====================================================
# SIDEBAR — FILTROS
# =====================================================
st.sidebar.header("⚙️ Filtros")

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

aduanas_disponibles = sorted(df["Aduana"].dropna().unique())
aduanas_seleccion = st.sidebar.multiselect(
    "Filtrar aduanas (vacío = todas)",
    options=aduanas_disponibles,
    default=[],
)

# --- Aplicar filtros ---
df_filtrado = df[
    (df["Mes"] >= rango_meses[0]) & (df["Mes"] <= rango_meses[1])
].copy()

if tipo_seleccion != "Total":
    df_filtrado = df_filtrado[df_filtrado["Tipo Carne"] == tipo_seleccion]

if aduanas_seleccion:
    df_filtrado = df_filtrado[df_filtrado["Aduana"].isin(aduanas_seleccion)]

# =====================================================
# KPIs SUPERIORES
# =====================================================
agg_total = df_filtrado.groupby("Aduana", as_index=False).agg({
    "Valor (USD M)": "sum",
    "Volumen (t)": "sum",
    "US FOB": "count",
}).rename(columns={"US FOB": "Embarques"}).sort_values("Valor (USD M)", ascending=False)

k1, k2, k3, k4 = st.columns(4)
k1.metric("🏛️ Aduanas activas",    f"{len(agg_total):,}")
k2.metric("💵 Valor total",         f"${agg_total['Valor (USD M)'].sum():,.1f}M USD")
k3.metric("📦 Volumen total",       f"{agg_total['Volumen (t)'].sum():,.0f} t")
k4.metric("🚛 Embarques totales",   f"{agg_total['Embarques'].sum():,}")

st.divider()

# =====================================================
# SECCIÓN 1 — BARRAS: VALOR Y VOLUMEN POR ADUANA
# =====================================================
st.subheader("📦 Valor y Volumen por Aduana")

col1, col2 = st.columns(2)

with col1:
    df_val = agg_total.sort_values("Valor (USD M)", ascending=True)
    fig_val = go.Figure(go.Bar(
        x=df_val["Valor (USD M)"],
        y=df_val["Aduana"],
        orientation="h",
        marker=dict(
            color=df_val["Valor (USD M)"],
            colorscale="YlOrRd",
            showscale=False,
        ),
        text=df_val["Valor (USD M)"].map("${:,.1f}M".format),
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Valor: $%{x:,.2f}M USD<extra></extra>",
    ))
    fig_val.update_layout(
        title="Valor de Exportación (USD M)",
        height=max(350, len(df_val) * 30),
        margin={"r": 80, "t": 40, "l": 10, "b": 10},
        xaxis=dict(showgrid=True, gridcolor="#eeeeee"),
        plot_bgcolor="white",
    )
    st.plotly_chart(fig_val, use_container_width=True)

with col2:
    df_vol = agg_total.sort_values("Volumen (t)", ascending=True)
    fig_vol = go.Figure(go.Bar(
        x=df_vol["Volumen (t)"],
        y=df_vol["Aduana"],
        orientation="h",
        marker=dict(
            color=df_vol["Volumen (t)"],
            colorscale="Blues",
            showscale=False,
        ),
        text=df_vol["Volumen (t)"].map("{:,.0f} t".format),
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Volumen: %{x:,.1f} t<extra></extra>",
    ))
    fig_vol.update_layout(
        title="Volumen de Exportación (t)",
        height=max(350, len(df_vol) * 30),
        margin={"r": 80, "t": 40, "l": 10, "b": 10},
        xaxis=dict(showgrid=True, gridcolor="#eeeeee"),
        plot_bgcolor="white",
    )
    st.plotly_chart(fig_vol, use_container_width=True)

st.divider()

# =====================================================
# SECCIÓN 2 — PARTICIPACIÓN (PIE)
# =====================================================
st.subheader("🥧 Participación por Aduana")

col3, col4 = st.columns(2)

with col3:
    fig_pie_val = px.pie(
        agg_total,
        values="Valor (USD M)",
        names="Aduana",
        title="Participación en Valor (USD M)",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_pie_val.update_traces(textposition="inside", textinfo="percent+label")
    fig_pie_val.update_layout(height=420, showlegend=True,
                               legend=dict(orientation="v", x=1.0, y=0.5))
    st.plotly_chart(fig_pie_val, use_container_width=True)

with col4:
    fig_pie_emb = px.pie(
        agg_total,
        values="Embarques",
        names="Aduana",
        title="Participación en Embarques",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_pie_emb.update_traces(textposition="inside", textinfo="percent+label")
    fig_pie_emb.update_layout(height=420, showlegend=True,
                               legend=dict(orientation="v", x=1.0, y=0.5))
    st.plotly_chart(fig_pie_emb, use_container_width=True)

st.divider()

# =====================================================
# SECCIÓN 3 — EVOLUCIÓN MENSUAL (TODAS LAS ADUANAS)
# =====================================================
st.subheader("📅 Evolución Mensual por Aduana")

metrica_evol = st.radio(
    "Variable",
    options=["Valor (USD M)", "Volumen (t)", "Embarques"],
    horizontal=True,
    key="metrica_evol",
)

# Agregar por mes y aduana — SIN límite de aduanas
evol = df_filtrado.groupby(["Mes", "Aduana"], as_index=False).agg({
    "Valor (USD M)": "sum",
    "Volumen (t)": "sum",
    "US FOB": "count",
}).rename(columns={"US FOB": "Embarques"})

fig_line = px.line(
    evol,
    x="Mes",
    y=metrica_evol,
    color="Aduana",
    markers=True,
    title=f"Evolución Mensual — {metrica_evol} (todas las aduanas)",
    color_discrete_sequence=px.colors.qualitative.Alphabet,
)
fig_line.update_layout(
    height=520,
    xaxis_tickangle=-45,
    plot_bgcolor="white",
    xaxis=dict(showgrid=True, gridcolor="#eeeeee"),
    yaxis=dict(showgrid=True, gridcolor="#eeeeee"),
    legend=dict(
        orientation="v",
        x=1.01, y=1,
        bgcolor="rgba(255,255,255,0.85)",
        bordercolor="#cccccc",
        borderwidth=1,
    ),
)
st.plotly_chart(fig_line, use_container_width=True)

st.divider()

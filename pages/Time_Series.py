import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller
import pmdarima as pm
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="Time Series", layout="wide")
st.title("📈 Time Series — Pronóstico de Comercio Exterior de Cárnicos")

# ───────────────── CARGA DE DATOS ─────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(
    os.path.join(BASE_DIR, "..", "BD_reto_circular.csv"),
    encoding="utf-8-sig"
)
df.columns = df.columns.str.strip()
df['Fecha'] = pd.to_datetime(df['Fecha'])

# IMPORTANTE: asumimos una columna 'Producto' con valores como:
# 'Bovino fresca/refrigerada', 'Bovino congelado', 'Porcino'
# Si el nombre es otro, ajusta aquí:
# df['Producto'] = df['TU_COLUMNA_DE_PRODUCTO']

# ───────────── FUNCIONES AUXILIARES (IGUALES) ─────────────
@st.cache_data
def test_estacionariedad(serie, nombre):
    resultado = adfuller(serie.dropna(), autolag='AIC')
    return {
        "Serie": nombre,
        "Estadístico ADF": round(resultado[0], 4),
        "p-value": round(resultado[1], 4),
        "Lags usados": resultado[2],
        "Observaciones": resultado[3],
        "¿Estacionaria? (α=0.05)": "Sí" if resultado[1] < 0.05 else "No"
    }

@st.cache_data
def ajustar_sarima(serie_values, serie_index_list):
    serie = pd.Series(serie_values, index=pd.DatetimeIndex(serie_index_list, freq='MS'))

    auto_model = pm.auto_arima(
        serie,
        start_p=0, start_q=0,
        max_p=3, max_q=3,
        d=None,
        start_P=0, start_Q=0,
        max_P=2, max_Q=2,
        D=None,
        m=12,
        seasonal=True,
        test='adf',
        seasonal_test='ocsb',
        trace=False,
        error_action='ignore',
        suppress_warnings=True,
        stepwise=True,
        information_criterion='aic'
    )

    order = auto_model.order
    seasonal_order = auto_model.seasonal_order

    model = SARIMAX(
        serie,
        order=order,
        seasonal_order=seasonal_order,
        enforce_stationarity=False,
        enforce_invertibility=False
    )
    results = model.fit(disp=False)

    return results, order, seasonal_order, auto_model.aic(), auto_model.bic()

@st.cache_data
def generar_forecast(serie_values, serie_index_list, steps=12):
    results, order, seasonal_order, aic, bic = ajustar_sarima(serie_values, serie_index_list)
    forecast_obj = results.get_forecast(steps=steps)
    forecast_mean = forecast_obj.predicted_mean
    conf_int = forecast_obj.conf_int(alpha=0.05)
    return forecast_mean, conf_int, order, seasonal_order, aic, bic, results

def plot_forecast(serie, forecast_mean, conf_int, titulo, color_hist, color_fc):
    scale = 1e6
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=serie.index,
        y=serie.values / scale,
        name='Datos históricos',
        line=dict(color=color_hist, width=2)
    ))

    fig.add_trace(go.Scatter(
        x=forecast_mean.index,
        y=forecast_mean.values / scale,
        name='Pronóstico SARIMA',
        line=dict(color=color_fc, width=2.5, dash='dash')
    ))

    lower = conf_int.iloc[:, 0] / scale
    upper = conf_int.iloc[:, 1] / scale

    fig.add_trace(go.Scatter(
        x=list(forecast_mean.index) + list(forecast_mean.index[::-1]),
        y=list(upper) + list(lower[::-1]),
        fill='toself',
        fillcolor='rgba(99,110,250,0.15)',
        line=dict(color='rgba(0,0,0,0)'),
        name='IC 95%',
        hoverinfo='skip'
    ))

    corte = serie.index[-1]
    y_all = list(serie.values / scale) + list(forecast_mean.values / scale)
    y_max = max(y_all) * 1.05
    y_min = min(y_all) * 0.95

    fig.add_shape(
        type="line",
        x0=corte, x1=corte, y0=y_min, y1=y_max,
        line=dict(color="gray", width=1.5, dash="dot")
    )
    fig.add_annotation(
        x=corte, y=y_max, text="Inicio pronóstico",
        showarrow=False, xanchor="left",
        font=dict(size=11, color="gray")
    )

    fig.update_layout(
        title=dict(text=titulo, font=dict(size=18)),
        xaxis_title="Fecha",
        yaxis_title="USD Millones",
        legend=dict(orientation='h', yanchor='top', y=-0.12,
                    xanchor='center', x=0.5),
        height=500,
        margin=dict(l=50, r=30, t=60, b=60),
        hovermode='x unified'
    )
    return fig

# ───────────── SELECTOR DE PRODUCTO ─────────────
st.markdown("---")
st.subheader("1️⃣ Selecciona el tipo de producto")

productos_disponibles = sorted(df['Producto'].dropna().unique().tolist())
# Esperado algo como:
# ['Bovino fresca/refrigerada', 'Bovino congelado', 'Porcino']

producto_sel = st.radio(
    "Tipo

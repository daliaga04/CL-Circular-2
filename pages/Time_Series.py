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
df["Fecha"] = pd.to_datetime(df["Fecha"])

# IMPORTANTE: ajusta el nombre de la columna de producto si es distinto
# por ejemplo: df["Producto"] = df["DescripcionProducto"]
# Debe tener valores como: 'Bovino fresca/refrigerada', 'Bovino congelado', 'Porcino'

# ───────────── FUNCIONES AUXILIARES ─────────────
@st.cache_data
def test_estacionariedad(serie, nombre):
    resultado = adfuller(serie.dropna(), autolag="AIC")
    return {
        "Serie": nombre,
        "Estadístico ADF": round(resultado[0], 4),
        "p-value": round(resultado[1], 4),
        "Lags usados": resultado[2],
        "Observaciones": resultado[3],
        "¿Estacionaria? (α=0.05)": "Sí" if resultado[1] < 0.05 else "No",
    }

@st.cache_data
def ajustar_sarima(serie_values, serie_index_list):
    serie = pd.Series(serie_values, index=pd.DatetimeIndex(serie_index_list, freq="MS"))
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
        test="adf",
        seasonal_test="ocsb",
        trace=False,
        error_action="ignore",
        suppress_warnings=True,
        stepwise=True,
        information_criterion="aic",
    )
    order = auto_model.order
    seasonal_order = auto_model.seasonal_order

    model = SARIMAX(
        serie,
        order=order,
        seasonal_order=seasonal_order,
        enforce_stationarity=False,
        enforce_invertibility=False,
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
        name="Datos históricos",
        line=dict(color=color_hist, width=2),
    ))

    fig.add_trace(go.Scatter(
        x=forecast_mean.index,
        y=forecast_mean.values / scale,
        name="Pronóstico SARIMA",
        line=dict(color=color_fc, width=2.5, dash="dash"),
    ))

    lower = conf_int.iloc[:, 0] / scale
    upper = conf_int.iloc[:, 1] / scale

    fig.add_trace(go.Scatter(
        x=list(forecast_mean.index) + list(forecast_mean.index[::-1]),
        y=list(upper) + list(lower[::-1]),
        fill="toself",
        fillcolor="rgba(99,110,250,0.15)",
        line=dict(color="rgba(0,0,0,0)"),
        name="IC 95%",
        hoverinfo="skip",
    ))

    corte = serie.index[-1]
    y_all = list(serie.values / scale) + list(forecast_mean.values / scale)
    y_max = max(y_all) * 1.05
    y_min = min(y_all) * 0.95

    fig.add_shape(
        type="line",
        x0=corte, x1=corte, y0=y_min, y1=y_max,
        line=dict(color="gray", width=1.5, dash="dot"),
    )
    fig.add_annotation(
        x=corte, y=y_max, text="Inicio pronóstico",
        showarrow=False, xanchor="left",
        font=dict(size=11, color="gray"),
    )

    fig.update_layout(
        title=dict(text=titulo, font=dict(size=18)),
        xaxis_title="Fecha",
        yaxis_title="USD Millones",
        legend=dict(orientation="h", yanchor="top", y=-0.12,
                    xanchor="center", x=0.5),
        height=500,
        margin=dict(l=50, r=30, t=60, b=60),
        hovermode="x unified",
    )
    return fig

# ───────────── SELECTOR DE PRODUCTO ─────────────
st.markdown("---")
st.subheader("1️⃣ Selecciona el tipo de producto")

if "Producto" not in df.columns:
    st.error("No encuentro la columna 'Producto' en BD_reto_circular.csv. Ajusta el nombre en el código.")
    st.stop()

productos_disponibles = sorted(df["Producto"].dropna().unique().tolist())
producto_sel = st.radio(
    "Tipo de producto",
    options=productos_disponibles,
    index=0,
    horizontal=True,
)
st.markdown(f"**Producto seleccionado:** {producto_sel}")

df_prod = df[df["Producto"] == producto_sel].copy()

imp = df_prod[df_prod["flujo_id"] == 1].set_index("Fecha")["Exportaciones"].asfreq("MS")
exp = df_prod[df_prod["flujo_id"] == 2].set_index("Fecha")["Exportaciones"].asfreq("MS")

FORECAST_STEPS = 12

# ───────────── ADF + AUTO_SARIMA ─────────────
st.markdown("---")
st.subheader("2️⃣ Estacionariedad y modelo SARIMA")

col1, col2 = st.columns(2)
adf_imp = test_estacionariedad(imp, f"Importaciones – {producto_sel}")
adf_exp = test_estacionariedad(exp, f"Exportaciones – {producto_sel}")

with col1:
    st.markdown("**Importaciones**")
    st.json(adf_imp)
with col2:
    st.markdown("**Exportaciones**")
    st.json(adf_exp)

with st.spinner("Ajustando SARIMA para Importaciones..."):
    fc_imp, ci_imp, order_imp, sorder_imp, aic_imp, bic_imp, res_imp = generar_forecast(
        imp.values, imp.index.tolist(), FORECAST_STEPS
    )

with st.spinner("Ajustando SARIMA para Exportaciones..."):
    fc_exp, ci_exp, order_exp, sorder_exp, aic_exp, bic_exp, res_exp = generar_forecast(
        exp.values, exp.index.tolist(), FORECAST_STEPS
    )

c1, c2 = st.columns(2)
with c1:
    st.markdown("**Modelo Importaciones**")
    st.markdown(f"- SARIMA{order_imp}×{sorder_imp}\n- AIC: {aic_imp:,.1f}\n- BIC: {bic_imp:,.1f}")
with c2:
    st.markdown("**Modelo Exportaciones**")
    st.markdown(f"- SARIMA{order_exp}×{sorder_exp}\n- AIC: {aic_exp:,.1f}\n- BIC: {bic_exp:,.1f}")

# ───────────── GRÁFICAS ─────────────
st.markdown("---")
st.subheader("3️⃣ Pronóstico a 12 meses con IC 95%")

fig_imp = plot_forecast(
    imp, fc_imp, ci_imp,
    f"Importaciones — {producto_sel}",
    color_hist="#636EFA",
    color_fc="#EF553B",
)
st.plotly_chart(fig_imp, use_container_width=True)

fig_exp = plot_forecast(
    exp, fc_exp, ci_exp,
    f"Exportaciones — {producto_sel}",
    color_hist="#00CC96",
    color_fc="#AB63FA",
)
st.plotly_chart(fig_exp, use_container_width=True)

# ───────────── TABLAS ─────────────
st.markdown("---")
st.subheader("4️⃣ Tablas de pronóstico")

tab_imp = pd.DataFrame({
    "Fecha": fc_imp.index.strftime("%Y-%m"),
    "Importaciones (USD)": fc_imp.values.round(0).astype(int),
    "IC Inferior 95%": ci_imp.iloc[:, 0].values.round(0).astype(int),
    "IC Superior 95%": ci_imp.iloc[:, 1].values.round(0).astype(int),
})
tab_exp = pd.DataFrame({
    "Fecha": fc_exp.index.strftime("%Y-%m"),
    "Exportaciones (USD)": fc_exp.values.round(0).astype(int),
    "IC Inferior 95%": ci_exp.iloc[:, 0].values.round(0).astype(int),
    "IC Superior 95%": ci_exp.iloc[:, 1].values.round(0).astype(int),
})

c1, c2 = st.columns(2)
with c1:
    st.markdown("**Importaciones**")
    st.dataframe(tab_imp, use_container_width=True, hide_index=True)
with c2:
    st.markdown("**Exportaciones**")
    st.dataframe(tab_exp, use_container_width=True, hide_index=True)

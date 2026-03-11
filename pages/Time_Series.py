# pages/Time_Series.py

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller
import warnings
import os

warnings.filterwarnings("ignore")

# ══════════════════════════════════════════════════════════════════
# RUTA AL CSV — sube un nivel desde pages/ hasta la raíz del repo
# ══════════════════════════════════════════════════════════════════
DATA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "Exportaciones_carne.csv"
)

# ══════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE PÁGINA
# ══════════════════════════════════════════════════════════════════
st.set_page_config(page_title="Serie de Tiempo — Carne", layout="wide")
st.title("📈 Modelos SARIMA — Comercio Exterior de Carne México")

# ══════════════════════════════════════════════════════════════════
# FUNCIONES
# ══════════════════════════════════════════════════════════════════
def cargar_series(path):
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = df.columns.str.strip()
    df["Fecha"] = pd.to_datetime(df["Fecha"], dayfirst=True)
    agg = (
        df.groupby(["Fecha", "flujo_id"])["Exportaciones"]
        .sum()
        .reset_index()
        .sort_values("Fecha")
    )
    exp = (agg[agg["flujo_id"] == 2]
           .set_index("Fecha")["Exportaciones"]
           .asfreq("MS")
           .interpolate("linear"))
    imp = (agg[agg["flujo_id"] == 1]
           .set_index("Fecha")["Exportaciones"]
           .asfreq("MS")
           .interpolate("linear"))
    return exp, imp


def prueba_adf(serie, nombre):
    r = adfuller(serie.dropna(), autolag="AIC")
    return {
        "Serie"      : nombre,
        "Estadístico": round(r[0], 4),
        "p-valor"    : round(r[1], 4),
        "Resultado"  : "✅ Estacionaria" if r[1] < 0.05 else "❌ No estacionaria",
    }


def buscar_sarima(ts):
    """Grid search AIC: p,q ∈ {1,2}  P,Q ∈ {0,1}  d=D=1  s=12"""
    mejor_aic, mejor_params = np.inf, None
    for p in [1, 2]:
        for q in [1, 2]:
            for P in [0, 1]:
                for Q in [0, 1]:
                    try:
                        r = SARIMAX(
                            ts,
                            order=(p, 1, q),
                            seasonal_order=(P, 1, Q, 12),
                            trend="c",
                            enforce_stationarity=False,
                            enforce_invertibility=False,
                        ).fit(disp=False, maxiter=150)
                        if r.aic < mejor_aic:
                            mejor_aic    = r.aic
                            mejor_params = (p, 1, q, P, 1, Q)
                    except Exception:
                        pass
    return mejor_params, mejor_aic


def ajustar(ts, params):
    p, d, q, P, D, Q = params
    return SARIMAX(
        ts,
        order=(p, d, q),
        seasonal_order=(P, D, Q, 12),
        trend="c",
        enforce_stationarity=False,
        enforce_invertibility=False,
    ).fit(disp=False, maxiter=200)


def forecast(res, pasos=12):
    fc   = res.get_forecast(steps=pasos)
    mean = fc.predicted_mean / 1e6
    ci   = fc.conf_int(alpha=0.05)
    lo   = ci.iloc[:, 0].clip(lower=0) / 1e6
    hi   = ci.iloc[:, 1] / 1e6
    return mean, lo, hi


def crear_grafica(hist, fc_mean, fc_lo, fc_hi,
                  titulo, subtitulo, c_hist, c_fc):
    fig, ax = plt.subplots(figsize=(13, 5), facecolor="white")
    ax.set_facecolor("white")
    ax.grid(True, color="#eeeeee", linewidth=0.8, zorder=0)

    ax.plot(hist.index, hist.values,
            color=c_hist, linewidth=1.8,
            label="Histórico (2006–2025)", zorder=3)

    ax.fill_between(fc_mean.index, fc_lo.values, fc_hi.values,
                    color=c_fc, alpha=0.18, label="IC 95%", zorder=2)

    ax.plot(fc_mean.index, fc_mean.values,
            color=c_fc, linewidth=2.5, linestyle="--",
            marker="o", markersize=5,
            label="Pronóstico 12 meses", zorder=4)

    last = hist.index[-1]
    ax.axvline(x=last, color="#9e9e9e", linewidth=1.2, linestyle=":")
    ax.text(last, ax.get_ylim()[1] * 0.97,
            "  Último dato", fontsize=8.5, color="#757575", va="top")

    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.tick_params(axis="x", labelsize=10)
    ax.tick_params(axis="y", labelsize=10)
    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.set_ylabel("Millones USD", fontsize=11)
    ax.set_xlim(pd.Timestamp("2006-01-01"),
                pd.Timestamp(fc_mean.index[-1]) + pd.DateOffset(months=1))

    ax.set_title(f"{titulo}\n{subtitulo}",
                 fontsize=11, fontweight="bold", pad=8, loc="left")
    ax.legend(loc="upper left", fontsize=9,
              framealpha=0.85, edgecolor="#cccccc", fancybox=False)
    ax.text(0.99, 0.05,
            f"Pronóstico total: ${fc_mean.sum():,.0f}M USD",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=10, color=c_fc, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3",
                      facecolor="white", edgecolor=c_fc, alpha=0.85))
    for spine in ax.spines.values():
        spine.set_edgecolor("#dddddd")

    plt.tight_layout()
    return fig


# ══════════════════════════════════════════════════════════════════
# CARGA Y MODELADO (cacheado para no recalcular en cada interacción)
# ══════════════════════════════════════════════════════════════════
@st.cache_data(show_spinner=False)
def pipeline(path):
    exp_ts, imp_ts = cargar_series(path)

    params_exp, aic_exp = buscar_sarima(exp_ts)
    params_imp, aic_imp = buscar_sarima(imp_ts)

    res_exp = ajustar(exp_ts, params_exp)
    res_imp = ajustar(imp_ts, params_imp)

    fc_e_mean, fc_e_lo, fc_e_hi = forecast(res_exp)
    fc_i_mean, fc_i_lo, fc_i_hi = forecast(res_imp)

    return (exp_ts, imp_ts,
            params_exp, params_imp,
            aic_exp, aic_imp,
            res_exp, res_imp,
            fc_e_mean, fc_e_lo, fc_e_hi,
            fc_i_mean, fc_i_lo, fc_i_hi)


# ══════════════════════════════════════════════════════════════════
# EJECUCIÓN
# ══════════════════════════════════════════════════════════════════
with st.spinner("⏳ Ajustando modelos SARIMA..."):
    (exp_ts, imp_ts,
     params_exp, params_imp,
     aic_exp, aic_imp,
     res_exp, res_imp,
     fc_e_mean, fc_e_lo, fc_e_hi,
     fc_i_mean, fc_i_lo, fc_i_hi) = pipeline(DATA_PATH)

# ── KPIs ──────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("📤 Exportación (próx. 12 m)",
          f"${fc_e_mean.sum():,.0f}M USD")
k2.metric("📥 Importación (próx. 12 m)",
          f"${fc_i_mean.sum():,.0f}M USD")
k3.metric("Modelo Exportación",
          f"SARIMA({params_exp[0]},1,{params_exp[2]})")
k4.metric("Modelo Importación",
          f"SARIMA({params_imp[0]},1,{params_imp[2]})"
          f"({params_imp[3]},1,{params_imp[5]},12)")

st.divider()

# ── Prueba ADF ────────────────────────────────────────────────────
with st.expander("🔍 Prueba de Estacionariedad (ADF)", expanded=False):
    adf_rows = [
        prueba_adf(exp_ts,                  "Exportación nivel"),
        prueba_adf(imp_ts,                  "Importación nivel"),
        prueba_adf(exp_ts.diff().dropna(),  "Exportación Δ(1)"),
        prueba_adf(imp_ts.diff().dropna(),  "Importación Δ(1)"),
    ]
    st.dataframe(pd.DataFrame(adf_rows),
                 use_container_width=True, hide_index=True)
    st.caption("d=1 confirmado: ambas series se vuelven estacionarias con una diferencia.")

# ── Parámetros del modelo ─────────────────────────────────────────
with st.expander("📋 Parámetros del Modelo", expanded=False):
    info = pd.DataFrame([
        {"Flujo": "Exportación",
         "Orden SARIMA": f"({params_exp[0]},1,{params_exp[2]})({params_exp[3]},1,{params_exp[5]},12)",
         "AIC": round(aic_exp, 1),
         "BIC": round(res_exp.bic, 1)},
        {"Flujo": "Importación",
         "Orden SARIMA": f"({params_imp[0]},1,{params_imp[2]})({params_imp[3]},1,{params_imp[5]},12)",
         "AIC": round(aic_imp, 1),
         "BIC": round(res_imp.bic, 1)},
    ])
    st.dataframe(info, use_container_width=True, hide_index=True)

st.divider()

# ── Gráficas ──────────────────────────────────────────────────────
st.subheader("📊 Histórico y Pronóstico")

orden_e = (f"SARIMA({params_exp[0]},1,{params_exp[2]})"
           f"({params_exp[3]},1,{params_exp[5]},12)  |  AIC={aic_exp:.0f}"
           f"  |  d=1, D=1, s=12")
orden_i = (f"SARIMA({params_imp[0]},1,{params_imp[2]})"
           f"({params_imp[3]},1,{params_imp[5]},12)  |  AIC={aic_imp:.0f}"
           f"  |  d=1, D=1, s=12")

fig_exp = crear_grafica(
    exp_ts / 1e6, fc_e_mean, fc_e_lo, fc_e_hi,
    "Exportación de Carne México", orden_e,
    "#1565c0", "#e65100"
)
st.pyplot(fig_exp, use_container_width=True)
plt.close(fig_exp)

fig_imp = crear_grafica(
    imp_ts / 1e6, fc_i_mean, fc_i_lo, fc_i_hi,
    "Importación de Carne México", orden_i,
    "#1b5e20", "#bf360c"
)
st.pyplot(fig_imp, use_container_width=True)
plt.close(fig_imp)

st.divider()

# ── Tabla pronóstico mensual + descarga ───────────────────────────
st.subheader("📅 Pronóstico Mensual")

fc_df = pd.DataFrame({
    "Mes"                    : fc_e_mean.index.strftime("%b %Y"),
    "Exp. Pronóstico (M USD)": fc_e_mean.values.round(1),
    "Exp. IC Bajo (M USD)"   : fc_e_lo.values.round(1),
    "Exp. IC Alto (M USD)"   : fc_e_hi.values.round(1),
    "Imp. Pronóstico (M USD)": fc_i_mean.values.round(1),
    "Imp. IC Bajo (M USD)"   : fc_i_lo.values.round(1),
    "Imp. IC Alto (M USD)"   : fc_i_hi.values.round(1),
})
st.dataframe(fc_df, use_container_width=True, hide_index=True)

st.download_button(
    label="⬇️ Descargar pronóstico CSV",
    data=fc_df.to_csv(index=False, encoding="utf-8-sig"),
    file_name="sarima_forecast.csv",
    mime="text/csv",
)

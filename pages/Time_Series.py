import os
import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller
import matplotlib
matplotlib.use("Agg")  # backend sin GUI para Streamlit/servidor
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import warnings
import json

warnings.filterwarnings("ignore")

# ══════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE ENTORNO
# Detecta automáticamente si corre en Streamlit o en local/VS Code
# ══════════════════════════════════════════════════════════════════
try:
    import streamlit as st
    IS_STREAMLIT = True
except ImportError:
    IS_STREAMLIT = False

# Ruta al CSV — compatible con cualquier estructura de repo
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "Exportaciones_carne.csv")


# ══════════════════════════════════════════════════════════════════
# 1. CARGA Y PREPARACIÓN DE DATOS
# ══════════════════════════════════════════════════════════════════
def cargar_datos(path):
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = df.columns.str.strip()
    df["Fecha"] = pd.to_datetime(df["Fecha"], dayfirst=True)

    agg = (df.groupby(["Fecha", "flujo_id"])["Exportaciones"]
             .sum()
             .reset_index()
             .sort_values("Fecha"))

    exp_ts = (agg[agg["flujo_id"] == 2]
              .set_index("Fecha")["Exportaciones"]
              .asfreq("MS")
              .interpolate("linear"))

    imp_ts = (agg[agg["flujo_id"] == 1]
              .set_index("Fecha")["Exportaciones"]
              .asfreq("MS")
              .interpolate("linear"))

    return exp_ts, imp_ts


# ══════════════════════════════════════════════════════════════════
# 2. PRUEBA ADF
# ══════════════════════════════════════════════════════════════════
def adf_test(series, name):
    result = adfuller(series.dropna(), autolag="AIC")
    estatus = "✅ Estacionaria" if result[1] < 0.05 else "❌ No estacionaria"
    return {"Serie": name, "Estadístico": round(result[0], 4),
            "p-valor": round(result[1], 4), "Resultado": estatus}


# ══════════════════════════════════════════════════════════════════
# 3. BÚSQUEDA DE ÓRDENES ÓPTIMOS (grid search por AIC)
# ══════════════════════════════════════════════════════════════════
def buscar_mejor_sarima(ts, nombre):
    mejor_aic    = np.inf
    mejor_params = None
    for p in [1, 2]:
        for q in [1, 2]:
            for P in [0, 1]:
                for Q in [0, 1]:
                    try:
                        m = SARIMAX(ts,
                                    order=(p, 1, q),
                                    seasonal_order=(P, 1, Q, 12),
                                    trend="c",
                                    enforce_stationarity=False,
                                    enforce_invertibility=False)
                        r = m.fit(disp=False, maxiter=150)
                        if r.aic < mejor_aic:
                            mejor_aic    = r.aic
                            mejor_params = (p, 1, q, P, 1, Q)
                    except Exception:
                        pass
    return mejor_params, mejor_aic


# ══════════════════════════════════════════════════════════════════
# 4. AJUSTE DEL MODELO FINAL
# ══════════════════════════════════════════════════════════════════
def ajustar_sarima(ts, params):
    p, d, q, P, D, Q = params
    res = SARIMAX(ts,
                  order=(p, d, q),
                  seasonal_order=(P, D, Q, 12),
                  trend="c",
                  enforce_stationarity=False,
                  enforce_invertibility=False).fit(disp=False, maxiter=200)
    return res


# ══════════════════════════════════════════════════════════════════
# 5. PRONÓSTICO 12 MESES
# ══════════════════════════════════════════════════════════════════
def obtener_forecast(res, horizon=12):
    fc      = res.get_forecast(steps=horizon)
    fc_mean = fc.predicted_mean / 1e6
    fc_ci   = fc.conf_int(alpha=0.05)
    fc_lo   = fc_ci.iloc[:, 0].clip(lower=0) / 1e6
    fc_hi   = fc_ci.iloc[:, 1] / 1e6
    return fc_mean, fc_lo, fc_hi


# ══════════════════════════════════════════════════════════════════
# 6. GRÁFICA (devuelve fig de matplotlib — funciona en ambos modos)
# ══════════════════════════════════════════════════════════════════
def crear_grafica(hist_e, hist_i,
                  fc_e_mean, fc_e_lo, fc_e_hi,
                  fc_i_mean, fc_i_lo, fc_i_hi,
                  params_exp, params_imp,
                  aic_exp, aic_imp):

    fig, axes = plt.subplots(2, 1, figsize=(14, 10), facecolor="white")
    fig.subplots_adjust(hspace=0.45)

    configs = [
        (hist_e, fc_e_mean, fc_e_lo, fc_e_hi,
         "Exportación de Carne México — Pronóstico 2026",
         f"SARIMA({params_exp[0]},1,{params_exp[2]})({params_exp[3]},1,{params_exp[5]},12)"
         f"  |  AIC={aic_exp:.0f}",
         "#1565c0", "#e65100"),
        (hist_i, fc_i_mean, fc_i_lo, fc_i_hi,
         "Importación de Carne México — Pronóstico 2026",
         f"SARIMA({params_imp[0]},1,{params_imp[2]})({params_imp[3]},1,{params_imp[5]},12)"
         f"  |  AIC={aic_imp:.0f}",
         "#1b5e20", "#bf360c"),
    ]

    for ax, (hist, fc_mean, fc_lo, fc_hi,
             title, subtitle, c_hist, c_fc) in zip(axes, configs):

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
                label="Pronóstico 2026", zorder=4)

        last = hist.index[-1]
        ax.axvline(x=last, color="#9e9e9e", linewidth=1.3,
                   linestyle=":", zorder=5)
        ax.text(last, fc_hi.max() * 0.95,
                "  Nov 2025", fontsize=9, color="#616161", va="top")

        ax.xaxis.set_major_locator(mdates.YearLocator(2))
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
        ax.tick_params(axis="x", labelsize=10, rotation=0)
        ax.tick_params(axis="y", labelsize=10)
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
        ax.set_ylabel("Millones USD", fontsize=11)
        ax.set_xlim(pd.Timestamp("2006-01-01"),
                    pd.Timestamp("2026-12-01"))

        ax.set_title(f"{title}\n{subtitle}",
                     fontsize=12, fontweight="bold", pad=10, loc="left")
        ax.legend(loc="upper left", fontsize=10,
                  framealpha=0.85, edgecolor="#cccccc", fancybox=False)
        ax.text(0.99, 0.05,
                f"Total pronóstico 2026: ${fc_mean.sum():,.0f}M USD",
                transform=ax.transAxes, ha="right", va="bottom",
                fontsize=10, color=c_fc, fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3",
                          facecolor="white", edgecolor=c_fc, alpha=0.9))

        for spine in ax.spines.values():
            spine.set_edgecolor("#cccccc")

    fig.suptitle("Modelos SARIMA — Comercio Exterior de Carne México",
                 fontsize=15, fontweight="bold", y=1.01, color="#212121")

    return fig


# ══════════════════════════════════════════════════════════════════
# 7A. MODO STREAMLIT
# ══════════════════════════════════════════════════════════════════
def run_streamlit():
    st.set_page_config(page_title="SARIMA — Carne México", layout="wide")
    st.title("📈 Modelos SARIMA — Comercio Exterior de Carne México")

    # Cargar datos con cache
    @st.cache_data
    def load_and_fit(path):
        exp_ts, imp_ts = cargar_datos(path)
        params_exp, aic_exp = buscar_mejor_sarima(exp_ts, "Exportación")
        params_imp, aic_imp = buscar_mejor_sarima(imp_ts, "Importación")
        res_exp = ajustar_sarima(exp_ts, params_exp)
        res_imp = ajustar_sarima(imp_ts, params_imp)
        fc_e_mean, fc_e_lo, fc_e_hi = obtener_forecast(res_exp)
        fc_i_mean, fc_i_lo, fc_i_hi = obtener_forecast(res_imp)
        return (exp_ts, imp_ts,
                params_exp, params_imp,
                aic_exp, aic_imp,
                res_exp, res_imp,
                fc_e_mean, fc_e_lo, fc_e_hi,
                fc_i_mean, fc_i_lo, fc_i_hi)

    with st.spinner("Ajustando modelos SARIMA..."):
        (exp_ts, imp_ts,
         params_exp, params_imp,
         aic_exp, aic_imp,
         res_exp, res_imp,
         fc_e_mean, fc_e_lo, fc_e_hi,
         fc_i_mean, fc_i_lo, fc_i_hi) = load_and_fit(DATA_PATH)

    hist_e = exp_ts / 1e6
    hist_i = imp_ts / 1e6

    # ── KPIs ──────────────────────────────────────────────────────
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("📤 Exportación 2026",
              f"${fc_e_mean.sum():,.0f}M USD")
    k2.metric("📥 Importación 2026",
              f"${fc_i_mean.sum():,.0f}M USD")
    k3.metric("🔢 Modelo Exportación",
              f"SARIMA({params_exp[0]},1,{params_exp[2]})({params_exp[3]},1,{params_exp[5]},12)")
    k4.metric("🔢 Modelo Importación",
              f"SARIMA({params_imp[0]},1,{params_imp[2]})({params_imp[3]},1,{params_imp[5]},12)")

    st.divider()

    # ── Prueba ADF ────────────────────────────────────────────────
    with st.expander("🔍 Prueba de Estacionariedad (ADF)", expanded=False):
        adf_rows = [
            adf_test(exp_ts,                 "Exportación nivel"),
            adf_test(imp_ts,                 "Importación nivel"),
            adf_test(exp_ts.diff().dropna(), "Exportación Δ(1)"),
            adf_test(imp_ts.diff().dropna(), "Importación Δ(1)"),
        ]
        st.dataframe(pd.DataFrame(adf_rows), use_container_width=True,
                     hide_index=True)

    # ── Resumen de modelos ────────────────────────────────────────
    with st.expander("📋 Parámetros del Modelo", expanded=False):
        model_info = pd.DataFrame([
            {"Flujo": "Exportación",
             "Orden": f"({params_exp[0]},1,{params_exp[2]})({params_exp[3]},1,{params_exp[5]},12)",
             "AIC": round(aic_exp, 1), "BIC": round(res_exp.bic, 1)},
            {"Flujo": "Importación",
             "Orden": f"({params_imp[0]},1,{params_imp[2]})({params_imp[3]},1,{params_imp[5]},12)",
             "AIC": round(aic_imp, 1), "BIC": round(res_imp.bic, 1)},
        ])
        st.dataframe(model_info, use_container_width=True, hide_index=True)

    # ── Gráfica principal ─────────────────────────────────────────
    st.subheader("📊 Histórico y Pronóstico")
    fig = crear_grafica(hist_e, hist_i,
                        fc_e_mean, fc_e_lo, fc_e_hi,
                        fc_i_mean, fc_i_lo, fc_i_hi,
                        params_exp, params_imp,
                        aic_exp, aic_imp)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    # ── Tabla de pronóstico mensual ───────────────────────────────
    st.subheader("📅 Pronóstico Mensual 2026")
    fc_df = pd.DataFrame({
        "Mes"                    : fc_e_mean.index.strftime("%b %Y"),
        "Exp. Pronóstico (M USD)": fc_e_mean.values.round(1),
        "Exp. IC Low (M USD)"    : fc_e_lo.values.round(1),
        "Exp. IC High (M USD)"   : fc_e_hi.values.round(1),
        "Imp. Pronóstico (M USD)": fc_i_mean.values.round(1),
        "Imp. IC Low (M USD)"    : fc_i_lo.values.round(1),
        "Imp. IC High (M USD)"   : fc_i_hi.values.round(1),
    })
    st.dataframe(fc_df, use_container_width=True, hide_index=True)

    # Botón de descarga
    csv = fc_df.to_csv(index=False, encoding="utf-8-sig")
    st.download_button(
        label="⬇️ Descargar pronóstico CSV",
        data=csv,
        file_name="sarima_forecast_2026.csv",
        mime="text/csv",
    )


# ══════════════════════════════════════════════════════════════════
# 7B. MODO LOCAL / VS CODE
# ══════════════════════════════════════════════════════════════════
def run_local():
    print("Cargando datos...")
    exp_ts, imp_ts = cargar_datos(DATA_PATH)

    print("\n── Prueba ADF ──")
    for row in [
        adf_test(exp_ts,                 "Exportación nivel"),
        adf_test(imp_ts,                 "Importación nivel"),
        adf_test(exp_ts.diff().dropna(), "Exportación Δ(1)"),
        adf_test(imp_ts.diff().dropna(), "Importación Δ(1)"),
    ]:
        print(f"  {row['Serie']:<30} p={row['p-valor']}  {row['Resultado']}")

    print("\n── Buscando órdenes óptimos (grid search AIC) ──")
    params_exp, aic_exp = buscar_mejor_sarima(exp_ts, "Exportación")
    params_imp, aic_imp = buscar_mejor_sarima(imp_ts, "Importación")

    print("\n── Ajustando modelos ──")
    res_exp = ajustar_sarima(exp_ts, params_exp)
    res_imp = ajustar_sarima(imp_ts, params_imp)

    print(f"  Exportación — AIC={res_exp.aic:.1f}  BIC={res_exp.bic:.1f}")
    print(f"  Importación — AIC={res_imp.aic:.1f}  BIC={res_imp.bic:.1f}")

    fc_e_mean, fc_e_lo, fc_e_hi = obtener_forecast(res_exp)
    fc_i_mean, fc_i_lo, fc_i_hi = obtener_forecast(res_imp)

    print(f"\n── Pronóstico total 2026 ──")
    print(f"  Exportación: ${fc_e_mean.sum():,.0f}M USD")
    print(f"  Importación: ${fc_i_mean.sum():,.0f}M USD")

    # Guardar CSV
    fc_df = pd.DataFrame({
        "Fecha"                  : fc_e_mean.index,
        "Exp_Forecast_MUSD"      : fc_e_mean.values.round(1),
        "Exp_CI_Low_MUSD"        : fc_e_lo.values.round(1),
        "Exp_CI_High_MUSD"       : fc_e_hi.values.round(1),
        "Imp_Forecast_MUSD"      : fc_i_mean.values.round(1),
        "Imp_CI_Low_MUSD"        : fc_i_lo.values.round(1),
        "Imp_CI_High_MUSD"       : fc_i_hi.values.round(1),
    })
    out_path = os.path.join(BASE_DIR, "sarima_forecast.csv")
    fc_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\n✅ CSV guardado en: {out_path}")

    # Mostrar gráfica
    matplotlib.use("TkAgg")   # backend interactivo para VS Code
    fig = crear_grafica(exp_ts / 1e6, imp_ts / 1e6,
                        fc_e_mean, fc_e_lo, fc_e_hi,
                        fc_i_mean, fc_i_lo, fc_i_hi,
                        params_exp, params_imp,
                        aic_exp, aic_imp)
    plt.show()


# ══════════════════════════════════════════════════════════════════
# 8. PUNTO DE ENTRADA
# ══════════════════════════════════════════════════════════════════
if IS_STREAMLIT:
    run_streamlit()
else:
    run_local()

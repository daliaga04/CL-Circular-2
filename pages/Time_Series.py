import pandas as pd
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import warnings
import json

warnings.filterwarnings("ignore")

# ══════════════════════════════════════════════════════════════════
# 1. CARGA Y PREPARACIÓN DE DATOS
# ══════════════════════════════════════════════════════════════════
df = pd.read_csv("Exportaciones_carne.csv", encoding="utf-8-sig")
df.columns = df.columns.str.strip()
df["Fecha"] = pd.to_datetime(df["Fecha"], dayfirst=True)

# Agregar por flujo sumando todos los tipos de carne
# flujo_id=1 → Importación | flujo_id=2 → Exportación
agg = df.groupby(["Fecha", "flujo_id"])["Exportaciones"].sum().reset_index()
agg = agg.sort_values("Fecha")

exp_ts = agg[agg["flujo_id"] == 2].set_index("Fecha")["Exportaciones"].asfreq("MS")
imp_ts = agg[agg["flujo_id"] == 1].set_index("Fecha")["Exportaciones"].asfreq("MS")

# Rellenar meses faltantes con interpolación lineal
exp_ts = exp_ts.interpolate(method="linear")
imp_ts = imp_ts.interpolate(method="linear")

print(f"Exportación — {len(exp_ts)} obs | {exp_ts.index[0].date()} → {exp_ts.index[-1].date()}")
print(f"Importación — {len(imp_ts)} obs | {imp_ts.index[0].date()} → {imp_ts.index[-1].date()}")


# ══════════════════════════════════════════════════════════════════
# 2. PRUEBA DE ESTACIONARIEDAD (ADF)
# ══════════════════════════════════════════════════════════════════
def adf_test(series, name):
    result = adfuller(series.dropna(), autolag="AIC")
    estatus = "✅ Estacionaria" if result[1] < 0.05 else "❌ No estacionaria"
    print(f"ADF {name}: stat={result[0]:.4f}, p={result[1]:.4f} — {estatus}")

print("\n── Prueba ADF ──")
adf_test(exp_ts,              "Exportación nivel")
adf_test(imp_ts,              "Importación nivel")
adf_test(exp_ts.diff().dropna(), "Exportación Δ(1)")
adf_test(imp_ts.diff().dropna(), "Importación Δ(1)")
# Resultado: d=1 confirmado para ambas series


# ══════════════════════════════════════════════════════════════════
# 3. SELECCIÓN DE ÓRDENES POR AIC (grid search)
#    p, q ∈ {1, 2}  |  P, Q ∈ {0, 1}  |  d=D=1, s=12
# ══════════════════════════════════════════════════════════════════
def buscar_mejor_sarima(ts, nombre):
    mejor_aic    = np.inf
    mejor_params = None
    for p in [1, 2]:
        for q in [1, 2]:
            for P in [0, 1]:
                for Q in [0, 1]:
                    try:
                        m = SARIMAX(
                            ts,
                            order=(p, 1, q),
                            seasonal_order=(P, 1, Q, 12),
                            trend="c",
                            enforce_stationarity=False,
                            enforce_invertibility=False,
                        )
                        r = m.fit(disp=False, maxiter=150)
                        if r.aic < mejor_aic:
                            mejor_aic    = r.aic
                            mejor_params = (p, 1, q, P, 1, Q)
                    except Exception:
                        pass
    p, d, q, P, D, Q = mejor_params
    print(f"\n{nombre} — Mejor AIC={mejor_aic:.1f} | SARIMA({p},{d},{q})({P},{D},{Q},12)")
    return mejor_params

print("\n── Búsqueda de órdenes óptimos ──")
params_exp = buscar_mejor_sarima(exp_ts, "Exportación")
params_imp = buscar_mejor_sarima(imp_ts, "Importación")


# ══════════════════════════════════════════════════════════════════
# 4. AJUSTE DE MODELOS FINALES
# ══════════════════════════════════════════════════════════════════
def ajustar_sarima(ts, params, nombre):
    p, d, q, P, D, Q = params
    model = SARIMAX(
        ts,
        order=(p, d, q),
        seasonal_order=(P, D, Q, 12),
        trend="c",
        enforce_stationarity=False,
        enforce_invertibility=False,
    )
    res = model.fit(disp=False, maxiter=200)
    print(f"\n── {nombre} ──")
    print(f"   Orden : SARIMA({p},{d},{q})({P},{D},{Q},12)")
    print(f"   AIC   : {res.aic:.1f}")
    print(f"   BIC   : {res.bic:.1f}")
    return res

res_exp = ajustar_sarima(exp_ts, params_exp, "Modelo Exportación")
res_imp = ajustar_sarima(imp_ts, params_imp, "Modelo Importación")


# ══════════════════════════════════════════════════════════════════
# 5. PRONÓSTICO — 12 MESES (2026)
# ══════════════════════════════════════════════════════════════════
HORIZON = 12

def obtener_forecast(res):
    fc      = res.get_forecast(steps=HORIZON)
    fc_mean = fc.predicted_mean / 1e6
    fc_ci   = fc.conf_int(alpha=0.05)
    fc_lo   = fc_ci.iloc[:, 0].clip(lower=0) / 1e6
    fc_hi   = fc_ci.iloc[:, 1] / 1e6
    return fc_mean, fc_lo, fc_hi

fc_e_mean, fc_e_lo, fc_e_hi = obtener_forecast(res_exp)
fc_i_mean, fc_i_lo, fc_i_hi = obtener_forecast(res_imp)

print(f"\n── Pronóstico anual 2026 ──")
print(f"   Exportación total: ${fc_e_mean.sum():,.0f}M USD")
print(f"   Importación total: ${fc_i_mean.sum():,.0f}M USD")


# ══════════════════════════════════════════════════════════════════
# 6. EXPORTAR FORECAST A CSV
# ══════════════════════════════════════════════════════════════════
fc_df = pd.DataFrame({
    "Fecha"               : fc_e_mean.index,
    "Exp_Forecast_MUSD"   : fc_e_mean.values,
    "Exp_CI_Low_MUSD"     : fc_e_lo.values,
    "Exp_CI_High_MUSD"    : fc_e_hi.values,
    "Imp_Forecast_MUSD"   : fc_i_mean.values,
    "Imp_CI_Low_MUSD"     : fc_i_lo.values,
    "Imp_CI_High_MUSD"    : fc_i_hi.values,
})
fc_df.to_csv("sarima_forecast.csv", index=False, encoding="utf-8-sig")
print("\n✅ sarima_forecast.csv guardado")


# ══════════════════════════════════════════════════════════════════
# 7. GRÁFICA — HISTÓRICO + PRONÓSTICO (2 paneles)
# ══════════════════════════════════════════════════════════════════
hist_e = exp_ts / 1e6
hist_i = imp_ts / 1e6

fig, axes = plt.subplots(2, 1, figsize=(14, 10), facecolor="white")
fig.subplots_adjust(hspace=0.45)

configs = [
    (
        hist_e, fc_e_mean, fc_e_lo, fc_e_hi,
        "Exportación de Carne México — Pronóstico 2026",
        f"SARIMA({params_exp[0]},1,{params_exp[2]})({params_exp[3]},1,{params_exp[5]},12)"
        f"  |  AIC={res_exp.aic:.0f}  |  d=1, D=1, s=12",
        "#1565c0", "#e65100",
    ),
    (
        hist_i, fc_i_mean, fc_i_lo, fc_i_hi,
        "Importación de Carne México — Pronóstico 2026",
        f"SARIMA({params_imp[0]},1,{params_imp[2]})({params_imp[3]},1,{params_imp[5]},12)"
        f"  |  AIC={res_imp.aic:.0f}  |  d=1, D=1, s=12",
        "#1b5e20", "#bf360c",
    ),
]

for ax, (hist, fc_mean, fc_lo, fc_hi, title, subtitle, c_hist, c_fc) in zip(axes, configs):
    ax.set_facecolor("white")
    ax.grid(True, color="#eeeeee", linewidth=0.8, zorder=0)

    # Histórico completo
    ax.plot(hist.index, hist.values,
            color=c_hist, linewidth=1.8, label="Histórico (2006–2025)", zorder=3)

    # Banda IC 95%
    ax.fill_between(fc_mean.index, fc_lo.values, fc_hi.values,
                    color=c_fc, alpha=0.18, label="IC 95%", zorder=2)

    # Línea de pronóstico
    ax.plot(fc_mean.index, fc_mean.values,
            color=c_fc, linewidth=2.5, linestyle="--",
            marker="o", markersize=5, label="Pronóstico 2026", zorder=4)

    # Línea divisoria histórico / forecast
    last = hist.index[-1]
    ax.axvline(x=last, color="#9e9e9e", linewidth=1.3, linestyle=":", zorder=5)
    ax.text(last, ax.get_ylim()[1] if ax.get_ylim()[1] > 0 else fc_hi.max() * 1.05,
            "  Nov 2025", fontsize=9, color="#616161", va="top")

    # Formato ejes
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.tick_params(axis="x", labelsize=10, rotation=0)
    ax.tick_params(axis="y", labelsize=10)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.set_ylabel("Millones USD", fontsize=11)
    ax.set_xlim(pd.Timestamp("2006-01-01"), pd.Timestamp("2026-12-01"))

    # Títulos
    ax.set_title(f"{title}\n{subtitle}",
                 fontsize=12, fontweight="bold", pad=10, loc="left")

    # Leyenda
    ax.legend(loc="upper left", fontsize=10, framealpha=0.85,
              edgecolor="#cccccc", fancybox=False)

    # Anotación con total anual
    ax.text(0.99, 0.05,
            f"Total pronóstico 2026: ${fc_mean.sum():,.0f}M USD",
            transform=ax.transAxes, ha="right", va="bottom",
            fontsize=10, color=c_fc, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.3",
                      facecolor="white", edgecolor=c_fc, alpha=0.9))

    for spine in ax.spines.values():
        spine.set_edgecolor("#cccccc")

plt.suptitle("Modelos SARIMA — Comercio Exterior de Carne México",
             fontsize=15, fontweight="bold", y=1.01, color="#212121")

plt.savefig("sarima_modelos.png", dpi=150,
            bbox_inches="tight", facecolor="white", edgecolor="none")
plt.show()
print("✅ sarima_modelos.png guardado")

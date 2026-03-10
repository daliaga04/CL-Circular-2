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
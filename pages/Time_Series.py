# Librerias
import streamlit as st
import pandas as pd
import numpy as np
from prophet import Prophet
import plotly.graph_objects as go
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

st.title("Forecast y análisis de exportaciones")

# Cargar datos
st.header("Carga de datos")

df = pd.read_excel("data/BD reto circular.xlsx")
df["Fecha"] = pd.to_datetime(df["Fecha"])

st.write("Vista previa del dataset")
st.dataframe(df.head())

# Preparar series de tiempo
st.header("Preparación de series")

imp = df[df["flujo_id"] == 1].set_index("Fecha")["Exportaciones"].asfreq("MS")
exp = df[df["flujo_id"] == 2].set_index("Fecha")["Exportaciones"].asfreq("MS")

st.write("Serie de importaciones")
st.line_chart(imp)

st.write("Serie de exportaciones")
st.line_chart(exp)

# Crear modelo prophet
st.header("Modelo de pronóstico")

def train_prophet(series):

    df_p = series.reset_index()
    df_p.columns = ["ds","y"]

    model = Prophet(
        yearly_seasonality=True,
        changepoint_prior_scale=0.3
    )

    model.fit(df_p)

    return model

    # Entrenar modelo
    model_imp = train_prophet(imp)
model_exp = train_prophet(exp)

future_imp = model_imp.make_future_dataframe(periods=12, freq="MS")
future_exp = model_exp.make_future_dataframe(periods=12, freq="MS")

fc_imp = model_imp.predict(future_imp)
fc_exp = model_exp.predict(future_exp)

# Graficar el forecast
st.header("Pronóstico")

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=imp.index,
    y=imp.values,
    name="Importaciones reales"
))

fig.add_trace(go.Scatter(
    x=fc_imp["ds"],
    y=fc_imp["yhat"],
    name="Forecast importaciones"
))

st.plotly_chart(fig, use_container_width=True)
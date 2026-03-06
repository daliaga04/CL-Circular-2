# Librerias
import os
import pandas as pd
import numpy as np
from prophet import Prophet
import plotly.graph_objects as go
import warnings
warnings.filterwarnings('ignore')

#Cargar Base de Datos
# Asegúrate de que el archivo CSV esté en la misma carpeta que tu notebook
df = pd.read_csv("BD_reto_circular.csv")
df['Fecha'] = pd.to_datetime(df['Fecha'])

imp = df[df['flujo_id'] == 1].set_index('Fecha')['Exportaciones'].asfreq('MS')
exp = df[df['flujo_id'] == 2].set_index('Fecha')['Exportaciones'].asfreq('MS')

imp.index = pd.DatetimeIndex(imp.index)
exp.index = pd.DatetimeIndex(exp.index)

test_size = 12  # ← Este valor estaba vacío en tu notebook, ajústalo según tus datos
imp_train = imp.iloc[:-test_size]
imp_test  = imp.iloc[-test_size:]
exp_train = exp.iloc[:-test_size]
exp_test  = exp.iloc[-test_size:]

def train_prophet(serie, changepoint_prior=0.3):
    df_p = serie.reset_index().rename(columns={serie.index.name: 'ds', serie.name: 'y'})
    model = Prophet(
        changepoint_prior_scale=changepoint_prior,
        seasonality_prior_scale=12,
        yearly_seasonality=True,
        weekly_seasonality=False,
        daily_seasonality=False
    )
    model.fit(df_p)
    return model

model_imp = train_prophet(imp_train)
model_exp = train_prophet(exp_train)

def validate_prophet(model, serie_train, serie_test, nombre):
    future   = model.make_future_dataframe(periods=len(serie_test), freq='MS')
    forecast = model.predict(future)

    pred = forecast[forecast['ds'].isin(serie_test.index)]['yhat'].values
    real = serie_test.values

    mae  = np.mean(np.abs(real - pred))
    rmse = np.sqrt(np.mean((real - pred) ** 2))
    mape = np.mean(np.abs((real - pred) / real)) * 100

    print(f"\n{'='*50}")
    print(f" Prophet Train/Test — {nombre}")
    print(f"{'='*50}")
    print(f" MAE  : ${mae:>15,.0f}")
    print(f" RMSE : ${rmse:>15,.0f}")
    print(f" MAPE : {mape:>13.2f}%")

    return forecast, pred

fc_test_imp, pred_imp_test = validate_prophet(model_imp, imp_train, imp_test, "Importaciones")
fc_test_exp, pred_exp_test = validate_prophet(model_exp, exp_train, exp_test, "Exportaciones")

def plot_train_test_prophet(serie_train, serie_test, forecast, titulo):
    scale    = 1e6
    test_fc  = forecast[forecast['ds'].isin(serie_test.index)]
    corte    = serie_train.index[-1].strftime('%Y-%m-%d')
    y_max    = max(serie_train.values.max(), serie_test.values.max()) / scale * 1.1
    y_min    = serie_train.values.min() / scale * 0.9

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=serie_train.index, y=serie_train.values / scale,
        name='Train', line=dict(width=2)
    ))
    fig.add_trace(go.Scatter(
        x=serie_test.index, y=serie_test.values / scale,
        name='Test (real)', line=dict(width=2.5, dash='dot')
    ))
    fig.add_trace(go.Scatter(
        x=test_fc['ds'], y=test_fc['yhat'] / scale,
        name='Pronóstico', line=dict(width=2.5, dash='dash')
    ))
    fig.add_trace(go.Scatter(
        x=list(test_fc['ds']) + list(test_fc['ds'][::-1]),
        y=list(test_fc['yhat_upper'] / scale) + list(test_fc['yhat_lower'] / scale)[::-1],
        fill='toself', fillcolor='rgba(99,110,250,0.13)',
        line=dict(color='rgba(0,0,0,0)'),
        name='IC 95%', hoverinfo='skip'
    ))
    fig.add_shape(type="line",
        x0=corte, x1=corte, y0=y_min, y1=y_max,
        line=dict(color="gray", width=1.5, dash="dot")
    )
    fig.add_annotation(
        x=corte, y=y_max, text="Inicio test",
        showarrow=False, xanchor="left",
        font=dict(size=11, color="gray")
    )
    fig.update_layout(
        title=f"{titulo} | Prophet — Validación Train/Test",
        legend=dict(orientation='h', yanchor='top', y=-0.12,
                    xanchor='center', x=0.5)
    )
    fig.update_xaxes(title_text="Año")
    fig.update_yaxes(title_text="USD Millones")
    fig.show()  # Abre automáticamente en el navegador predeterminado

plot_train_test_prophet(imp_train, imp_test, fc_test_imp, "Importaciones — Carne y Despojos")
plot_train_test_prophet(exp_train, exp_test, fc_test_exp, "Exportaciones — Carne y Despojos")

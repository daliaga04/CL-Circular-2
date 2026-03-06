# Librerias
import pandas as pd
import numpy as np
from prophet import Prophet
import plotly.graph_objects as go
import warnings
warnings.filterwarnings('ignore')

#Cargar Base de Datos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(BASE_DIR, "..", "data", "BD_reto_circular.csv"))
df['Fecha'] = pd.to_datetime(df['Fecha'])

imp = df[df['flujo_id'] == 1].set_index('Fecha')['Exportaciones'].asfreq('MS')
exp = df[df['flujo_id'] == 2].set_index('Fecha')['Exportaciones'].asfreq('MS')

imp.index = pd.DatetimeIndex(imp.index)
exp.index = pd.DatetimeIndex(exp.index)
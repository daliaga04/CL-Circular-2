import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
import json
import warnings
warnings.filterwarnings("ignore")

df = pd.read_csv("empresas_exportadoras.csv", encoding="utf-8-sig")
df.columns = df.columns.str.strip()
df = df[df["Exportador"].str.strip() != "NO DETERMINADO"]

tipo_map = {
    "Carne Bovino Fresca/Refrigerada": "Bovino_Fresco",
    "Carne Bovino Congelado": "Bovino_Congelado",
    "Carne Cerdo": "Cerdo",
}
df["Tipo Carne"] = df["Producto"].str.strip().map(tipo_map).fillna("Otro")

agg = df.groupby("Exportador").agg(
    embarques        = ("Ordinal", "count"),
    valor_total      = ("US FOB", "sum"),
    volumen_total    = ("Volumen (kg)", "sum"),
    distancia_prom   = ("Distancia Frontera", "mean"),
    riesgo_prom      = ("Indice Seguridad", "mean"),
    aduanas_unicas   = ("Aduana", "nunique"),
    estados_unicos   = ("Estado", "nunique"),
    n_productos      = ("Tipo Carne", "nunique"),
).reset_index()
agg["precio_prom_kg"] = agg["valor_total"] / agg["volumen_total"]

pivot_carne = df.groupby(["Exportador","Tipo Carne"])["US FOB"].sum().unstack(fill_value=0)
pivot_carne = pivot_carne.div(pivot_carne.sum(axis=1), axis=0)
for col in ["Bovino_Fresco","Bovino_Congelado","Cerdo"]:
    if col not in pivot_carne.columns:
        pivot_carne[col] = 0
agg = agg.merge(pivot_carne[["Bovino_Fresco","Bovino_Congelado","Cerdo"]].rename(columns={
    "Bovino_Fresco": "pct_bovino_fresco",
    "Bovino_Congelado": "pct_bovino_congelado",
    "Cerdo": "pct_cerdo",
}), on="Exportador", how="left").fillna(0)

features = ["embarques","valor_total","volumen_total","precio_prom_kg",
            "distancia_prom","riesgo_prom","aduanas_unicas","estados_unicos",
            "n_productos","pct_bovino_fresco","pct_bovino_congelado","pct_cerdo"]
X = agg[features].copy()
scaler = StandardScaler()
Xs = scaler.fit_transform(X)

# Forzar k=4 para segmentación más accionable (ignorar outlier dominante)
# Usar log-transform para suavizar outliers
X_log = X.copy()
for col in ["embarques","valor_total","volumen_total"]:
    X_log[col] = np.log1p(X_log[col])
Xs_log = scaler.fit_transform(X_log)

sil_scores = {}
for k in range(2,8):
    km = KMeans(n_clusters=k, random_state=42, n_init=20)
    lbl = km.fit_predict(Xs_log)
    sil_scores[k] = silhouette_score(Xs_log, lbl)
    
best_k = max(sil_scores, key=sil_scores.get)
print("Silhouette scores:", sil_scores)
print("Mejor k:", best_k)

km_final = KMeans(n_clusters=best_k, random_state=42, n_init=20)
agg["Cluster"] = km_final.fit_predict(Xs_log)

pca = PCA(n_components=2, random_state=42)
coords = pca.fit_transform(Xs_log)
agg["PC1"] = coords[:,0]
agg["PC2"] = coords[:,1]

# Nombrar clusters por valor total mediano
perfil = agg.groupby("Cluster").agg(
    n_empresas    = ("Exportador", "count"),
    embarques_med = ("embarques", "median"),
    valor_med     = ("valor_total", "median"),
    volumen_med   = ("volumen_total", "median"),
    precio_med    = ("precio_prom_kg", "median"),
    distancia_med = ("distancia_prom", "median"),
    riesgo_med    = ("riesgo_prom", "median"),
    aduanas_med   = ("aduanas_unicas", "median"),
    pct_fresco    = ("pct_bovino_fresco", "mean"),
    pct_congelado = ("pct_bovino_congelado", "mean"),
    pct_cerdo     = ("pct_cerdo", "mean"),
).reset_index().sort_values("valor_med")

# Asignar etiquetas por ranking de valor
labels_map = {}
nombres = ["Micro\nExportador", "Exportador\nPequeño", "Exportador\nMediano", "Gran\nExportador",
           "Exportador\nNivel 5", "Exportador\nNivel 6", "Exportador\nNivel 7"]
for i, row in enumerate(perfil.itertuples()):
    labels_map[row.Cluster] = nombres[i]

agg["Segmento"] = agg["Cluster"].map(labels_map)
perfil["Segmento"] = perfil["Cluster"].map(labels_map)
print(perfil[["Segmento","n_empresas","embarques_med","valor_med","distancia_med","riesgo_med"]].to_string())

# ============================================================
# CHARTS
# ============================================================
COLORS = px.colors.qualitative.Set2[:best_k]
cluster_color = {seg: COLORS[i] for i, seg in enumerate(perfil["Segmento"])}

# 1. Scatter PCA
fig1 = go.Figure()
for seg in agg["Segmento"].unique():
    sub = agg[agg["Segmento"] == seg]
    fig1.add_trace(go.Scatter(
        x=sub["PC1"], y=sub["PC2"],
        mode="markers",
        name=seg.replace("\n"," "),
        marker=dict(size=9, opacity=0.75, color=cluster_color[seg]),
        customdata=sub[["Exportador","embarques","valor_total","aduanas_unicas"]].values,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Embarques: %{customdata[1]:,}<br>"
            "Valor: $%{customdata[2]:,.0f}<br>"
            "Aduanas: %{customdata[3]}<extra></extra>"
        ),
    ))
fig1.update_layout(
    title={"text": "Clusters de Empresas Exportadoras (PCA)<br>"
                   "<span style='font-size:15px;font-weight:normal'>K-Means con log-transform | Agrupadas por perfil exportador</span>"},
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
)
fig1.update_xaxes(title_text="Componente 1")
fig1.update_yaxes(title_text="Componente 2")
fig1.update_traces(cliponaxis=False)
fig1.write_image("cluster_pca.png")
with open("cluster_pca.png.meta.json","w") as f:
    json.dump({"caption":"Dispersión PCA de empresas por cluster",
               "description":"Scatter plot en espacio PCA mostrando los clusters de empresas exportadoras de carne"}, f)

# 2. Bubble: Valor vs Embarques por cluster
fig2 = go.Figure()
for seg in agg["Segmento"].unique():
    sub = agg[agg["Segmento"] == seg]
    fig2.add_trace(go.Scatter(
        x=sub["embarques"],
        y=sub["valor_total"] / 1e6,
        mode="markers",
        name=seg.replace("\n"," "),
        marker=dict(
            size=np.sqrt(sub["volumen_total"] / sub["volumen_total"].max()) * 40 + 6,
            opacity=0.7,
            color=cluster_color[seg],
        ),
        customdata=sub[["Exportador","distancia_prom","riesgo_prom"]].values,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Embarques: %{x:,}<br>"
            "Valor: $%{y:.2f}M<br>"
            "Dist. media: %{customdata[1]:,.0f} km<br>"
            "Riesgo: %{customdata[2]:.1f}<extra></extra>"
        ),
    ))
fig2.update_layout(
    title={"text": "Embarques vs Valor por Segmento<br>"
                   "<span style='font-size:15px;font-weight:normal'>Tamaño = volumen exportado (kg)</span>"},
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
)
fig2.update_xaxes(title_text="Embarques", type="log")
fig2.update_yaxes(title_text="Valor (USD M)", type="log")
fig2.update_traces(cliponaxis=False)
fig2.write_image("cluster_bubble.png")
with open("cluster_bubble.png.meta.json","w") as f:
    json.dump({"caption":"Embarques vs Valor por segmento de empresa",
               "description":"Bubble chart log-log de embarques vs valor total, tamaño proporcional al volumen"}, f)

# 3. Radar de perfil por cluster
from plotly.subplots import make_subplots

radar_vars = ["embarques_med","valor_med","distancia_med","riesgo_med","aduanas_med","pct_fresco","pct_congelado","pct_cerdo"]
radar_labels = ["Embarques","Valor","Distancia","Riesgo","Aduanas","% Fresco","% Congelado","% Cerdo"]

# Normalizar 0-1 para radar
perfil_norm = perfil.copy()
for col in radar_vars:
    mn, mx = perfil[col].min(), perfil[col].max()
    perfil_norm[col] = (perfil[col] - mn) / (mx - mn) if mx > mn else 0

fig3 = go.Figure()
for i, row in perfil_norm.iterrows():
    seg = row["Segmento"].replace("\n"," ")
    vals = [row[v] for v in radar_vars] + [row[radar_vars[0]]]
    lbls = radar_labels + [radar_labels[0]]
    fig3.add_trace(go.Scatterpolar(
        r=vals, theta=lbls,
        fill="toself", name=seg,
        line_color=COLORS[list(perfil_norm["Segmento"]).index(row["Segmento"])],
        opacity=0.6,
    ))
fig3.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
    title={"text": "Perfil Normalizado por Segmento<br>"
                   "<span style='font-size:15px;font-weight:normal'>Variables clave normalizadas 0-1</span>"},
    legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
)
fig3.write_image("cluster_radar.png")
with open("cluster_radar.png.meta.json","w") as f:
    json.dump({"caption":"Radar de perfil normalizado por segmento",
               "description":"Gráfico de radar comparando los perfiles de cada cluster en variables clave"}, f)

# 4. Barras: distribución de empresas y valor por segmento
fig4 = go.Figure()
segs_ord = perfil["Segmento"].str.replace("\n"," ").tolist()
fig4.add_trace(go.Bar(
    x=segs_ord,
    y=perfil["n_empresas"],
    name="Empresas",
    marker_color=COLORS[:best_k],
    text=perfil["n_empresas"],
    textposition="outside",
    yaxis="y",
))
fig4.update_layout(
    title={"text": "Empresas y Valor Mediano por Segmento<br>"
                   "<span style='font-size:15px;font-weight:normal'>De menor a mayor tamaño exportador</span>"},
    xaxis_title="Segmento",
    yaxis_title="Nº Empresas",
    showlegend=False,
)
fig4.update_traces(cliponaxis=False)
fig4.write_image("cluster_dist.png")
with open("cluster_dist.png.meta.json","w") as f:
    json.dump({"caption":"Distribución de empresas por segmento exportador",
               "description":"Barras mostrando cuántas empresas hay en cada cluster"}, f)

# Guardar CSV final
agg[["Exportador","Segmento","Cluster","embarques","valor_total","volumen_total",
     "precio_prom_kg","distancia_prom","riesgo_prom","aduanas_unicas","estados_unicos"]]\
    .sort_values(["Cluster","valor_total"], ascending=[True,False])\
    .to_csv("clusters_empresas.csv", index=False, encoding="utf-8-sig")

print("✅ Todo generado")
print(perfil[["Segmento","n_empresas","embarques_med","valor_med","distancia_med","riesgo_med","aduanas_med"]].to_string())

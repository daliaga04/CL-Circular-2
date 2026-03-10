# =====================================================
# SECCIÓN 1 — BARRAS: VALOR Y VOLUMEN POR ADUANA
# =====================================================
st.subheader("📦 Valor y Volumen por Aduana")

col1, col2 = st.columns(2)

with col1:
    df_val = agg_total.sort_values("Valor (USD M)", ascending=True)
    fig_val = go.Figure(go.Bar(
        x=df_val["Valor (USD M)"],
        y=df_val["Aduana"],
        orientation="h",
        marker=dict(
            color=df_val["Valor (USD M)"],
            colorscale="YlOrRd",
            showscale=False,
        ),
        text=df_val["Valor (USD M)"].map("${:,.1f}M".format),
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Valor: $%{x:,.2f}M USD<extra></extra>",
    ))
    val_max = df_val["Valor (USD M)"].max()
    fig_val.update_layout(
        title="Valor de Exportación (USD M)",
        height=max(350, len(df_val) * 38),
        margin={"r": 20, "t": 40, "l": 180, "b": 10},  # margen izquierdo amplio para nombres
        xaxis=dict(
            showgrid=True,
            gridcolor="#eeeeee",
            range=[0, val_max * 1.25],  # espacio derecho para etiquetas
        ),
        yaxis=dict(
            tickfont=dict(size=12),
            automargin=True,
        ),
        plot_bgcolor="white",
    )
    st.plotly_chart(fig_val, use_container_width=True)

with col2:
    df_vol = agg_total.sort_values("Volumen (t)", ascending=True)
    fig_vol = go.Figure(go.Bar(
        x=df_vol["Volumen (t)"],
        y=df_vol["Aduana"],
        orientation="h",
        marker=dict(
            color=df_vol["Volumen (t)"],
            colorscale="Blues",
            showscale=False,
        ),
        text=df_vol["Volumen (t)"].map("{:,.0f} t".format),
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Volumen: %{x:,.1f} t<extra></extra>",
    ))
    vol_max = df_vol["Volumen (t)"].max()
    fig_vol.update_layout(
        title="Volumen de Exportación (t)",
        height=max(350, len(df_vol) * 38),
        margin={"r": 20, "t": 40, "l": 180, "b": 10},
        xaxis=dict(
            showgrid=True,
            gridcolor="#eeeeee",
            range=[0, vol_max * 1.25],
        ),
        yaxis=dict(
            tickfont=dict(size=12),
            automargin=True,
        ),
        plot_bgcolor="white",
    )
    st.plotly_chart(fig_vol, use_container_width=True)

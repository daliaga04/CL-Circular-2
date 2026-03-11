import streamlit as st

# Configuración básica de la página
st.set_page_config(
    page_title="Inicio - Mercado de Carnes Frías y Congelados",
    layout="wide"
)

# ===== TÍTULO PRINCIPAL =====
st.title("Plataforma de Análisis del Mercado de Carnes Frías y Congelados")

st.markdown(
    """
Esta aplicación es una plataforma de **data analytics** para analizar el mercado de carnes frías y alimentos congelados
en el contexto del comercio entre **México y Estados Unidos**. Integra en un mismo entorno:

- Un **módulo de series de tiempo** con modelos SARIMA para proyectar exportaciones e importaciones de productos cárnicos.  
- Un **módulo de segmentación de empresas** que clasifica a los exportadores según su perfil operativo y potencial de negocio.
- Un **módulo de aduanas** indicando donde los principales cruces fronterizos.
- Un **módulo de mapa** donde se puede apreciar de que estado proviene la carne.
- Un *módulo de rutas** donde se puede apreciar las rutas que toman los camiones de incio al cruce fronterizo.  
"""
)

st.markdown("---")

# ===== INTRODUCCIÓN AL TEMA =====
st.subheader("Introducción al Mercado de Carnes Frías y Alimentos Congelados")

st.markdown(
    """
En México, el mercado de **carnes frías y alimentos congelados** ha crecido de manera sostenida en los últimos años,
impulsado por la urbanización, cambios en los hábitos de consumo y una mayor preferencia por productos prácticos, de fácil
preparación y con mayor vida de anaquel. Este dinamismo ha sido posible también gracias al fortalecimiento de las cadenas
de suministro en **logística y almacenamiento en frío**, lo que ha permitido una distribución más amplia de estos productos a nivel nacional.

A nivel internacional, la industria cárnica mexicana ha incrementado su presencia en el comercio exterior, con crecimientos
significativos en las exportaciones de productos cárnicos y derivados desde 2021, en un entorno fuertemente marcado por la
**integración productiva y logística con Estados Unidos**. El flujo bilateral México–EE. UU. constituye hoy uno de los
principales ejes del mercado, tanto por el volumen de intercambio como por el grado de interdependencia de sus cadenas agroalimentarias.

El objetivo central de esta plataforma es **analizar el potencial del mercado de carnes frías y productos congelados**
dentro del comercio bilateral, identificando oportunidades de crecimiento, tendencias de consumo y posibles áreas de desarrollo
para la industria. Para ello se emplea una metodología basada en el análisis de datos comerciales y estadísticas sectoriales,
apoyada en fuentes secundarias especializadas y en modelos cuantitativos que permiten:

1. **Pronosticar flujos de comercio** (exportaciones e importaciones) mediante modelos de **series de tiempo SARIMA**.  
2. **Clasificar empresas potencialmente relevantes** como clientes o socios, según su comportamiento exportador, volumen
   y características logísticas.

La plataforma, implementada como **dashboard interactivo en Streamlit**, permite explorar estas dimensiones de manera parametrizable,
visualizar escenarios de ventas futuros y distinguir perfiles de empresas objetivo, ofreciendo al usuario una visión integrada del mercado
y un soporte práctico para la toma de decisiones estratégicas en el sector cárnico y de alimentos congelados.
"""
)

st.markdown("---")

# ===== SECCIÓN: CÓMO USAR LA APLICACIÓN =====
st.subheader("Cómo navegar la aplicación")

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
**1. Series de Tiempo (Time_Series.py)**  
En esta sección podrás:

- Visualizar las series históricas de exportaciones e importaciones de carne.
- Consultar los **pronósticos SARIMA** a 12 meses con bandas de confianza.
- Descargar los resultados en formato CSV para análisis adicional.
"""
    )

with col2:
    st.markdown(
        """
**2. Segmentación de Empresas (Clusters / Empresas)**  
En esta sección podrás:

- Analizar los **clusters de empresas exportadoras** (Micro, Pequeñas, Medianas y Grandes).
- Filtrar por segmento, empresa o tipo de producto.
- Identificar clientes potenciales según volumen, logística y composición de productos.
"""
    )

st.markdown(
    """
**3. Reportes y Anexos**  
En las secciones de reportes podrás consultar:

- Resúmenes ejecutivos del análisis cuantitativo.
- Principales hallazgos y recomendaciones estratégicas.
- Detalles metodológicos (técnicas de preparación de datos, especificaciones de modelos, supuestos y limitaciones).
"""
)

st.markdown("---")

# ===== FOOTER =====
st.caption(
    "Esta plataforma fue desarrollada como herramienta de apoyo a la toma de decisiones "
    "en el sector cárnico y de alimentos congelados, utilizando datos de Penta_Transaction "
    "y Data México (Secretaría de Economía)."
)

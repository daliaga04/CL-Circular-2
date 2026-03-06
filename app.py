import streamlit as st

st.title("Mi primera app en Streamlit")

st.write("Hola 👋 esta es mi primera app desplegada desde GitHub")

numero = st.slider("Selecciona un número", 0, 100)

st.write("Número seleccionado:", numero)
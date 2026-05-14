import streamlit as st
import google.generativeai as genai
import pandas as pd
import json, io, datetime
from PIL import Image

st.set_page_config(page_title="Historial de Facturas", layout="wide")
st.title("📑 Extractor e Historial de Facturas")

if 'historial' not in st.session_state:
    st.session_state.historial = pd.DataFrame()

key = st.sidebar.text_input("API Key:", type="password")

if key:
    try:
        genai.configure(api_key=key)
        # Probamos con la versión 'latest' que apunta siempre a la más estable
        model = genai.GenerativeModel('gemini-1.5-flash-latest')
        
        upload = st.file_uploader("Subir Facturas:", accept_multiple_files=True)
        
        if upload and st.button("Procesar"):
        nuevos_datos = []
        for f in upload:
            img = Image.open(io.BytesIO(f.getvalue()))
            p = "Extrae JSON: Fecha (DD/MM/YYYY), Empresa, RUT, Subtotal, IVA, Total, Moneda. Solo el JSON."
            try:
                r = model.generate_content([p, img])
                res_txt = r.text.strip()
                inicio, fin = res_txt.find('{'), res_txt.rfind('}') + 1
                if inicio != -1:
                    dato = json.loads(res_txt[inicio:fin])
                    nuevos_datos.append(dato)
            except Exception as e:
                st.error(f"Error en {f.name}: {e}")
        
        if nuevos_datos:
            df_nuevo = pd.DataFrame(nuevos_datos)
            df_nuevo['Fecha'] = pd.to_datetime(df_nuevo['Fecha'], dayfirst=True, errors='coerce')
            df_nuevo['Año'] = df_nuevo['Fecha'].dt.year.fillna(0).astype(int)
            df_nuevo['Mes'] = df_nuevo['Fecha'].dt.month_name(locale='es_ES').fillna("Desconocido")
            st.session_state.historial = pd.concat([st.session_state.historial, df_nuevo], ignore_index=True)
            st.success("¡Procesado!")

    if not st.session_state.historial.empty:
        st.write("---")
        st.dataframe(st.session_state.historial, use_container_width=True)
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='openpyxl') as w:
            st.session_state.historial.to_excel(w, index=False)
        st.download_button("📥 Descargar Excel", out.getvalue(), "historial.xlsx")
else:
    st.info("Ingresa tu API Key")
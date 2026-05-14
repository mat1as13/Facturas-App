import streamlit as st
import google.generativeai as genai
import pandas as pd
import json, io, datetime
from PIL import Image

st.set_page_config(page_title="Historial de Facturas", layout="wide")
st.title("📑 Extractor e Historial de Facturas")

# Inicializar historial en la sesión
if 'historial' not in st.session_state:
    st.session_state.historial = pd.DataFrame()

key = st.sidebar.text_input("API Key:", type="password")

if key:
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    upload = st.file_uploader("Subir Facturas:", accept_multiple_files=True)
    
    if upload and st.button("Procesar"):
        nuevos_datos = []
        for f in upload:
            img = Image.open(io.BytesIO(f.getvalue()))
            # Le pedimos el formato de fecha exacto para que no haya errores luego
            p = "Extrae JSON: Fecha (DD/MM/YYYY), Empresa, RUT, Subtotal, IVA, Total, Moneda. Solo devuelve el objeto JSON."
            try:
                r = model.generate_content([p, img])
                respuesta = r.text.strip()
                
                # --- BUSCADOR DE JSON ROBUSTO ---
                inicio = respuesta.find('{')
                fin = respuesta.rfind('}') + 1
                if inicio != -1:
                    clean_json = respuesta[inicio:fin]
                    dato = json.loads(clean_json)
                    nuevos_datos.append(dato)
                else:
                    st.error(f"No se detectó formato de factura en: {f.name}")
            except Exception as e:
                st.error(f"Error procesando {f.name}: {e}")
        
        if nuevos_datos:
            df_nuevo = pd.DataFrame(nuevos_datos)
            # Intentar convertir fechas para separar por mes y año
            df_nuevo['Fecha'] = pd.to_datetime(df_nuevo['Fecha'], dayfirst=True, errors='coerce')
            df_nuevo['Año'] = df_nuevo['Fecha'].dt.year.fillna(0).astype(int)
            df_nuevo['Mes'] = df_nuevo['Fecha'].dt.month_name(locale='es_ES').fillna("Desconocido")
            
            st.session_state.historial = pd.concat([st.session_state.historial, df_nuevo], ignore_index=True)
            st.success("¡Facturas procesadas con éxito!")

    # --- MOSTRAR HISTORIAL ---
    if not st.session_state.historial.empty:
        st.write("### 📊 Historial Acumulado")
        
        # Filtros de búsqueda
        col1, col2 = st.columns(2)
        with col1:
            anios = ["Todos"] + sorted(list(st.session_state.historial['Año'].unique().astype(str)))
            sel_anio = st.selectbox("Filtrar por Año", anios)
        with col2:
            meses = ["Todos"] + list(st.session_state.historial['Mes'].unique())
            sel_mes = st.selectbox("Filtrar por Mes", meses)

        df_filtro = st.session_state.historial.copy()
        if sel_anio != "Todos":
            df_filtro = df_filtro[df_filtro['Año'] == int(sel_anio)]
        if sel_mes != "Todos":
            df_filtro = df_filtro[df_filtro['Mes'] == sel_mes]

        st.dataframe(df_filtro, use_container_width=True)

        # Descarga
        out = io.BytesIO()
        with pd.ExcelWriter(out, engine='openpyxl') as w:
            df_filtro.to_excel(w, index=False, sheet_name='Historial')
        
        st.download_button("📥 Descargar Excel Filtrado", out.getvalue(), f"historial_{datetime.date.today()}.xlsx")

        if st.button("Limpiar Historial"):
            st.session_state.historial = pd.DataFrame()
            st.rerun()
else:
    st.info("Ingresa tu API Key en la barra lateral")
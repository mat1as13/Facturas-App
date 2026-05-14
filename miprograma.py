import streamlit as st
import google.generativeai as genai
import pandas as pd
import json, io
from PIL import Image

st.title("📑 Extractor de Facturas")
key = st.sidebar.text_input("API Key:", type="password")

if key:
    genai.configure(api_key=key)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    upload = st.file_uploader("Fotos:", accept_multiple_files=True)
    if upload and st.button("Procesar"):
        res_list = []
        for f in upload:
            img = Image.open(io.BytesIO(f.getvalue()))
            p = "Extrae en JSON: Fecha, Empresa, RUT, Subtotal, IVA, Total, Moneda. Solo el JSON."
            try:
                r = model.generate_content([p, img])
                txt = r.text.strip().replace('```json', '').replace('```', '').strip()
                res_list.append(json.loads(txt))
            except: st.error("Error en una imagen")
        
        if res_list:
            df = pd.DataFrame(res_list)
            st.dataframe(df)
            out = io.BytesIO()
            with pd.ExcelWriter(out, engine='openpyxl') as w:
                df.to_excel(w, index=False)
            st.download_button("Bajar Excel", out.getvalue(), "facturas.xlsx")
else:
    st.info("Pon la API Key a la izquierda")
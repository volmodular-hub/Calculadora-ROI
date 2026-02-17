import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
import os
import json
import re
import base64
import requests 
from PIL import Image
from io import BytesIO
import urllib.parse 

# ==========================================
# 🔐 CLAVE DE GOOGLE (CON LIMPIEZA DE ESPACIOS)
# ==========================================
# He añadido .strip() por si al copiar en el iPad se coló un espacio
GOOGLE_API_KEY = "AIzaSyBXfXVgHa9j_UrdiFrYaeQ_GgrX9LpTwDQ".strip() 
LOGOTIPO = "logo.png"

st.set_page_config(page_title="Promotora IA - DIAGNOSTICO", layout="wide", page_icon="🩺")

# ==========================================
# 🧠 CEREBRO IA (CON DIAGNÓSTICO DE ERRORES)
# ==========================================

def analizar_imagen_diagnostico(image, tipo="testigo"):
    """
    Intenta conectar y MUESTRA EL ERROR REAL si falla.
    """
    # 1. Preparar imagen
    buffered = BytesIO()
    if image.mode in ("RGBA", "P"): image = image.convert("RGB")
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

    # 2. Prompt
    if tipo == "testigo":
        texto_prompt = "Extrae: PRECIO (number) y M2 (number). JSON: {'precio': 0, 'm2': 0}."
    else:
        texto_prompt = "Extrae: PRECIO, UBICACION, M2_SUELO. JSON: {'precio': 0, 'ubicacion': '', 'm2_suelo': 0}."

    # 3. INTENTO CON MODELO FLASH (El más rápido)
    modelo = "gemini-1.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={GOOGLE_API_KEY}"
    
    payload = {
        "contents": [{
            "parts": [
                {"text": texto_prompt},
                {"inline_data": {
                    "mime_type": "image/jpeg",
                    "data": img_str
                }}
            ]
        }]
    }
    
    try:
        response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
        
        # --- ZONA DE DIAGNÓSTICO ---
        if response.status_code == 200:
            st.toast("✅ Conexión exitosa con Google", icon="🟢")
            resultado = response.json()
            texto = resultado['candidates'][0]['content']['parts'][0]['text']
            match = re.search(r'\{.*\}', texto, re.DOTALL)
            if match: return json.loads(match.group(0))
            return {}
        else:
            # AQUÍ ESTÁ LA CLAVE: Mostramos por qué falla
            error_json = response.json()
            mensaje_error = error_json.get('error', {}).get('message', 'Error desconocido')
            st.error(f"❌ ERROR GOOGLE ({response.status_code}): {mensaje_error}")
            
            # Ayuda contextual según el error
            if response.status_code == 400:
                st.warning("💡 Pista: API Key inválida o mal escrita.")
            elif response.status_code == 403:
                st.warning("💡 Pista: Tu cuenta de Google Cloud no tiene permiso o bloquearon la key.")
            
            return {}

    except Exception as e:
        st.error(f"❌ Error de Python: {e}")
        return {}

def generar_render_arquitectonico(ubicacion, estilo):
    prompt = f"architectural render of a {estilo} house, located in {ubicacion}, sunny day, blue sky, 8k"
    prompt_encoded = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1280&height=720&nologo=true&seed={datetime.datetime.now().microsecond}"

# ==========================================
# 📄 PDF
# ==========================================
class PDF(FPDF):
    def header(self):
        if os.path.exists(LOGOTIPO):
            try: self.image(LOGOTIPO, 10, 8, 33)
            except: pass
            self.ln(25)
        else: self.ln(10)
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'DOSIER DE VIABILIDAD', 0, 1, 'R')
        self.ln(5)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Generado el {datetime.date.today()}', 0, 0, 'C')

def generar_pdf(terreno, testigos, financiero, render_path=None):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, f"  Proyecto: {terreno['nombre']}", 1, 1, 'L', fill=True)
    pdf.ln(5)
    if render_path and os.path.exists(render_path):
        try:
            pdf.image(render_path, x=15, y=pdf.get_y()+2, w=180)
            pdf.ln(110) 
        except: pass
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "DATOS FINANCIEROS", 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f"Inversión: {financiero['inversion']:,.0f} EUR", 0, 1)
    pdf.cell(0, 8, f"Beneficio: {financiero['beneficio']:,.0f} EUR", 0, 1)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"ROI: {financiero['roi']:.2f}% (Anual: {financiero['roi_anual']:.2f}%)", 0, 1)
    
    if render_path: pdf.add_page()
    pdf.ln(5)
    pdf.cell(0, 10, "TESTIGOS", 0, 1)
    pdf.set_font('Arial', '', 10)
    for i, t in enumerate(testigos):
        p = t['precio']
        m = t['m2']
        pdf.cell(0, 8, f"T{i+1}: {p:,.0f} EUR ({m} m2)", 1, 1)
        if t.get('img_path') and os.path.exists(t['img_path']):
            try:
                pdf.image(t['img_path'], x=15, y=pdf.get_y()+2, w=50)
                pdf.ln(40)
            except: pass
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 📱 INTERFAZ 
# ==========================================
st.title("🩺 Modo Diagnóstico (iPad)")
st.info("Sube una foto. Si falla, saldrá un mensaje ROJO. Cópialo y pégalo en el chat.")

with st.sidebar:
    st.header("⚙️ Configuración")
    meses_proyecto = st.slider("Meses", 1, 12, 3)
    coste_const_m2 = st.number_input("Coste Obra", 1200)
    m2_objetivo = st.number_input("m² Casa", 180)

if "suelo_data" not in st.session_state:
    st.session_state["suelo_data"] = {"precio": 100000.0, "nombre": "Parcela", "m2": 500.0, "render": None}

c1, c2 = st.columns([1, 1.5])

with c1:
    st.subheader("1. Terreno")
    up_suelo = st.file_uploader("Foto Terreno", type=["jpg", "png", "jpeg"], key="u_suelo")
    if up_suelo:
        img_s = Image.open(up_suelo)
        if st.button("🧠 PROBAR CONEXIÓN (Suelo)"):
            datos = analizar_imagen_diagnostico(img_s, "suelo")
            if datos:
                st.session_state["suelo_data"]["precio"] = float(datos.get("precio", 0))
                st.session_state["suelo_data"]["m2"] = float(datos.get("m2_suelo", 0))
                st.success("¡Funciona!")

    nombre_terreno = st.text_input("Ubicación", value=st.session_state["suelo_data"]["nombre"])
    precio_terreno = st.number_input("Precio (€)", value=st.session_state["suelo_data"]["precio"])

    if st.button("✨ Generar Render"):
        url_render = generar_render_arquitectonico(nombre_terreno, "Moderno")
        st.image(url_render)
        # Descarga simple para demo
        import requests
        resp = requests.get(url_render)
        with open("render_temp.jpg", "wb") as f: f.write(resp.content)
        st.session_state["suelo_data"]["render"] = "render_temp.jpg"

with c2:
    st.subheader("2. Testigos")
    lista_testigos = []
    for i in range(1, 2): # Solo 1 para probar rápido
        up_t = st.file_uploader(f"Foto Testigo {i}", key=f"ut_{i}")
        if up_t:
            img_t = Image.open(up_t)
            img_t.save(f"temp_t_{i}.jpg")
            if st.button(f"🧠 PROBAR CONEXIÓN (Testigo {i})"):
                datos = analizar_imagen_diagnostico(img_t, "testigo")
                st.write(datos) # Ver datos en bruto

# CÁLCULO SIMPLE PARA DEMO
if st.button("ANALIZAR"):
    st.success("Análisis realizado (Modo Demo)")

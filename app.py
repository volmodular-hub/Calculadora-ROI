import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
import os
import json
import re
import base64
import requests # Conexión directa "a prueba de balas"
from PIL import Image
from io import BytesIO
import urllib.parse 

# ==========================================
# 🔐 TU CLAVE DE GOOGLE
# ==========================================
GOOGLE_API_KEY = "AIzaSyBXfXVgHa9j_UrdiFrYaeQ_GgrX9LpTwDQ" 
LOGOTIPO = "logo.png"

st.set_page_config(page_title="Promotora IA Todoterreno", layout="wide", page_icon="🏗️")

# ==========================================
# 🧠 CEREBRO IA (MULTIMODELO)
# ==========================================

def analizar_imagen_bruteforce(image, tipo="testigo"):
    """
    Intenta conectar con 4 modelos distintos de Google hasta que uno responda.
    """
    # 1. Preparar imagen en base64
    buffered = BytesIO()
    if image.mode in ("RGBA", "P"): image = image.convert("RGB")
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

    # 2. Preparar el Prompt
    if tipo == "testigo":
        texto_prompt = "Actúa como experto inmobiliario. Extrae de la imagen: PRECIO (número) y M2 (número). Responde SOLO JSON: {'precio': 0, 'm2': 0}. Si no hay dato pon 0."
    else:
        texto_prompt = "Analiza el anuncio del terreno. Extrae: PRECIO (número), UBICACION (texto corto) y M2_SUELO (número). Responde SOLO JSON: {'precio': 0, 'ubicacion': '', 'm2_suelo': 0}."

    # 3. LISTA DE MODELOS (Si uno falla, probamos el siguiente)
    modelos_a_probar = [
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-flash-001",
        "gemini-pro-vision" # El viejo confiable
    ]

    # 4. Bucle de intentos
    for modelo in modelos_a_probar:
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
            # st.toast(f"Probando modelo: {modelo}...", icon="🔄") # Comentado para no molestar visualmente
            response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                # ¡ÉXITO!
                st.success(f"Conectado con éxito usando: {modelo}")
                resultado = response.json()
                texto_ia = resultado['candidates'][0]['content']['parts'][0]['text']
                
                # Limpiar JSON
                match = re.search(r'\{.*\}', texto_ia, re.DOTALL)
                if match:
                    return json.loads(match.group(0))
                else:
                    return {} # Respondió pero no JSON
            else:
                # Si es 404, seguimos al siguiente modelo del bucle
                continue 

        except Exception as e:
            continue

    st.error("❌ Todos los modelos de Google han fallado. Revisa tu conexión a internet.")
    return {}

def generar_render_arquitectonico(ubicacion, estilo):
    """
    Render gratuito con Pollinations
    """
    prompt = f"architectural render of a {estilo} house, located in {ubicacion}, sunny day, blue sky, cinematic lighting, 8k resolution, photorealistic"
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
        self.cell(0, 10, 'DOSIER DE VIABILIDAD - IA', 0, 1, 'R')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Generado el {datetime.date.today()}', 0, 0, 'C')

def generar_pdf(terreno, testigos, financiero, render_path=None):
    pdf = PDF()
    pdf.add_page()
    
    # PORTADA
    pdf.set_font('Arial', 'B', 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, f"  Proyecto: {terreno['nombre']}", 1, 1, 'L', fill=True)
    pdf.ln(5)

    if render_path and os.path.exists(render_path):
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "PROPUESTA VISUAL", 0, 1)
        try:
            pdf.image(render_path, x=15, y=pdf.get_y()+2, w=180)
            pdf.ln(110) 
        except: pass
    
    # DATOS
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "RESUMEN EJECUTIVO", 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f"Suelo: {terreno['precio']:,.0f} EUR | {terreno.get('m2',0)} m2", 0, 1)
    pdf.cell(0, 8, f"Inversión Total: {financiero['inversion']:,.0f} EUR", 0, 1)
    pdf.cell(0, 8, f"Beneficio Neto: {financiero['beneficio']:,.0f} EUR", 0, 1)
    
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(39, 174, 96)
    pdf.cell(0, 10, f"ROI PROYECTO: {financiero['roi']:.2f}%", 0, 1)
    pdf.cell(0, 10, f"ROI ANUALIZADO: {financiero['roi_anual']:.2f}%", 0, 1)
    pdf.set_text_color(0, 0, 0)
    
    if render_path: pdf.add_page()
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "COMPARABLES DE MERCADO", 0, 1)
    pdf.set_font('Arial', '', 10)
    
    for i, t in enumerate(testigos):
        p = t['precio']
        m = t['m2']
        pm2 = p/m if m>0 else 0
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(0, 8, f"Testigo {i+1}: {p:,.0f} EUR ({m} m2) - {pm2:,.0f} EUR/m2", 1, 1, fill=True)
        if t.get('img_path') and os.path.exists(t['img_path']):
            try:
                pdf.image(t['img_path'], x=15, y=pdf.get_y()+2, w=50)
                pdf.ln(40)
            except: pass
        else: pdf.ln(2)

    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 📱 INTERFAZ PRINCIPAL
# ==========================================
st.title("🏗️ Calculadora Promotora (Modo Todoterreno)")
st.caption("Prueba automática de múltiples modelos IA hasta conectar.")
st.markdown("---")

with st.sidebar:
    if os.path.exists(LOGOTIPO): st.image(LOGOTIPO, width=150)
    st.header("⚙️ Configuración")
    meses_proyecto = st.slider("Duración (Meses)", 1, 12, 3)
    coste_const_m2 = st.number_input("Coste Const. (€/m²)", 1200)
    gastos_generales = st.slider("Soft Costs (%)", 5, 25, 15) / 100
    impuestos_compra = 0.10
    m2_objetivo = st.number_input("m² Construcción Objetivo", 180)
    estilo_casa = st.selectbox("Estilo", ["Moderno Mediterráneo", "Minimalista Cubico", "Clásico", "Industrial"])

if "suelo_data" not in st.session_state:
    st.session_state["suelo_data"] = {"precio": 100000.0, "nombre": "Parcela", "m2": 500.0, "render": None}

c1, c2 = st.columns([1, 1.5])
with c1:
    st.subheader("1. Terreno")
    tab_m, tab_f = st.tabs(["✍️ Manual", "📸 Foto Cartel"])
    with tab_f:
        up_suelo = st.file_uploader("Foto Terreno", type=["jpg", "png", "jpeg"], key="u_suelo")
        if up_suelo:
            img_s = Image.open(up_suelo)
            if st.button("🧠 Analizar Suelo"):
                with st.spinner("Probando modelos de Google..."):
                    datos = analizar_imagen_bruteforce(img_s, "suelo")
                    if datos:
                        st.session_state["suelo_data"]["precio"] = float(datos.get("precio", 0))
                        st.session_state["suelo_data"]["m2"] = float(datos.get("m2_suelo", 0))
                        ubi = datos.get("ubicacion", "")
                        if ubi: st.session_state["suelo_data"]["nombre"] = ubi
                    else: st.warning("Ningún modelo pudo leer la foto.")

    nombre_terreno = st.text_input("Ubicación", value=st.session_state["suelo_data"]["nombre"])
    precio_terreno = st.number_input("Precio Suelo (€)", value=st.session_state["suelo_data"]["precio"], step=1000.0)
    m2_parcela = st.number_input("m² Parcela", value=st.session_state["suelo_data"]["m2"], step=10.0)

    st.markdown("#### 🎨 Diseño Virtual")
    if st.button("✨ Generar Render"):
        with st.spinner("Diseñando..."):
            try:
                url_render = generar_render_arquitectonico(nombre_terreno, estilo_casa)
                resp = requests.get(url_render)
                if resp.status_code == 200:
                    img_r = Image.open(BytesIO(resp.content))
                    img_r.save("render_temp.jpg")
                    st.session_state["suelo_data"]["render"] = "render_temp.jpg"
                    st.image(url_render, caption=estilo_casa)
            except Exception as e: st.error(e)

with c2:
    st.subheader("2. Comparables")
    lista_testigos = []
    for i in range(1, 4):
        with st.expander(f"🏠 Testigo {i}", expanded=False):
            cc_img, cc_dat = st.columns([1, 2])
            up_t = cc_img.file_uploader("Foto", key=f"ut_{i}", label_visibility="collapsed")
            if f"dt_{i}" not in st.session_state: st.session_state[f"dt_{i}"] = {"p":0.0, "m":0.0, "path":None}
            
            if up_t:
                img_t = Image.open(up_t)
                path = f"temp_t_{i}.jpg"
                if img_t.mode != 'RGB': img_t = img_t.convert('RGB')
                img_t.save(path)
                st.session_state[f"dt_{i}"]["path"] = path
                
                if st.session_state[f"dt_{i}"]["p"] == 0:
                    with st.spinner("Analizando..."):
                        datos = analizar_imagen_bruteforce(img_t, "testigo")
                        st.session_state[f"dt_{i}"]["p"] = float(datos.get("precio", 0))
                        st.session_state[f"dt_{i}"]["m"] = float(datos.get("m2", 0))

            with cc_dat:
                d = st.session_state[f"dt_{i}"]
                p = st.number_input("€", value=d["p"], key=f"p_{i}", step=1000.0)
                m = st.number_input("m2", value=d["m"], key=f"m_{i}", step=1.0)
                if p > 0: lista_testigos.append({"precio":p, "m2":m, "img_path":d["path"]})

st.markdown("---")
if st.button("ANALIZAR VIABILIDAD", type="primary", use_container_width=True):
    if not lista_testigos:
        st.error("⚠️ Faltan testigos.")
    else:
        validos = [t for t in lista_testigos if t['m2'] > 0]
        if validos:
            media_m2 = sum([t['precio']/t['m2'] for t in validos])/len(validos)
            precio_venta = media_m2 * m2_objetivo
        else:
            precio_venta = sum([t['precio'] for t in lista_testigos])/len(lista_testigos)
            media_m2 = 0

        coste_suelo_total = precio_terreno * (1+impuestos_compra)
        coste_obra = coste_const_m2 * m2_objetivo
        soft_costs = (coste_suelo_total + coste_obra) * gastos_generales
        inversion = coste_suelo_total + coste_obra + soft_costs
        beneficio = precio_venta - inversion
        roi = (beneficio/inversion)*100
        roi_anual = ((1+roi/100)**(12/meses_proyecto)-1)*100
        
        st.header("📊 Resultados")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Venta", f"{precio_venta:,.0f} €")
        c2.metric("Inversión", f"{inversion:,.0f} €")
        c3.metric("Beneficio", f"{beneficio:,.0f} €")
        c4.metric("ROI Anual", f"{roi_anual:.2f} %")
        
        st.divider()
        col_res, col_chart = st.columns([2, 1])
        with col_res:
            if roi > 20:
                st.success(f"✅ VIABLE (ROI {roi:.2f}%)")
                pdf_bytes = generar_pdf(
                    {"nombre": nombre_terreno, "precio": precio_terreno, "m2": m2_parcela},
                    lista_testigos,
                    {"inversion": inversion, "beneficio": beneficio, "roi": roi, "roi_anual": roi_anual, "meses": meses_proyecto},
                    render_path=st.session_state["suelo_data"]["render"]
                )
                st.download_button("📄 DESCARGAR DOSIER", pdf_bytes, "dosier.pdf", "application/pdf")
            else:
                st.error(f"❌ RIESGO ALTO (ROI {roi:.2f}%)")
        with col_chart:
            st.bar_chart(pd.DataFrame({'C':['Suelo','Obra','Soft','Bº'], 'V':[coste_suelo_total, coste_obra, soft_costs, beneficio]}).set_index('C'))

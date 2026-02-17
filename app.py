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
# 🔐 CONFIGURACIÓN
# ==========================================
GOOGLE_API_KEY = "AIzaSyBXfXVgHa9j_UrdiFrYaeQ_GgrX9LpTwDQ".strip() 
LOGOTIPO = "logo.png"

st.set_page_config(page_title="Promotora IA - Universal", layout="wide", page_icon="🏗️")

# ==========================================
# 🧠 CEREBRO IA (MULTIMODELO AUTOMÁTICO)
# ==========================================

def analizar_imagen_universal(image, tipo="testigo"):
    """
    Prueba 3 modelos diferentes de Google. Si uno falla, salta al siguiente.
    Esto garantiza que funcione con cualquier tipo de cuenta.
    """
    # 1. Preparar imagen
    buffered = BytesIO()
    if image.mode in ("RGBA", "P"): image = image.convert("RGB")
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")

    # 2. Prompt (Instrucciones)
    if tipo == "testigo":
        texto_prompt = "Eres un experto inmobiliario. Analiza la imagen. Extrae: PRECIO (solo numero) y M2 (solo numero). Responde SOLO un JSON así: {'precio': 0, 'm2': 0}. Si no ves el dato pon 0."
    else:
        texto_prompt = "Analiza el anuncio del terreno. Extrae: PRECIO (numero), UBICACION (texto breve), M2_SUELO (numero). Responde SOLO un JSON así: {'precio': 0, 'ubicacion': '', 'm2_suelo': 0}."

    # 3. LISTA DE MODELOS A PROBAR (En orden de prioridad)
    # Si falla el Flash, usará el Pro Vision (que funciona seguro)
    modelos = [
        "gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-pro-vision"  # <--- ESTE ES EL SALVAVIDAS
    ]

    for modelo in modelos:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent?key={GOOGLE_API_KEY}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": texto_prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": img_str}}
                ]
            }]
        }
        
        try:
            # st.toast(f"Intentando con modelo: {modelo}...", icon="⏳")
            response = requests.post(url, json=payload, headers={'Content-Type': 'application/json'})
            
            if response.status_code == 200:
                # ¡ÉXITO!
                st.toast(f"✅ Conectado con: {modelo}", icon="🟢")
                
                # Extraer y limpiar JSON
                resultado = response.json()
                try:
                    texto = resultado['candidates'][0]['content']['parts'][0]['text']
                    match = re.search(r'\{.*\}', texto, re.DOTALL)
                    if match:
                        return json.loads(match.group(0))
                except:
                    return {} # Falló el formato, pero conectó
                
                return {} # Si llegamos aquí, salimos del bucle con éxito

        except Exception:
            continue # Si falla, prueba el siguiente modelo de la lista

    st.error("❌ Todos los modelos fallaron. Verifica que la API Key esté activa en Google Cloud Console.")
    return {}

def generar_render_arquitectonico(ubicacion, estilo):
    prompt = f"architectural render of a {estilo} house, located in {ubicacion}, sunny day, blue sky, 8k resolution, photorealistic"
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
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "PROPUESTA VISUAL", 0, 1)
        try:
            pdf.image(render_path, x=15, y=pdf.get_y()+2, w=180)
            pdf.ln(110) 
        except: pass
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "RESUMEN EJECUTIVO", 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f"Suelo: {terreno['precio']:,.0f} EUR | {terreno.get('m2',0)} m2", 0, 1)
    pdf.cell(0, 8, f"Inversión: {financiero['inversion']:,.0f} EUR", 0, 1)
    pdf.cell(0, 8, f"Beneficio: {financiero['beneficio']:,.0f} EUR", 0, 1)
    
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(39, 174, 96)
    pdf.cell(0, 10, f"ROI: {financiero['roi']:.2f}% (Anual: {financiero['roi_anual']:.2f}%)", 0, 1)
    pdf.set_text_color(0, 0, 0)
    
    if render_path: pdf.add_page()
    pdf.ln(5)
    pdf.cell(0, 10, "COMPARABLES", 0, 1)
    pdf.set_font('Arial', '', 10)
    for i, t in enumerate(testigos):
        p = t['precio']
        m = t['m2']
        pm2 = p/m if m>0 else 0
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(0, 8, f"T{i+1}: {p:,.0f} EUR ({m} m2) - {pm2:,.0f} EUR/m2", 1, 1, fill=True)
        if t.get('img_path') and os.path.exists(t['img_path']):
            try:
                pdf.image(t['img_path'], x=15, y=pdf.get_y()+2, w=50)
                pdf.ln(40)
            except: pass
        else: pdf.ln(2)
    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 📱 INTERFAZ 
# ==========================================
st.title("🏗️ Calculadora Promotora IA")
st.caption("Sistema multi-modelo (Flash + Pro Vision)")
st.markdown("---")

with st.sidebar:
    if os.path.exists(LOGOTIPO): st.image(LOGOTIPO, width=150)
    st.header("⚙️ Configuración")
    meses_proyecto = st.slider("Meses", 1, 12, 3)
    coste_const_m2 = st.number_input("Coste Obra", 1200)
    gastos_generales = st.slider("Soft Costs %", 5, 25, 15)/100
    impuestos_compra = 0.10
    m2_objetivo = st.number_input("m² Casa", 180)
    estilo_casa = st.selectbox("Estilo", ["Moderno Mediterráneo", "Minimalista Cubico", "Clásico", "Industrial"])

if "suelo_data" not in st.session_state:
    st.session_state["suelo_data"] = {"precio": 100000.0, "nombre": "Parcela", "m2": 500.0, "render": None}

c1, c2 = st.columns([1, 1.5])

# SUELO
with c1:
    st.subheader("1. Terreno")
    tab_m, tab_f = st.tabs(["✍️ Manual", "📸 Foto Cartel"])
    with tab_f:
        up_suelo = st.file_uploader("Foto Terreno", type=["jpg", "png", "jpeg"], key="u_suelo")
        if up_suelo:
            img_s = Image.open(up_suelo)
            if st.button("🧠 Analizar Suelo"):
                with st.spinner("Conectando IA..."):
                    datos = analizar_imagen_universal(img_s, "suelo")
                    if datos:
                        st.session_state["suelo_data"]["precio"] = float(datos.get("precio", 0))
                        st.session_state["suelo_data"]["m2"] = float(datos.get("m2_suelo", 0))
                        ubi = datos.get("ubicacion", "")
                        if ubi: st.session_state["suelo_data"]["nombre"] = ubi
                        st.success("¡Datos extraídos!")

    nombre_terreno = st.text_input("Ubicación", value=st.session_state["suelo_data"]["nombre"])
    precio_terreno = st.number_input("Precio (€)", value=st.session_state["suelo_data"]["precio"], step=1000.0)
    m2_parcela = st.number_input("m² Parcela", value=st.session_state["suelo_data"]["m2"], step=10.0)

    if st.button("✨ Generar Render"):
        with st.spinner("Diseñando..."):
            try:
                url_render = generar_render_arquitectonico(nombre_terreno, estilo_casa)
                resp = requests.get(url_render)
                if resp.status_code == 200:
                    with open("render_temp.jpg", "wb") as f: f.write(resp.content)
                    st.session_state["suelo_data"]["render"] = "render_temp.jpg"
                    st.image(url_render, caption=estilo_casa)
            except Exception as e: st.error(e)

# TESTIGOS
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
                    with st.spinner("Leyendo..."):
                        datos = analizar_imagen_universal(img_t, "testigo")
                        st.session_state[f"dt_{i}"]["p"] = float(datos.get("precio", 0))
                        st.session_state[f"dt_{i}"]["m"] = float(datos.get("m2", 0))

            with cc_dat:
                d = st.session_state[f"dt_{i}"]
                p = st.number_input("€", value=d["p"], key=f"p_{i}", step=1000.0)
                m = st.number_input("m2", value=d["m"], key=f"m_{i}", step=1.0)
                if p > 0: lista_testigos.append({"precio":p, "m2":m, "img_path":d["path"]})

# CÁLCULO
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

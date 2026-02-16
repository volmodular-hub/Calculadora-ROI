import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
import os
import json
import re  # IMPORTANTE: Para buscar el JSON entre el texto
import google.generativeai as genai
from PIL import Image
import urllib.parse 
import requests # Para descargar el render
from io import BytesIO

# ==========================================
# 🔐 CONFIGURACIÓN
# ==========================================
# TU CLAVE API AQUÍ
GOOGLE_API_KEY = "AIzaSyDAeL2GfyusB3w55sLur27b7t7I_rbETy4" 
LOGOTIPO = "logo.png"

try:
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    st.error(f"Error Configuración API: {e}")

st.set_page_config(page_title="Promotora IA Debug", layout="wide", page_icon="🏗️")

# ==========================================
# 🧠 CEREBRO IA (VISIÓN & RENDER)
# ==========================================

def analizar_imagen_generico(image, tipo="testigo"):
    """
    Versión BLINDADA con depuración para ver por qué falla.
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # 1. Elegir el Prompt (Instrucciones) según qué estemos mirando
    if tipo == "testigo":
        prompt = """
        Actúa como un experto en datos inmobiliarios. Analiza esta imagen.
        Tu objetivo es extraer el PRECIO DE VENTA y los METROS CUADRADOS (m2).
        Responde ÚNICAMENTE con un objeto JSON válido.
        Formato: {"precio": 150000, "m2": 90}
        Si no encuentras algún dato, pon el valor 0. No inventes.
        """
    else: # SUELO
        prompt = """
        Analiza este cartel o anuncio de TERRENO/SOLAR.
        Extrae en JSON estos 3 campos:
        1. "precio": Precio de venta (número).
        2. "ubicacion": Nombre de la calle, barrio o zona que aparezca (texto).
        3. "m2_suelo": Metros cuadrados de la PARCELA (número).
        
        Formato: {"precio": 100000, "ubicacion": "Calle Mayor", "m2_suelo": 500}
        """
    
    try:
        with st.spinner(f"🤖 La IA está leyendo el {tipo}..."):
            response = model.generate_content([prompt, image])
            
            # --- ZONA DE DEPURACIÓN (VISIBLE EN PANTALLA) ---
            # Esto te ayudará a entender por qué falla si sale 0
            with st.expander(f"🕵️ Ver Datos Crudos de la IA ({tipo}) - Debug"):
                st.write(f"**Texto detectado:** {response.text}")
            
            # --- EXTRACCIÓN ROBUSTA CON REGEX ---
            # Buscamos cualquier cosa que parezca un JSON { ... }
            match = re.search(r'\{.*\}', response.text, re.DOTALL)
            
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
            else:
                return {}

    except Exception as e:
        st.error(f"❌ Error de Conexión/API: {e}")
        return {}

def generar_render_arquitectonico(ubicacion, estilo):
    """
    Genera una URL de una imagen usando IA generativa.
    """
    # Prompt en inglés para mejor calidad
    prompt = f"architectural render of a {estilo} house, located in {ubicacion}, sunny day, blue sky, cinematic lighting, 8k resolution, photorealistic, architectural photography"
    prompt_encoded = urllib.parse.quote(prompt)
    # API Gratuita Pollinations
    url_imagen = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1280&height=720&nologo=true&seed={datetime.datetime.now().microsecond}"
    return url_imagen

# ==========================================
# 📄 GENERADOR PDF
# ==========================================
class PDF(FPDF):
    def header(self):
        if os.path.exists(LOGOTIPO):
            try: self.image(LOGOTIPO, 10, 8, 33)
            except: pass
            self.ln(25)
        else:
            self.ln(10)
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'DOSIER DE VIABILIDAD - IA', 0, 1, 'R')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Informe generado el {datetime.date.today()}', 0, 0, 'C')

def generar_pdf(terreno, testigos, financiero, render_path=None):
    pdf = PDF()
    pdf.add_page()
    
    # PORTADA
    pdf.set_font('Arial', 'B', 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, f"  Proyecto: {terreno['nombre']}", 1, 1, 'L', fill=True)
    pdf.ln(5)

    # RENDER EN PORTADA
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
    pdf.cell(0, 10, f"ROI ANUALIZADO ({financiero['meses']} m): {financiero['roi_anual']:.2f}%", 0, 1)
    pdf.set_text_color(0, 0, 0)
    
    # TESTIGOS
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
        pdf.cell(0, 8, f"Comparable {i+1}: {p:,.0f} EUR ({m} m2) - {pm2:,.0f} EUR/m2", 1, 1, fill=True)
        
        if t.get('img_path') and os.path.exists(t['img_path']):
            try:
                pdf.image(t['img_path'], x=15, y=pdf.get_y()+2, w=50)
                pdf.ln(40)
            except: pass
        else:
            pdf.ln(2)

    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 📱 INTERFAZ PRINCIPAL
# ==========================================

st.title("🏗️ Calculadora Promotora IA")
st.caption("Versión con Depuración de Errores")
st.markdown("---")

# CONFIGURACIÓN LATERAL
with st.sidebar:
    if os.path.exists(LOGOTIPO): st.image(LOGOTIPO, width=150)
    st.header("⚙️ Configuración")
    meses_proyecto = st.slider("Duración (Meses)", 1, 12, 3)
    coste_const_m2 = st.number_input("Coste Const. (€/m²)", 1200)
    gastos_generales = st.slider("Soft Costs (%)", 5, 25, 15) / 100
    impuestos_compra = 0.10
    m2_objetivo = st.number_input("m² Construcción Objetivo", 180)
    estilo_casa = st.selectbox("Estilo Diseño", ["Moderno Mediterráneo", "Minimalista Cubico", "Clásico", "Industrial"])

# VARIABLES DE ESTADO (Para no perder datos al recargar)
if "suelo_data" not in st.session_state:
    st.session_state["suelo_data"] = {"precio": 100000.0, "nombre": "Parcela", "m2": 500.0, "render": None}

# --- ZONA 1: SUELO (COLUMNA IZQUIERDA) ---
c1, c2 = st.columns([1, 1.5])

with c1:
    st.subheader("1. Terreno / Solar")
    
    tab_m, tab_f = st.tabs(["✍️ Manual", "📸 Leer Cartel/Anuncio"])
    
    with tab_f:
        up_suelo = st.file_uploader("Sube foto del terreno", type=["jpg", "png", "jpeg"], key="u_suelo")
        if up_suelo:
            img_s = Image.open(up_suelo)
            if st.button("🧠 Analizar Foto Suelo"):
                datos = analizar_imagen_generico(img_s, "suelo")
                if datos:
                    st.session_state["suelo_data"]["precio"] = float(datos.get("precio", 0))
                    st.session_state["suelo_data"]["m2"] = float(datos.get("m2_suelo", 0))
                    ubi = datos.get("ubicacion", "")
                    if ubi: st.session_state["suelo_data"]["nombre"] = ubi
                    st.success("Datos actualizados!")
                else:
                    st.warning("No se pudo extraer JSON. Revisa el desplegable 'Depuración' arriba.")

    # Campos editables
    nombre_terreno = st.text_input("Ubicación", value=st.session_state["suelo_data"]["nombre"])
    precio_terreno = st.number_input("Precio Suelo (€)", value=st.session_state["suelo_data"]["precio"], step=1000.0)
    m2_parcela = st.number_input("m² Parcela", value=st.session_state["suelo_data"]["m2"], step=10.0)

    st.markdown("#### 🎨 Diseño Virtual")
    if st.button("✨ Generar Render (IA)"):
        with st.spinner("Generando imagen arquitectónica..."):
            try:
                url_render = generar_render_arquitectonico(nombre_terreno, estilo_casa)
                # Descargar imagen para PDF
                resp = requests.get(url_render)
                if resp.status_code == 200:
                    img_r = Image.open(BytesIO(resp.content))
                    img_r.save("render_temp.jpg")
                    st.session_state["suelo_data"]["render"] = "render_temp.jpg"
                    st.image(url_render, caption=f"Propuesta: {estilo_casa}")
                else:
                    st.error("Error descargando imagen.")
            except Exception as e:
                st.error(f"Error render: {e}")

# --- ZONA 2: TESTIGOS (COLUMNA DERECHA) ---
with c2:
    st.subheader("2. Comparables (Testigos)")
    lista_testigos = []
    
    for i in range(1, 4):
        with st.expander(f"🏠 Testigo {i}", expanded=False):
            cc_img, cc_dat = st.columns([1, 2])
            
            # SUBIDA
            up_t = cc_img.file_uploader("Foto", key=f"ut_{i}", label_visibility="collapsed")
            
            # ESTADO
            if f"dt_{i}" not in st.session_state: 
                st.session_state[f"dt_{i}"] = {"p":0.0, "m":0.0, "path":None}
            
            # PROCESO IA
            if up_t:
                img_t = Image.open(up_t)
                # Convertir a RGB y guardar temporal
                if img_t.mode != 'RGB': img_t = img_t.convert('RGB')
                path = f"temp_t_{i}.jpg"
                img_t.save(path)
                st.session_state[f"dt_{i}"]["path"] = path
                
                # Si precio es 0, intentar leer
                if st.session_state[f"dt_{i}"]["p"] == 0:
                    datos = analizar_imagen_generico(img_t, "testigo")
                    st.session_state[f"dt_{i}"]["p"] = float(datos.get("precio", 0))
                    st.session_state[f"dt_{i}"]["m"] = float(datos.get("m2", 0))

            # INPUTS
            with cc_dat:
                d = st.session_state[f"dt_{i}"]
                p = st.number_input("€", value=d["p"], key=f"p_{i}", step=1000.0)
                m = st.number_input("m2", value=d["m"], key=f"m_{i}", step=1.0)
                
                if p > 0:
                    lista_testigos.append({"precio":p, "m2":m, "img_path":d["path"]})

# --- CÁLCULO FINAL ---
st.markdown("---")
if st.button("ANALIZAR VIABILIDAD", type="primary", use_container_width=True):
    if not lista_testigos:
        st.error("⚠️ Faltan testigos. Añade al menos uno.")
    else:
        # 1. Media Mercado
        validos = [t for t in lista_testigos if t['m2'] > 0]
        if validos:
            media_m2 = sum([t['precio']/t['m2'] for t in validos])/len(validos)
            precio_venta = media_m2 * m2_objetivo
        else:
            # Fallback si no hay m2
            precio_venta = sum([t['precio'] for t in lista_testigos])/len(lista_testigos)
            media_m2 = 0

        # 2. Costes
        coste_suelo_total = precio_terreno * (1+impuestos_compra)
        coste_obra = coste_const_m2 * m2_objetivo
        soft_costs = (coste_suelo_total + coste_obra) * gastos_generales
        inversion = coste_suelo_total + coste_obra + soft_costs
        
        # 3. Rentabilidad
        beneficio = precio_venta - inversion
        roi = (beneficio/inversion)*100
        roi_anual = ((1+roi/100)**(12/meses_proyecto)-1)*100
        
        # 4. Resultados
        st.header("📊 Resultados del Estudio")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Precio Venta", f"{precio_venta:,.0f} €")
        c2.metric("Inversión Total", f"{inversion:,.0f} €")
        c3.metric("Beneficio Neto", f"{beneficio:,.0f} €")
        c4.metric("ROI Anualizado", f"{roi_anual:.2f} %")
        
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
                st.download_button("📄 DESCARGAR DOSIER COMPLETO", pdf_bytes, "dosier_ia.pdf", "application/pdf")
            else:
                st.error(f"❌ RIESGO ALTO (ROI {roi:.2f}%)")
        
        with col_chart:
            df_chart = pd.DataFrame({
                'Coste': ['Suelo', 'Obra', 'Soft', 'Beneficio'],
                'Valor': [coste_suelo_total, coste_obra, soft_costs, beneficio]
            })
            st.bar_chart(df_chart.set_index('Coste'))

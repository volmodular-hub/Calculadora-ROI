import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
import os
import json
import google.generativeai as genai
from PIL import Image
import urllib.parse # Para generar la URL del render

# ==========================================
# 🔐 CONFIGURACIÓN
# ==========================================
GOOGLE_API_KEY = "AIzaSyDAeL2GfyusB3w55sLur27b7t7I_rbETy4" # Tu clave
LOGOTIPO = "logo.png"

try:
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    st.error(f"Error API Key: {e}")

st.set_page_config(page_title="Promotora IA", layout="wide", page_icon="🏗️")

# ==========================================
# 🧠 CEREBRO IA (VISIÓN & RENDER)
# ==========================================

def analizar_imagen_generico(image, tipo="testigo"):
    """
    Analiza tanto testigos (casas) como suelos (terrenos).
    """
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    if tipo == "testigo":
        prompt = """
        Extrae en JSON: {"precio": (numero), "m2": (numero)}. 
        Si no está claro, pon 0. Solo JSON.
        """
    else: # TIPO SUELO
        prompt = """
        Analiza este anuncio de TERRENO. Extrae en JSON:
        1. "precio": Precio venta (solo numero).
        2. "ubicacion": Calle, zona o municipio que aparezca (texto corto).
        3. "m2_suelo": Metros cuadrados de la PARCELA (no edificabilidad).
        
        Ejemplo: {"precio": 150000, "ubicacion": "Urb. El Bosque", "m2_suelo": 800}
        Solo JSON.
        """
    
    try:
        response = model.generate_content([prompt, image])
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(clean_text)
    except:
        return {}

def generar_render_arquitectonico(ubicacion, estilo="moderno minimalista"):
    """
    Genera una URL de una imagen usando IA generativa gratuita.
    """
    prompt = f"hyperrealistic architectural render of a single storey {estilo} house, white facade, swimming pool, sunny day, located in {ubicacion}, 8k resolution, professional photography"
    prompt_encoded = urllib.parse.quote(prompt)
    # Usamos Pollinations.ai (API Gratuita excelente para pruebas)
    url_imagen = f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1024&height=768&nologo=true"
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
        self.cell(0, 10, 'ESTUDIO DE VIABILIDAD & DISEÑO', 0, 1, 'R')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Informe generado el {datetime.date.today()}', 0, 0, 'C')

def generar_pdf(terreno, testigos, financiero, render_path=None):
    pdf = PDF()
    pdf.add_page()
    
    # 1. PORTADA CON RENDER (Si existe)
    pdf.set_font('Arial', 'B', 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, f"  Proyecto: {terreno['nombre']}", 1, 1, 'L', fill=True)
    pdf.ln(5)

    if render_path and os.path.exists(render_path):
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 10, "PROPUESTA DE DISEÑO (RENDER IA)", 0, 1)
        try:
            pdf.image(render_path, x=15, y=pdf.get_y()+2, w=180) # Imagen grande
            pdf.ln(110) # Espacio para la imagen grande
        except:
            pdf.cell(0, 10, "(Error cargando render)", 0, 1)
    
    # 2. Resumen Financiero
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "RESUMEN FINANCIERO", 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f"Precio Suelo: {terreno['precio']:,.0f} EUR", 0, 1)
    pdf.cell(0, 8, f"Inversión Total: {financiero['inversion']:,.0f} EUR", 0, 1)
    pdf.cell(0, 8, f"Beneficio Neto: {financiero['beneficio']:,.0f} EUR", 0, 1)
    
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(39, 174, 96)
    pdf.cell(0, 10, f"ROI ANUALIZADO ({financiero['meses']} meses): {financiero['roi_anual']:.2f}%", 0, 1)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)

    # 3. Testigos (Nueva página si hace falta)
    if render_path: pdf.add_page()
    
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "COMPARABLES DE MERCADO", 0, 1)
    pdf.set_font('Arial', '', 10)
    
    for i, t in enumerate(testigos):
        precio = t['precio']
        m2 = t['m2']
        p_m2 = precio/m2 if m2>0 else 0
        pdf.set_fill_color(245, 245, 245)
        pdf.cell(0, 8, f"Testigo {i+1}: {precio:,.0f}€ ({m2}m2) - {p_m2:,.0f}€/m2", 1, 1, fill=True)
        
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

st.title("🏗️ Calculadora Promotora 360º")
st.markdown("---")

with st.sidebar:
    if os.path.exists(LOGOTIPO): st.image(LOGOTIPO, width=150)
    st.header("⚙️ Configuración")
    meses_proyecto = st.slider("Duración (Meses)", 1, 12, 3)
    coste_const_m2 = st.number_input("Coste Const. (€/m²)", 1200)
    gastos_generales = st.slider("Soft Costs (%)", 5, 25, 15) / 100
    impuestos_compra = 0.10
    m2_objetivo = st.number_input("m² Construcción", 180)
    estilo_casa = st.selectbox("Estilo Arquitectónico", ["Moderno Mediterráneo", "Minimalista Cubico", "Clásico Renovado", "Industrial"])

# --- ZONA 1: EL SUELO (Ahora con IA) ---
c1, c2 = st.columns([1, 1.5])

with c1:
    st.subheader("1. El Suelo")
    
    # Pestañas para elegir Manual o IA
    tab_manual, tab_foto = st.tabs(["✍️ Manual", "📸 Leer Foto"])
    
    # Variables de estado del suelo
    if "suelo_data" not in st.session_state:
        st.session_state["suelo_data"] = {"precio": 100000.0, "nombre": "Parcela", "render": None}

    with tab_foto:
        uploaded_suelo = st.file_uploader("Sube anuncio del terreno", type=["jpg","png"], key="up_suelo")
        if uploaded_suelo:
            img_suelo = Image.open(uploaded_suelo)
            if st.button("🧠 Extraer datos Suelo"):
                with st.spinner("Analizando terreno..."):
                    datos = analizar_imagen_generico(img_suelo, "suelo")
                    if datos:
                        st.session_state["suelo_data"]["precio"] = float(datos.get("precio", 0))
                        st.session_state["suelo_data"]["nombre"] = datos.get("ubicacion", "Parcela Detectada")
                        st.success("Datos extraídos!")
                    else:
                        st.error("No se detectaron datos.")

    # Inputs (se actualizan solos si la IA detecta algo)
    nombre_terreno = st.text_input("Ubicación", value=st.session_state["suelo_data"]["nombre"])
    precio_terreno = st.number_input("Precio Suelo (€)", value=st.session_state["suelo_data"]["precio"], step=1000.0)
    
    # --- BOTÓN DE RENDER ---
    st.markdown("#### 🎨 Diseño Virtual")
    if st.button("✨ Generar Render de la Casa"):
        with st.spinner("El arquitecto IA está dibujando..."):
            url_render = generar_render_arquitectonico(nombre_terreno, estilo_casa)
            # Descargamos la imagen para el PDF
            try:
                import requests
                from io import BytesIO
                resp = requests.get(url_render)
                img_render = Image.open(BytesIO(resp.content))
                img_render.save("render_temp.jpg")
                st.session_state["suelo_data"]["render"] = "render_temp.jpg"
                st.image(url_render, caption="Propuesta de Diseño Generada por IA")
            except:
                st.error("Error generando imagen.")

# --- ZONA 2: TESTIGOS (Igual que antes) ---
with c2:
    st.subheader("2. Mercado")
    lista_testigos = []
    for i in range(1, 4):
        with st.expander(f"🏠 Testigo {i}", expanded=False):
            c_img, c_dat = st.columns([1,2])
            up_testigo = c_img.file_uploader("Captura", key=f"t_{i}", label_visibility="collapsed")
            
            if f"dt_{i}" not in st.session_state: st.session_state[f"dt_{i}"] = {"p":0.0, "m":0.0, "path":None}
            
            if up_testigo:
                img = Image.open(up_testigo)
                path = f"temp_t_{i}.jpg"
                if img.mode != 'RGB': img = img.convert('RGB')
                img.save(path)
                st.session_state[f"dt_{i}"]["path"] = path
                
                if st.session_state[f"dt_{i}"]["p"] == 0:
                    datos = analizar_imagen_generico(img, "testigo")
                    st.session_state[f"dt_{i}"]["p"] = float(datos.get("precio", 0))
                    st.session_state[f"dt_{i}"]["m"] = float(datos.get("m2", 0))

            with c_dat:
                d = st.session_state[f"dt_{i}"]
                p = st.number_input("€", d["p"], key=f"p_{i}")
                m = st.number_input("m2", d["m"], key=f"m_{i}")
                if p > 0: lista_testigos.append({"precio":p, "m2":m, "img_path":d["path"]})

# --- CÁLCULOS ---
st.markdown("---")
if st.button("ANALIZAR OPERACIÓN", type="primary", use_container_width=True):
    if not lista_testigos:
        st.error("Faltan testigos.")
    else:
        # Lógica financiera
        media_m2 = sum([t['precio']/t['m2'] for t in lista_testigos if t['m2']>0])/len(lista_testigos)
        precio_venta = media_m2 * m2_objetivo
        
        coste_suelo = precio_terreno * (1+impuestos_compra)
        coste_obra = coste_const_m2 * m2_objetivo
        soft_costs = (coste_suelo + coste_obra) * gastos_generales
        inversion = coste_suelo + coste_obra + soft_costs
        
        beneficio = precio_venta - inversion
        roi = (beneficio/inversion)*100
        roi_anual = ((1+roi/100)**(12/meses_proyecto)-1)*100
        
        # Resultados
        st.header("📊 Resultados")
        c1, c2, c3 = st.columns(3)
        c1.metric("Beneficio", f"{beneficio:,.0f}€")
        c2.metric("ROI Operación", f"{roi:.2f}%")
        c3.metric("ROI Anualizado", f"{roi_anual:.2f}%")
        
        if roi > 20:
            st.success("✅ PROYECTO VIABLE")
            pdf_bytes = generar_pdf(
                {"nombre": nombre_terreno, "precio": precio_terreno},
                lista_testigos,
                {"inversion": inversion, "beneficio": beneficio, "roi": roi, "roi_anual": roi_anual, "meses": meses_proyecto},
                render_path=st.session_state["suelo_data"]["render"]
            )
            st.download_button("📄 DESCARGAR DOSIER CON RENDER", pdf_bytes, "dosier.pdf", "application/pdf")
        else:
            st.error("❌ RIESGO ALTO")

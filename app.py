import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
import os
from PIL import Image
import requests
from io import BytesIO
import urllib.parse

# ==========================================
# ⚙️ CONFIGURACIÓN
# ==========================================
LOGOTIPO = "logo.png"
st.set_page_config(page_title="Promotora Pro", layout="wide", page_icon="🏗️")

# ==========================================
# 📄 GENERADOR DE PDF PROFESIONAL
# ==========================================
class PDF(FPDF):
    def header(self):
        # Logo
        if os.path.exists(LOGOTIPO):
            try: self.image(LOGOTIPO, 10, 8, 33)
            except: pass
            self.ln(25)
        else:
            self.ln(10)
        
        # Título
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'DOSIER DE VIABILIDAD INMOBILIARIA', 0, 1, 'R')
        self.line(10, 35, 200, 35) # Línea separadora
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Informe generado el {datetime.date.today()} | Uso Interno', 0, 0, 'C')

def generar_pdf(datos_suelo, testigos, financiero):
    pdf = PDF()
    pdf.add_page()
    
    # --- 1. DATOS DEL PROYECTO ---
    pdf.set_font('Arial', 'B', 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, f"  PROYECTO: {datos_suelo['nombre']}", 1, 1, 'L', fill=True)
    pdf.ln(5)

    # Imagen del Terreno (Si existe)
    if datos_suelo.get('img_path') and os.path.exists(datos_suelo['img_path']):
        try:
            # Centramos la imagen
            pdf.image(datos_suelo['img_path'], x=15, y=pdf.get_y(), w=180, h=100)
            pdf.ln(105) # Dejamos espacio vertical
        except: pass
    
    # --- 2. RESUMEN EJECUTIVO (FINANZAS) ---
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "RESUMEN EJECUTIVO", 0, 1)
    
    # Tabla simple de datos
    pdf.set_font('Arial', '', 11)
    pdf.cell(95, 8, f"Precio Suelo: {datos_suelo['precio']:,.0f} EUR", 1)
    pdf.cell(95, 8, f"Metros Parcela: {datos_suelo['m2']:,.0f} m2", 1, 1)
    
    pdf.cell(95, 8, f"Inversión Total: {financiero['inversion']:,.0f} EUR", 1)
    pdf.cell(95, 8, f"Ventas Estimadas: {financiero['ventas']:,.0f} EUR", 1, 1)
    
    pdf.set_fill_color(220, 255, 220) # Verde claro
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(95, 12, f"BENEFICIO: {financiero['beneficio']:,.0f} EUR", 1, 0, fill=True)
    
    # ROI DESTACADO
    roi = financiero['roi']
    pdf.set_text_color(0, 100, 0) if roi > 0 else pdf.set_text_color(200, 0, 0)
    pdf.cell(95, 12, f"ROI: {roi:.2f}% (Anual: {financiero['roi_anual']:.2f}%)", 1, 1, fill=True)
    pdf.set_text_color(0, 0, 0)
    
    # --- 3. ESTUDIO DE MERCADO (IMÁGENES) ---
    pdf.add_page()
    pdf.set_font('Arial', 'B', 14)
    pdf.cell(0, 10, "COMPARABLES DE MERCADO (TESTIGOS)", 0, 1)
    pdf.ln(5)
    
    pdf.set_font('Arial', '', 10)
    
    for i, t in enumerate(testigos):
        # Datos del testigo
        precio = t['precio']
        m2 = t['m2']
        p_m2 = precio/m2 if m2 > 0 else 0
        
        # Encabezado gris
        pdf.set_fill_color(230, 230, 230)
        pdf.set_font('Arial', 'B', 11)
        texto_titulo = f"TESTIGO {i+1} | {precio:,.0f} EUR | {m2} m2 | {p_m2:,.0f} EUR/m2"
        pdf.cell(0, 8, texto_titulo, 1, 1, fill=True)
        
        # Foto del testigo
        if t.get('img_path') and os.path.exists(t['img_path']):
            try:
                # Calculamos posición
                y_actual = pdf.get_y()
                # Ponemos la foto (tamaño mediano)
                pdf.image(t['img_path'], x=20, y=y_actual+2, w=80)
                # Notas al lado de la foto (Opcional)
                pdf.set_xy(110, y_actual + 10)
                pdf.multi_cell(0, 5, "Comparable seleccionado en la zona para estimación de precio de salida.")
                
                pdf.ln(55) # Espacio para la siguiente foto
            except:
                pdf.ln(5)
        else:
            pdf.ln(5)
        
        pdf.ln(5) # Separador entre testigos

    return pdf.output(dest='S').encode('latin-1')

# ==========================================
# 🎨 FUNCIÓN RENDER (EXTRA VISUAL)
# ==========================================
def generar_render(ubicacion, estilo):
    """Genera una imagen conceptual gratis sin API Key"""
    prompt = f"architectural render of a {estilo} house, located in {ubicacion}, sunny day, blue sky, cinematic lighting, 8k"
    prompt_encoded = urllib.parse.quote(prompt)
    return f"https://image.pollinations.ai/prompt/{prompt_encoded}?width=1024&height=768&nologo=true&seed={datetime.datetime.now().microsecond}"

# ==========================================
# 📱 INTERFAZ DE USUARIO (STREAMLIT)
# ==========================================
st.title("🏗️ Calculadora Promotora (Manual & Visual)")
st.caption("Introduce los datos y sube las fotos para generar el dosier.")
st.markdown("---")

# --- BARRA LATERAL ---
with st.sidebar:
    if os.path.exists(LOGOTIPO): st.image(LOGOTIPO, width=150)
    st.header("⚙️ Configuración Modelo")
    
    meses_proyecto = st.slider("Duración Proyecto (Meses)", 1, 18, 3)
    coste_const_m2 = st.number_input("Coste Construcción (€/m²)", value=1200, step=50)
    gastos_generales_pct = st.slider("Gastos Generales/Soft (%)", 5, 25, 15) / 100
    impuestos_compra = 0.10
    m2_objetivo = st.number_input("m² Vivienda a Construir", value=180)
    estilo_render = st.selectbox("Estilo Arquitectónico", ["Moderno Mediterráneo", "Minimalista Cúbico", "Clásico", "Industrial"])

# --- VARIABLES DE SESIÓN (Para guardar las fotos al recargar) ---
if "suelo_img" not in st.session_state: st.session_state["suelo_img"] = None
if "render_img" not in st.session_state: st.session_state["render_img"] = None
# Inicializamos diccionario para testigos si no existe
for i in range(1, 4):
    if f"t{i}_img" not in st.session_state: st.session_state[f"t{i}_img"] = None

# --- COLUMNA 1: DATOS DEL TERRENO ---
c1, c2 = st.columns([1, 1])

with c1:
    st.subheader("1. El Terreno")
    nombre_terreno = st.text_input("📍 Ubicación / Nombre", "Parcela Ejemplo")
    col_p, col_m = st.columns(2)
    precio_terreno = col_p.number_input("💰 Precio (€)", value=100000, step=1000)
    m2_parcela = col_m.number_input("📐 m² Parcela", value=500, step=10)
    
    # SUBIDA DE FOTO TERRENO
    uploaded_suelo = st.file_uploader("📸 Subir Foto del Terreno", type=["jpg", "png", "jpeg"])
    if uploaded_suelo:
        # Guardamos la imagen localmente para el PDF
        img = Image.open(uploaded_suelo)
        if img.mode != 'RGB': img = img.convert('RGB') # Convertir para evitar errores PDF
        img.save("temp_suelo.jpg")
        st.session_state["suelo_img"] = "temp_suelo.jpg"
        st.image(img, caption="Imagen cargada", use_column_width=True)
    
    # GENERADOR DE RENDER (Opcional)
    st.write("---")
    st.markdown("**🎨 Visualización IA (Opcional)**")
    if st.button("✨ Generar Propuesta Visual"):
        with st.spinner("El arquitecto virtual está dibujando..."):
            url = generar_render(nombre_terreno, estilo_render)
            # Descargamos
            resp = requests.get(url)
            if resp.status_code == 200:
                img_r = Image.open(BytesIO(resp.content))
                img_r.save("temp_render.jpg")
                st.session_state["render_img"] = "temp_render.jpg"
                st.image(img_r, caption="Render generado", use_column_width=True)

# --- COLUMNA 2: COMPARABLES ---
with c2:
    st.subheader("2. Comparables de Mercado")
    lista_testigos = []
    
    # Bucle para 3 testigos
    for i in range(1, 4):
        with st.expander(f"🏠 Testigo {i}", expanded=True):
            cols_input = st.columns([1, 1])
            p = cols_input[0].number_input(f"Precio T{i} (€)", value=0, step=1000)
            m = cols_input[1].number_input(f"Metros T{i}", value=0, step=1)
            
            # Subida de foto individual
            up_t = st.file_uploader(f"Foto T{i}", type=["jpg", "png", "jpeg"], key=f"up_{i}")
            
            path_img = None
            if up_t:
                img_t = Image.open(up_t)
                if img_t.mode != 'RGB': img_t = img_t.convert('RGB')
                path_save = f"temp_t{i}.jpg"
                img_t.save(path_save)
                st.session_state[f"t{i}_img"] = path_save
                st.image(img_t, width=150)
                path_img = path_save
            
            # Guardamos datos si hay precio
            if p > 0:
                lista_testigos.append({
                    "precio": p,
                    "m2": m,
                    "img_path": path_img
                })

# --- CÁLCULOS Y RESULTADOS ---
st.markdown("---")
if st.button("🚀 ANALIZAR Y GENERAR DOSIER", type="primary", use_container_width=True):
    
    # 1. Validaciones
    if not lista_testigos:
        st.error("⚠️ Por favor, añade al menos 1 testigo con precio para calcular el mercado.")
    else:
        # 2. Cálculos Financieros
        # Precio medio m2 zona
        validos = [t for t in lista_testigos if t['m2'] > 0]
        if validos:
            media_m2_zona = sum([t['precio']/t['m2'] for t in validos]) / len(validos)
            ventas_estimadas = media_m2_zona * m2_objetivo
        else:
            # Si no ponen m2, usamos la media de precios totales (menos preciso)
            ventas_estimadas = sum([t['precio'] for t in lista_testigos]) / len(lista_testigos)
            media_m2_zona = 0

        # Costes
        coste_suelo_total = precio_terreno * (1 + impuestos_compra)
        coste_obra_total = coste_const_m2 * m2_objetivo
        gastos_soft_total = (coste_suelo_total + coste_obra_total) * gastos_generales_pct
        
        inversion_total = coste_suelo_total + coste_obra_total + gastos_soft_total
        
        beneficio = ventas_estimadas - inversion_total
        roi = (beneficio / inversion_total) * 100
        # Fórmula ROI Anualizado: ((1 + ROI_total)^(12/meses) - 1)
        roi_anual = ((1 + roi/100)**(12/meses_proyecto) - 1) * 100
        
        # 3. Mostrar Resultados en Pantalla
        st.success("✅ Análisis Completado")
        
        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Inversión Total", f"{inversion_total:,.0f} €")
        col2.metric("Ventas Estimadas", f"{ventas_estimadas:,.0f} €")
        col3.metric("Beneficio Neto", f"{beneficio:,.0f} €")
        col4.metric("ROI ANUALIZADO", f"{roi_anual:.2f} %", delta_color="normal")
        
        # Gráfica rápida
        st.caption("Desglose de la operación:")
        chart_data = pd.DataFrame({
            "Categoría": ["Suelo+Imp", "Construcción", "Gastos Soft", "Beneficio"],
            "Euros": [coste_suelo_total, coste_obra_total, gastos_soft_total, beneficio]
        })
        st.bar_chart(chart_data.set_index("Categoría"))

        # 4. Generar PDF
        # Si hemos generado un render, lo usamos como imagen principal, si no, la foto del suelo
        img_principal = st.session_state["render_img"] if st.session_state["render_img"] else st.session_state["suelo_img"]
        
        datos_suelo_pdf = {
            "nombre": nombre_terreno,
            "precio": precio_terreno,
            "m2": m2_parcela,
            "img_path": img_principal
        }
        
        datos_financieros_pdf = {
            "inversion": inversion_total,
            "ventas": ventas_estimadas,
            "beneficio": beneficio,
            "roi": roi,
            "roi_anual": roi_anual
        }
        
        pdf_bytes = generar_pdf(datos_suelo_pdf, lista_testigos, datos_financieros_pdf)
        
        st.download_button(
            label="📄 DESCARGAR DOSIER PDF PROFESIONAL",
            data=pdf_bytes,
            file_name="Dosier_Viabilidad.pdf",
            mime="application/pdf",
            use_container_width=True
        )

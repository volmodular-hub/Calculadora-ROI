import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
import os
import re
import cloudscraper
from bs4 import BeautifulSoup

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Calculadora ROI Pro", layout="wide", page_icon="🏗️")
LOGOTIPO = "logo.png"

# --- ESTILOS CSS ---
st.markdown("""
<style>
    .big-font { font-size:24px !important; color: #2E86C1; font-weight: bold; }
    .success-box { padding: 15px; background-color: #D4EFDF; border-radius: 10px; border-left: 5px solid #27AE60; }
    .metric-container { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- FUNCIÓN DE SCRAPING (ANTIBOT) ---
def extraer_datos_inmueble(url):
    """
    Intenta extraer datos saltándose la protección de Cloudflare usando CloudScraper.
    """
    datos = {"precio": 0.0, "m2": 0.0, "imagen": None, "titulo": "Desconocido"}
    
    if not url: return datos
    
    try:
        # Usamos un scraper que simula ser Chrome para evitar error 403
        scraper = cloudscraper.create_scraper(browser='chrome')
        response = scraper.get(url)
        
        if response.status_code != 200:
            st.toast(f"🔒 Web protegida ({response.status_code}). Introduce datos manualmente.", icon="⚠️")
            return datos

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. Metadatos (OpenGraph) - Suelen ser más fáciles de leer
        og_title = soup.find("meta", property="og:title")
        og_image = soup.find("meta", property="og:image")
        og_desc = soup.find("meta", property="og:description")
        
        if og_title: datos["titulo"] = og_title["content"]
        if og_image: datos["imagen"] = og_image["content"]

        # Texto completo para buscar
        texto_busqueda = (datos["titulo"] + " " + (og_desc["content"] if og_desc else "")).lower()
        
        # 2. Extracción de PRECIO con Regex
        # Quitamos puntos de miles (ej: 350.000 -> 350000) para facilitar la búsqueda
        texto_limpio = texto_busqueda.replace(".", "")
        
        # Busca números seguidos de € o eur
        match_precio = re.search(r'(\d{5,8})\s?(€|eur)', texto_limpio)
        if match_precio:
            datos["precio"] = float(match_precio.group(1))

        # 3. Extracción de M2 con Regex
        # Busca números seguidos de m2 o m²
        match_m2 = re.search(r'(\d{2,4})\s?(m2|m²)', texto_busqueda)
        if match_m2:
            datos["m2"] = float(match_m2.group(1))
            
    except Exception as e:
        print(f"Error scraping: {e}")
        st.toast("Error de lectura. Rellena manual.", icon="✍️")
    
    return datos

# --- CLASE PDF ---
class PDF(FPDF):
    def header(self):
        if os.path.exists(LOGOTIPO):
            self.image(LOGOTIPO, 10, 8, 33)
            self.ln(25)
        else:
            self.ln(10)
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'DOSIER DE VIABILIDAD - AUTOMATIZADO', 0, 1, 'R')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Generado el {datetime.date.today()}', 0, 0, 'C')

def generar_pdf(terreno, testigos, financiero):
    pdf = PDF()
    pdf.add_page()
    
    # Datos del Proyecto
    pdf.set_font('Arial', 'B', 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, f"  Proyecto: {terreno['nombre']}", 1, 1, 'L', fill=True)
    pdf.ln(5)

    # Resumen Ejecutivo
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "RESUMEN EJECUTIVO", 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f"Inversión Total: {financiero['inversion']:,.2f} EUR", 0, 1)
    pdf.cell(0, 8, f"Beneficio Neto: {financiero['beneficio']:,.2f} EUR", 0, 1)
    
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(39, 174, 96)
    pdf.cell(0, 10, f"ROI PROYECTADO: {financiero['roi']:.2f}%", 0, 1)
    pdf.cell(0, 10, f"ROI ANUALIZADO ({financiero['meses']} meses): {financiero['roi_anual']:.2f}%", 0, 1)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    
    # Tabla Testigos
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 10, "Comparables (Datos de Mercado)", 0, 1)
    pdf.set_font('Arial', '', 9)
    
    col_w = 63
    pdf.cell(col_w, 8, "Testigo / Fuente", 1)
    pdf.cell(col_w, 8, "Precio Venta", 1)
    pdf.cell(col_w, 8, "Precio m2", 1)
    pdf.ln()
    
    for i, t in enumerate(testigos):
        precio = t['precio']
        m2 = t['m2']
        precio_m2 = precio / m2 if m2 > 0 else 0
        
        pdf.cell(col_w, 8, f"Comparable {i+1}", 1)
        pdf.cell(col_w, 8, f"{precio:,.0f} EUR", 1)
        pdf.cell(col_w, 8, f"{precio_m2:,.0f} EUR/m2", 1)
        pdf.ln()

    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ PRINCIPAL ---

st.title("🚀 Analizador Inmobiliario IA")
st.markdown("---")

# BARRA LATERAL
with st.sidebar:
    if os.path.exists(LOGOTIPO): st.image(LOGOTIPO, width=150)
    st.header("⚙️ Configuración")
    meses_proyecto = st.slider("Duración (Meses)", 1, 12, 3)
    coste_const_m2 = st.number_input("Coste Const. (€/m²)", 1200)
    gastos_generales = st.slider("Soft Costs (%)", 5, 25, 15) / 100
    impuestos_compra = st.number_input("Impuestos Compra (%)", 10) / 100
    m2_objetivo = st.number_input("m² Construcción Objetivo", 180)

# COLUMNAS PRINCIPALES
c1, c2 = st.columns([1, 1.5])

# 1. DATOS DEL TERRENO
with c1:
    st.subheader("1. Terreno")
    nombre_terreno = st.text_input("📍 Ubicación", "Parcela Ejemplo")
    precio_terreno = st.number_input("💰 Precio Suelo (€)", value=100000, step=1000)

# 2. DATOS DE MERCADO (SCRAPER)
with c2:
    st.subheader("2. Investigación de Mercado (URLs)")
    st.info("Pega URLs de Idealista/Fotocasa/Habitaclia")
    
    lista_testigos_final = []
    
    # Creamos 3 bloques para testigos
    for i in range(1, 4):
        with st.expander(f"🏠 Testigo {i}", expanded=True):
            col_url, col_btn = st.columns([3, 1])
            url_input = col_url.text_input(f"URL Anuncio {i}", key=f"url_{i}")
            
            # Inicializar estado si no existe
            if f"data_{i}" not in st.session_state:
                st.session_state[f"data_{i}"] = {"precio": 0.0, "m2": 0.0, "img": None}
            
            # Botón Extraer
            if col_btn.button("🔍 Extraer", key=f"btn_{i}"):
                with st.spinner("Analizando web..."):
                    datos = extraer_datos_inmueble(url_input)
                    # Guardamos en sesión
                    st.session_state[f"data_{i}"] = {
                        "precio": datos["precio"],
                        "m2": datos["m2"],
                        "img": datos["imagen"]
                    }
                    if datos["precio"] == 0:
                        st.warning("No se detectó precio. Introdúcelo manual.")
            
            # Recuperar datos de sesión
            d = st.session_state[f"data_{i}"]
            
            if d["img"]:
                st.image(d["img"], width=100)
            
            # Inputs editables (Clave para corregir errores del robot)
            c_p, c_m = st.columns(2)
            p_val = c_p.number_input(f"Precio (€)", value=d["precio"], key=f"p_{i}", step=1000.0)
            m_val = c_m.number_input(f"Metros (m²)", value=d["m2"], key=f"m_{i}", step=1.0)
            
            if p_val > 0:
                lista_testigos_final.append({"precio": p_val, "m2": m_val})

st.markdown("---")

# CÁLCULOS FINALES
if st.button("ANALIZAR VIABILIDAD", type="primary", use_container_width=True):
    
    if len(lista_testigos_final) == 0:
        st.error("⚠️ Añade al menos 1 testigo con precio válido.")
    else:
        # Calcular media de m2 de la zona
        suma_precio_m2 = 0
        validos = 0
        for t in lista_testigos_final:
            if t['m2'] > 0:
                suma_precio_m2 += (t['precio'] / t['m2'])
                validos += 1
        
        if validos > 0:
            precio_m2_zona = suma_precio_m2 / validos
            precio_venta_estimado = precio_m2_zona * m2_objetivo
        else:
            # Fallback si no hay metros: media simple de precios
            precio_venta_estimado = sum([t['precio'] for t in lista_testigos_final]) / len(lista_testigos_final)
            precio_m2_zona = 0
            
        # Costes
        coste_obra = coste_const_m2 * m2_objetivo
        coste_suelo_total = precio_terreno * (1 + impuestos_compra)
        gastos_soft_total = (coste_obra + coste_suelo_total) * gastos_generales
        inversion_total = coste_suelo_total + coste_obra + gastos_soft_total
        
        # Resultados Financieros
        beneficio = precio_venta_estimado - inversion_total
        roi = (beneficio / inversion_total) * 100
        roi_anual = ((1 + (roi/100)) ** (12/meses_proyecto) - 1) * 100
        
        # MOSTRAR RESULTADOS
        st.header("📊 Resultados del Análisis")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Precio Venta Estimado", f"{precio_venta_estimado:,.0f} €", f"{precio_m2_zona:,.0f} €/m²")
        c2.metric("Inversión Total", f"{inversion_total:,.0f} €")
        c3.metric("Beneficio Neto", f"{beneficio:,.0f} €")
        c4.metric("ROI Anualizado", f"{roi_anual:.1f} %")
        
        st.divider()
        
        col_veredicto, col_graf = st.columns([2, 1])
        
        with col_veredicto:
            if roi > 20:
                st.markdown('<div class="success-box">', unsafe_allow_html=True)
                st.subheader("✅ LUZ VERDE: PROYECTO VIABLE")
                st.write(f"Con un ROI por operación del {roi:.2f}% y una rotación de {meses_proyecto} meses.")
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Generar PDF
                pdf_bytes = generar_pdf(
                    {"nombre": nombre_terreno},
                    lista_testigos_final,
                    {"inversion": inversion_total, "beneficio": beneficio, "roi": roi, "roi_anual": roi_anual, "meses": meses_proyecto}
                )
                st.download_button("📄 DESCARGAR DOSIER PDF", pdf_bytes, "dosier_inversion.pdf", "application/pdf")
            else:
                st.error(f"❌ RIESGO ALTO (ROI {roi:.2f}%)")
                st.write("El margen no justifica el riesgo. Intenta negociar el suelo.")

        with col_graf:
            datos_graf = pd.DataFrame({
                'Coste': ['Suelo', 'Obra', 'Soft', 'Beneficio'],
                'Valor': [coste_suelo_total, coste_obra, gastos_soft_total, beneficio]
            })
            st.bar_chart(datos_graf.set_index('Coste'))

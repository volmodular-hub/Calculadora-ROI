import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
import os
import requests
from bs4 import BeautifulSoup
import re

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Calculadora ROI Pro", layout="wide", page_icon="🏗️")
LOGOTIPO = "logo.png" 

# --- FUNCIONES DE SCRAPING (LA MAGIA) ---
def extraer_datos_inmueble(url):
    """
    Intenta extraer precio, m2 e imagen de una URL inmobiliaria.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept-Language': 'es-ES,es;q=0.9',
    }
    
    datos = {"precio": 0.0, "m2": 0.0, "imagen": None, "titulo": "Desconocido"}
    
    try:
        if not url: return datos
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code != 200:
            st.toast(f"⚠️ No se pudo acceder a la web (Bloqueo o Error {response.status_code})")
            return datos

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. Título (Suele tener el resumen)
        # Intentamos sacar OpenGraph description o Title
        og_title = soup.find("meta", property="og:title")
        og_desc = soup.find("meta", property="og:description")
        
        titulo_texto = ""
        if og_title: titulo_texto += og_title["content"]
        if og_desc: titulo_texto += " " + og_desc["content"]
        
        datos["titulo"] = titulo_texto if titulo_texto else soup.title.string

        # 2. Imagen Principal
        og_image = soup.find("meta", property="og:image")
        if og_image:
            datos["imagen"] = og_image["content"]

        # 3. Extracción con Regex (Busca patrones de números)
        # Buscar Precio (ej: 350.000 €)
        # Quitamos puntos para facilitar la búsqueda
        texto_limpio = titulo_texto.replace(".", "")
        match_precio = re.search(r'(\d{3,7})\s?€', texto_limpio)
        if match_precio:
            datos["precio"] = float(match_precio.group(1))

        # Buscar Metros (ej: 180 m2)
        match_m2 = re.search(r'(\d{2,4})\s?(m2|m²)', titulo_texto.lower())
        if match_m2:
            datos["m2"] = float(match_m2.group(1))

    except Exception as e:
        st.error(f"Error analizando URL: {e}")
    
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
    
    # ... (Resto del código del PDF igual que antes) ...
    # Simplemente adaptaremos la tabla de testigos más abajo
    
    pdf.set_font('Arial', 'B', 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, f"  Proyecto: {terreno['nombre']}", 1, 1, 'L', fill=True)
    pdf.ln(5)

    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "RESUMEN EJECUTIVO", 0, 1)
    pdf.set_font('Arial', '', 11)
    pdf.cell(0, 8, f"Inversión Total: {financiero['inversion']:,.2f} EUR", 0, 1)
    pdf.cell(0, 8, f"Beneficio Neto: {financiero['beneficio']:,.2f} EUR", 0, 1)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"ROI PROYECTADO: {financiero['roi']:.2f}%", 0, 1)
    pdf.cell(0, 10, f"ROI ANUALIZADO: {financiero['roi_anual']:.2f}%", 0, 1)
    pdf.ln(5)
    
    # Tabla Testigos con URLs
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 10, "Comparables (Datos extraídos de anuncios)", 0, 1)
    pdf.set_font('Arial', '', 9)
    
    for i, t in enumerate(testigos):
        precio = t['precio']
        m2 = t['m2']
        precio_m2 = precio / m2 if m2 > 0 else 0
        texto = f"Testigo {i+1}: {precio:,.0f}€ | {m2} m2 | {precio_m2:,.0f} €/m2"
        pdf.cell(0, 8, texto, 1, 1)
        # Si quisiéramos poner el link en el PDF:
        # pdf.cell(0, 5, t['url'], 0, 1, link=t['url'])

    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ PRINCIPAL ---

st.title("🚀 Analizador Inmobiliario con IA")
st.markdown("---")

with st.sidebar:
    if os.path.exists(LOGOTIPO): st.image(LOGOTIPO, width=150)
    st.header("⚙️ Configuración")
    meses_proyecto = st.slider("Duración (Meses)", 1, 12, 3)
    coste_const_m2 = st.number_input("Coste Const. (€/m²)", 1200)
    gastos_generales = 0.15
    impuestos_compra = 0.10
    m2_objetivo = st.number_input("m² Construcción Objetivo", 180)

# 1. COLUMNA IZQUIERDA: EL SUELO
c1, c2 = st.columns([1, 1.5]) # Hacemos la derecha un poco más ancha

with c1:
    st.subheader("1. Terreno")
    nombre_terreno = st.text_input("📍 Ubicación", "Parcela Ejemplo")
    precio_terreno = st.number_input("💰 Precio Suelo (€)", value=100000, step=1000)

# 2. COLUMNA DERECHA: LOS TESTIGOS CON URL
with c2:
    st.subheader("2. Investigación de Mercado (URLs)")
    st.info("Pega los enlaces de Idealista/Fotocasa/Habitaclia")
    
    lista_testigos_final = []
    
    # Creamos 3 bloques para 3 testigos
    for i in range(1, 4):
        with st.expander(f"🏠 Testigo {i}", expanded=True):
            col_url, col_btn = st.columns([3, 1])
            url_input = col_url.text_input(f"URL Anuncio {i}", key=f"url_{i}")
            
            # Variables de estado para guardar lo scrapreado
            if f"data_{i}" not in st.session_state:
                st.session_state[f"data_{i}"] = {"precio": 0.0, "m2": 0.0, "img": None}
            
            # Botón de extracción
            if col_btn.button("🔍 Extraer", key=f"btn_{i}"):
                with st.spinner("Analizando web..."):
                    datos = extraer_datos_inmueble(url_input)
                    st.session_state[f"data_{i}"] = {
                        "precio": datos["precio"],
                        "m2": datos["m2"],
                        "img": datos["imagen"]
                    }
            
            # Mostrar datos (Editables por si falla el scraper)
            d = st.session_state[f"data_{i}"]
            
            # Si hay imagen, la mostramos en pequeñito
            if d["img"]:
                st.image(d["img"], width=150)
            
            c_p, c_m = st.columns(2)
            p_val = c_p.number_input(f"Precio (€)", value=d["precio"], key=f"p_{i}")
            m_val = c_m.number_input(f"Metros (m²)", value=d["m2"], key=f"m_{i}")
            
            if p_val > 0:
                lista_testigos_final.append({"precio": p_val, "m2": m_val, "url": url_input})

st.markdown("---")

# CÁLCULOS FINALES
if st.button("ANALIZAR VIABILIDAD", type="primary", use_container_width=True):
    
    if len(lista_testigos_final) == 0:
        st.error("⚠️ Por favor, añade al menos 1 testigo con precio válido.")
    else:
        # Calcular media de los testigos
        media_precios = sum([t['precio'] for t in lista_testigos_final]) / len(lista_testigos_final)
        
        # Ajustamos el precio de venta a nuestros m2 objetivo
        # (Precio medio / m2 medio de testigos) * Nuestros m2
        # Pero para simplificar, usaremos el precio total medio de la zona si son casas similares
        # O mejor: Sacamos el precio/m2 de la zona
        
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
            precio_venta_estimado = media_precios # Fallback
            
        # Costes
        coste_obra = coste_const_m2 * m2_objetivo
        coste_suelo_total = precio_terreno * (1 + impuestos_compra)
        gastos_soft_total = (coste_obra + coste_suelo_total) * gastos_generales
        inversion_total = coste_suelo_total + coste_obra + gastos_soft_total
        
        beneficio = precio_venta_estimado - inversion_total
        roi = (beneficio / inversion_total) * 100
        roi_anual = ((1 + (roi/100)) ** (12/meses_proyecto) - 1) * 100
        
        # RESULTADOS
        st.header("📊 Resultados")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Precio m² Zona", f"{precio_m2_zona:,.0f} €/m²")
        c2.metric("Precio Venta Estimado", f"{precio_venta_estimado:,.0f} €")
        c3.metric("Beneficio Neto", f"{beneficio:,.0f} €")
        c4.metric("ROI Anualizado", f"{roi_anual:.1f} %")
        
        if roi > 20:
            st.success("✅ PROYECTO VIABLE")
            
            # Generar PDF
            pdf_bytes = generar_pdf(
                {"nombre": nombre_terreno},
                lista_testigos_final,
                {"inversion": inversion_total, "beneficio": beneficio, "roi": roi, "roi_anual": roi_anual}
            )
            st.download_button("📄 DESCARGAR DOSIER", pdf_bytes, "dosier.pdf", "application/pdf")
        else:
            st.error("❌ RIESGO ALTO")

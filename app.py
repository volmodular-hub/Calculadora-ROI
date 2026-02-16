import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
import os

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Calculadora Viabilidad Express", layout="wide", page_icon="🏗️")
LOGOTIPO = "logo.png"  # Nombre exacto de tu archivo

# --- ESTILOS CSS ---
st.markdown("""
<style>
    .big-font { font-size:24px !important; color: #2E86C1; font-weight: bold; }
    .success-box { padding: 15px; background-color: #D4EFDF; border-radius: 10px; border-left: 5px solid #27AE60; }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN LATERAL ---
with st.sidebar:
    # 1. AQUÍ PONEMOS EL LOGO EN LA PANTALLA
    if os.path.exists(LOGOTIPO):
        st.image(LOGOTIPO, width=200) # Ajusta el ancho si sale muy grande
    else:
        st.header("🏢 TU EMPRESA")
        st.warning(f"Sube un archivo llamado '{LOGOTIPO}' a la carpeta para ver tu logo aquí.")
    
    st.divider()
    st.header("⚙️ Tu Modelo Constructivo")
    meses_proyecto = st.slider("Duración del Proyecto (Meses)", 1, 12, 3)
    coste_const_m2 = st.number_input("Coste Construcción (€/m²)", value=1200, step=50)
    gastos_generales = st.slider("Soft Costs / Gastos Generales (%)", 5, 25, 15) / 100
    impuestos_compra = st.number_input("Impuestos Compra Suelo (%)", value=10) / 100
    m2_vivienda = st.number_input("Metros Construidos Vivienda", value=180)

# --- CLASE PDF CON LOGO ---
class PDF(FPDF):
    def header(self):
        # 2. AQUÍ PONEMOS EL LOGO EN EL PAPEL (PDF)
        if os.path.exists(LOGOTIPO):
            # image(archivo, x, y, ancho)
            self.image(LOGOTIPO, 10, 8, 33)
            self.ln(25) # Espacio después del logo
        else:
            self.ln(10)

        self.set_font('Arial', 'B', 16)
        # Movemos el título a la derecha para que no pise el logo
        self.cell(0, 10, 'DOSIER DE INVERSIÓN - SISTEMA EXPRESS', 0, 1, 'R')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Documento confidencial - Generado el {datetime.date.today()}', 0, 0, 'C')

def generar_pdf(terreno, mercado, financiero):
    pdf = PDF()
    pdf.add_page()
    
    # Título del Proyecto
    pdf.set_font('Arial', 'B', 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, f"  Proyecto: {terreno['nombre']}", 1, 1, 'L', fill=True)
    pdf.ln(5)

    # Resumen Ejecutivo
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "RESUMEN EJECUTIVO (Alta Rotación)", 0, 1)
    pdf.set_font('Arial', '', 11)
    
    pdf.cell(0, 8, f"Plazo de Ejecución: {financiero['meses']} Meses", 0, 1)
    pdf.cell(0, 8, f"Inversión Total: {financiero['inversion']:,.2f} EUR", 0, 1)
    pdf.cell(0, 8, f"Beneficio Neto: {financiero['beneficio']:,.2f} EUR", 0, 1)
    pdf.ln(5)

    # Resultados Financieros
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(39, 174, 96) # Verde
    pdf.cell(0, 10, f"ROI OPERACIÓN: {financiero['roi']:.2f}%", 0, 1)
    pdf.set_text_color(0, 0, 0) # Negro
    
    pdf.set_font('Arial', 'I', 12)
    pdf.cell(0, 10, f"Rentabilidad Anualizada (Proyectada): {financiero['roi_anual']:.2f}%", 0, 1)
    pdf.ln(10)
    
    # Tabla de Testigos
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "Comparables de Mercado Usados", 0, 1)
    pdf.set_font('Arial', '', 10)
    
    col_width = 60
    pdf.cell(col_width, 10, "Propiedad Comparable", 1)
    pdf.cell(col_width, 10, "Precio Venta", 1)
    pdf.ln()
    
    for i, t in enumerate(mercado['testigos']):
        pdf.cell(col_width, 10, f"Testigo {i+1}", 1)
        pdf.cell(col_width, 10, f"{t:,.0f} EUR", 1)
        pdf.ln()

    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ PRINCIPAL ---

st.title("🚀 Analizador de Suelo & Viabilidad")
st.markdown("---")

c1, c2 = st.columns(2)
with c1:
    st.subheader("1. Datos del Suelo")
    nombre_terreno = st.text_input("📍 Ubicación / Referencia", "Parcela Zona Alta")
    precio_terreno = st.number_input("💰 Precio Suelo (€)", value=90000, step=1000)

with c2:
    st.subheader("2. Investigación de Mercado")
    t1 = st.number_input("Testigo 1 (€)", value=320000)
    t2 = st.number_input("Testigo 2 (€)", value=340000)
    t3 = st.number_input("Testigo 3 (€)", value=310000)
    media_mercado = (t1 + t2 + t3) / 3

st.markdown("---")

if st.button("ANALIZAR OPERACIÓN", type="primary", use_container_width=True):
    
    # Cálculos
    coste_obra = coste_const_m2 * m2_vivienda
    coste_suelo_total = precio_terreno * (1 + impuestos_compra)
    gastos_soft_total = (coste_obra + coste_suelo_total) * gastos_generales
    inversion_total = coste_suelo_total + coste_obra + gastos_soft_total
    
    precio_venta = media_mercado
    beneficio_neto = precio_venta - inversion_total
    roi_absoluto = (beneficio_neto / inversion_total) * 100
    roi_anualizado = ((1 + (roi_absoluto/100)) ** (12/meses_proyecto) - 1) * 100

    # Resultados
    st.header("📊 Resultados del Análisis")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Inversión Total", f"{inversion_total:,.0f} €")
    m2.metric("Precio Venta", f"{precio_venta:,.0f} €")
    m3.metric("Beneficio", f"{beneficio_neto:,.0f} €")
    m4.metric("ROI Operación", f"{roi_absoluto:.2f} %")
    
    st.divider()
    
    col_veredicto, col_grafico = st.columns([2, 1])
    
    generar_doc = False
    with col_veredicto:
        if 20 <= roi_absoluto <= 40:
            st.markdown('<div class="success-box">', unsafe_allow_html=True)
            st.subheader(f"✅ LUZ VERDE")
            st.markdown(f"<span class='big-font'>ROI Anualizado: {roi_anualizado:.1f}%</span>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            generar_doc = True
        elif roi_absoluto > 40:
            st.success("🚀 OPORTUNIDAD ÚNICA")
            st.markdown(f"<span class='big-font'>ROI Anualizado: {roi_anualizado:.1f}%</span>", unsafe_allow_html=True)
            generar_doc = True
        else:
            st.error(f"❌ ROI BAJO ({roi_absoluto:.2f}%)")
            st.write("Revisar precio suelo.")

    with col_grafico:
        st.write("**Desglose**")
        datos = pd.DataFrame({'C': ['Suelo', 'Obra', 'Soft', 'Bº'], 'V': [coste_suelo_total, coste_obra, gastos_soft_total, beneficio_neto]})
        st.bar_chart(datos.set_index('C'))

    if generar_doc:
        st.write("")
        pdf_bytes = generar_pdf(
            {"nombre": nombre_terreno}, 
            {"testigos": [t1, t2, t3]}, 
            {"inversion": inversion_total, "beneficio": beneficio_neto, "roi": roi_absoluto, "roi_anual": roi_anualizado, "meses": meses_proyecto}
        )
        st.download_button("📄 DESCARGAR DOSIER", pdf_bytes, f"Viabilidad_{nombre_terreno}.pdf", "application/pdf")

import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Calculadora Viabilidad Express", layout="wide", page_icon="🏗️")

# --- ESTILOS CSS PARA DARLE TOQUE PRO ---
st.markdown("""
<style>
    .big-font { font-size:24px !important; color: #2E86C1; font-weight: bold; }
    .success-box { padding: 15px; background-color: #D4EFDF; border-radius: 10px; border-left: 5px solid #27AE60; }
    .metric-container { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# --- CONFIGURACIÓN LATERAL (MODELO DE NEGOCIO) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/263/263115.png", width=50)
    st.header("⚙️ Tu Modelo Constructivo")
    
    st.info("💡 Sistema de Construcción Rápida")
    meses_proyecto = st.slider("Duración del Proyecto (Meses)", 1, 12, 3, help="Tiempo desde compra de suelo hasta venta (Exit).")
    
    st.divider()
    
    coste_const_m2 = st.number_input("Coste Construcción (€/m²)", value=1200, step=50)
    gastos_generales = st.slider("Soft Costs / Gastos Generales (%)", 5, 25, 15) / 100
    impuestos_compra = st.number_input("Impuestos Compra Suelo (%)", value=10) / 100
    m2_vivienda = st.number_input("Metros Construidos Vivienda", value=180)

# --- CLASE PDF ---
class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'DOSIER DE INVERSIÓN - SISTEMA EXPRESS', 0, 1, 'C')
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
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(0, 10, f"Proyecto: {terreno['nombre']}", 1, 1, 'L', fill=True)
    pdf.ln(5)

    # Resumen Ejecutivo (Lo que le importa al inversor)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "RESUMEN EJECUTIVO (Alta Rotación)", 0, 1)
    pdf.set_font('Arial', '', 11)
    
    pdf.cell(0, 8, f"Plazo de Ejecución: {financiero['meses']} Meses", 0, 1)
    pdf.cell(0, 8, f"Inversión Total: {financiero['inversion']:,.2f} EUR", 0, 1)
    pdf.cell(0, 8, f"Beneficio Neto: {financiero['beneficio']:,.2f} EUR", 0, 1)
    pdf.ln(5)

    # Resultados Financieros GRANDES
    pdf.set_font('Arial', 'B', 16)
    pdf.set_text_color(39, 174, 96) # Verde
    pdf.cell(0, 10, f"ROI OPERACIÓN: {financiero['roi']:.2f}%", 0, 1)
    pdf.set_text_color(0, 0, 0) # Negro
    
    pdf.set_font('Arial', 'I', 12)
    pdf.cell(0, 10, f"Rentabilidad Anualizada (Proyectada): {financiero['roi_anual']:.2f}%", 0, 1)
    pdf.ln(5)
    
    # Detalle de Mercado
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "Análisis de Comparables (Testigos)", 0, 1)
    pdf.set_font('Arial', '', 10)
    
    # Tabla simple
    col_width = 45
    pdf.cell(col_width, 10, "Testigo", 1)
    pdf.cell(col_width, 10, "Precio Venta", 1)
    pdf.cell(col_width, 10, "Precio m2", 1)
    pdf.ln()
    
    for i, t in enumerate(mercado['testigos']):
        pdf.cell(col_width, 10, f"Comparable {i+1}", 1)
        pdf.cell(col_width, 10, f"{t:,.0f} EUR", 1)
        pdf.cell(col_width, 10, f"{t/m2_vivienda:,.0f} EUR/m2", 1)
        pdf.ln()

    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ PRINCIPAL ---

st.title("🚀 Analizador de Suelo & Viabilidad")
st.markdown(f"**Modelo Constructivo:** {m2_vivienda}m² en **{meses_proyecto} meses**.")
st.markdown("---")

# Columnas de entrada
c1, c2 = st.columns(2)

with c1:
    st.subheader("1. Datos del Suelo")
    nombre_terreno = st.text_input("📍 Ubicación / Referencia", "Parcela Zona Alta")
    precio_terreno = st.number_input("💰 Precio Suelo (€)", value=90000, step=1000)

with c2:
    st.subheader("2. Investigación de Mercado")
    st.info("Introduce 3 testigos reales de la zona (viviendas terminadas similares).")
    t1 = st.number_input("Testigo 1 (€)", value=320000)
    t2 = st.number_input("Testigo 2 (€)", value=340000)
    t3 = st.number_input("Testigo 3 (€)", value=310000)
    media_mercado = (t1 + t2 + t3) / 3

# Botón de Cálculo
st.markdown("---")
if st.button("ANALIZAR OPERACIÓN", type="primary", use_container_width=True):
    
    # --- LÓGICA FINANCIERA ---
    # Costes
    coste_obra = coste_const_m2 * m2_vivienda
    impuestos_suelo_val = precio_terreno * impuestos_compra
    coste_suelo_total = precio_terreno + impuestos_suelo_val
    gastos_soft_total = (coste_obra + coste_suelo_total) * gastos_generales
    
    inversion_total = coste_suelo_total + coste_obra + gastos_soft_total
    
    # Ventas (Conservador: usamos la media de mercado)
    precio_venta = media_mercado
    
    # Beneficios
    beneficio_neto = precio_venta - inversion_total
    roi_absoluto = (beneficio_neto / inversion_total) * 100
    
    # TIR / ROI ANUALIZADO (La magia de los 3 meses)
    # Fórmula: ((1 + ROI_total)^(12/meses) - 1) * 100
    roi_anualizado = ((1 + (roi_absoluto/100)) ** (12/meses_proyecto) - 1) * 100

    # --- MOSTRAR RESULTADOS ---
    st.header("📊 Resultados del Análisis")
    
    # Métricas clave en fila
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Inversión Total", f"{inversion_total:,.0f} €")
    m2.metric("Precio Venta (Exit)", f"{precio_venta:,.0f} €")
    m3.metric("Beneficio Neto", f"{beneficio_neto:,.0f} €", delta_color="normal")
    m4.metric("ROI Operación", f"{roi_absoluto:.2f} %", delta_color="normal")
    
    st.divider()
    
    # EL VEREDICTO (SEMÁFORO)
    col_veredicto, col_grafico = st.columns([2, 1])
    
    with col_veredicto:
        if 20 <= roi_absoluto <= 40:
            st.markdown('<div class="success-box">', unsafe_allow_html=True)
            st.subheader(f"✅ LUZ VERDE: PROYECTO VIABLE")
            st.write(f"Con un plazo de **{meses_proyecto} meses**, la rentabilidad anualizada es brutal.")
            st.markdown(f"<span class='big-font'>ROI Anualizado: {roi_anualizado:.1f}%</span>", unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            generar_doc = True
        
        elif roi_absoluto > 40:
            st.balloons()
            st.success("🚀 OPORTUNIDAD ÚNICA")
            st.write(f"Rentabilidad excepcional del {roi_absoluto:.2f}% en solo {meses_proyecto} meses.")
            st.markdown(f"<span class='big-font'>ROI Anualizado: {roi_anualizado:.1f}%</span>", unsafe_allow_html=True)
            generar_doc = True
            
        else:
            st.error(f"❌ DESCARTADO (ROI {roi_absoluto:.2f}%)")
            st.write("No alcanza el objetivo mínimo del 20% por operación.")
            generar_doc = False

    with col_grafico:
        st.write("**Desglose de Costes**")
        datos_grafico = pd.DataFrame({
            'Concepto': ['Suelo+Imp', 'Obra', 'Soft Costs', 'Beneficio'],
            'Valor': [coste_suelo_total, coste_obra, gastos_soft_total, beneficio_neto]
        })
        st.bar_chart(datos_grafico.set_index('Concepto'))

    # --- GENERADOR DE PDF ---
    if generar_doc:
        st.write("")
        st.write("⬇️ **Descargar documentación para inversor:**")
        
        datos_terreno = {"nombre": nombre_terreno}
        datos_mercado = {"testigos": [t1, t2, t3]}
        datos_financieros = {
            "inversion": inversion_total,
            "beneficio": beneficio_neto,
            "roi": roi_absoluto,
            "roi_anual": roi_anualizado,
            "meses": meses_proyecto
        }
        
        pdf_bytes = generar_pdf(datos_terreno, datos_mercado, datos_financieros)
        
        st.download_button(
            label="📄 DESCARGAR DOSIER VIABILIDAD (PDF)",
            data=pdf_bytes,
            file_name=f"Viabilidad_{nombre_terreno.replace(' ', '_')}.pdf",
            mime="application/pdf",
            key="pdf-download"
        )

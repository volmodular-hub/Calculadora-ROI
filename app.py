import streamlit as st
import pandas as pd
from fpdf import FPDF
import datetime
import os
import json
import google.generativeai as genai
from PIL import Image

# ==========================================
# 🔐 CONFIGURACIÓN DE LA IA (GOOGLE GEMINI)
# ==========================================
# TU CLAVE API (No compartir este archivo)
GOOGLE_API_KEY = "AIzaSyDAeL2GfyusB3w55sLur27b7t7I_rbETy4"

try:
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    st.error(f"Error configurando la API Key: {e}")

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Calculadora Visual IA", layout="wide", page_icon="🏗️")
LOGOTIPO = "logo.png"

# --- FUNCIÓN: LA IA ANALIZA LA FOTO ---
def analizar_imagen_con_ia(image):
    """
    Envía la captura a Gemini Flash para extraer precio y metros.
    """
    # Usamos el modelo Flash (rápido y eficiente)
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = """
    Actúa como un experto analista inmobiliario. Mira esta imagen (captura de pantalla de un anuncio, web o cartel).
    Extrae estrictamente en formato JSON estos 2 datos numéricos:
    1. "precio": El precio de venta total (solo el número, sin símbolos de moneda).
    2. "m2": Los metros cuadrados construidos (solo el número).
    
    Si no encuentras alguno de los datos, pon 0.
    NO escribas nada más que el JSON.
    Ejemplo de respuesta válida: {"precio": 350000, "m2": 180}
    """
    
    try:
        response = model.generate_content([prompt, image])
        # Limpiamos posibles bloques de código que devuelva la IA
        texto_limpio = response.text.replace("```json", "").replace("```", "").strip()
        datos = json.loads(texto_limpio)
        return datos
    except Exception as e:
        st.error(f"Error procesando imagen con IA: {e}")
        return {"precio": 0, "m2": 0}

# --- CLASE PDF ---
class PDF(FPDF):
    def header(self):
        # Logo de empresa
        if os.path.exists(LOGOTIPO):
            try:
                self.image(LOGOTIPO, 10, 8, 33)
                self.ln(25)
            except:
                self.ln(10)
        else:
            self.ln(10)
        
        # Título
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'DOSIER DE VIABILIDAD - ANÁLISIS VISUAL', 0, 1, 'R')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Generado el {datetime.date.today()} - Uso interno', 0, 0, 'C')

def generar_pdf(terreno, testigos, financiero):
    pdf = PDF()
    pdf.add_page()
    
    # 1. Datos del Proyecto
    pdf.set_font('Arial', 'B', 14)
    pdf.set_fill_color(240, 240, 240)
    pdf.cell(0, 10, f"  Proyecto: {terreno['nombre']}", 1, 1, 'L', fill=True)
    pdf.ln(5)

    # 2. Resumen Ejecutivo
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "RESUMEN EJECUTIVO", 0, 1)
    pdf.set_font('Arial', '', 11)
    
    pdf.cell(0, 8, f"Precio Suelo: {terreno['precio']:,.0f} EUR", 0, 1)
    pdf.cell(0, 8, f"Inversión Total: {financiero['inversion']:,.0f} EUR", 0, 1)
    pdf.cell(0, 8, f"Beneficio Neto: {financiero['beneficio']:,.0f} EUR", 0, 1)
    
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 12)
    pdf.set_text_color(39, 174, 96) # Verde
    pdf.cell(0, 10, f"ROI OPERACIÓN: {financiero['roi']:.2f}%", 0, 1)
    pdf.cell(0, 10, f"ROI ANUALIZADO ({financiero['meses']} meses): {financiero['roi_anual']:.2f}%", 0, 1)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)
    
    # 3. Testigos con Fotos
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, "Estudio de Mercado (Capturas)", 0, 1)
    pdf.set_font('Arial', '', 10)
    
    for i, t in enumerate(testigos):
        precio = t['precio']
        m2 = t['m2']
        precio_m2 = precio / m2 if m2 > 0 else 0
        
        pdf.set_fill_color(245, 245, 245)
        texto = f"Testigo {i+1}: {precio:,.0f} EUR | {m2} m2 | {precio_m2:,.0f} EUR/m2"
        pdf.cell(0, 10, texto, 1, 1, fill=True)
        
        # Insertar imagen si existe
        if t.get('img_path') and os.path.exists(t['img_path']):
            try:
                # Ajustamos tamaño para que no ocupe toda la hoja (ancho 60mm)
                # Obtenemos posición actual
                y_pos = pdf.get_y()
                # Insertamos imagen
                pdf.image(t['img_path'], x=15, y=y_pos+2, w=60)
                # Movemos el cursor hacia abajo dejando espacio para la foto
                pdf.ln(50) 
            except:
                pdf.cell(0, 10, "(Imagen no procesable en PDF)", 0, 1)
        else:
            pdf.ln(2)

    return pdf.output(dest='S').encode('latin-1')

# --- INTERFAZ PRINCIPAL ---

st.title("📸 Calculadora Inmobiliaria IA")
st.caption("Sube capturas de pantalla de Idealista/Fotocasa. La IA leerá los datos.")
st.markdown("---")

# BARRA LATERAL (CONFIGURACIÓN)
with st.sidebar:
    if os.path.exists(LOGOTIPO): 
        st.image(LOGOTIPO, width=150)
    
    st.header("⚙️ Modelo de Negocio")
    meses_proyecto = st.slider("Duración Proyecto (Meses)", 1, 12, 3)
    coste_const_m2 = st.number_input("Coste Const. (€/m²)", 1200)
    gastos_generales = st.slider("Gastos Generales/Soft (%)", 5, 25, 15) / 100
    impuestos_compra = st.number_input("Impuestos Compra Suelo (%)", 10) / 100
    m2_objetivo = st.number_input("m² Vivienda Objetivo", 180)
    
    st.divider()
    st.info("💡 Consejo: Usa capturas donde se vea claro el precio y los metros.")

# COLUMNAS PRINCIPALES
c1, c2 = st.columns([1, 1.5])

# 1. DATOS DEL SUELO
with c1:
    st.subheader("1. El Suelo")
    nombre_terreno = st.text_input("📍 Ubicación / Ref.", "Parcela Ejemplo")
    precio_terreno = st.number_input("💰 Precio Suelo (€)", value=100000, step=1000)

# 2. LOS TESTIGOS (CON IA)
with c2:
    st.subheader("2. Comparables de Mercado")
    
    lista_testigos_final = []
    
    # Bucle para crear 3 tarjetas de subida
    for i in range(1, 4):
        with st.expander(f"🏠 Testigo {i}", expanded=True):
            col_img, col_datos = st.columns([1, 2])
            
            # SUBIDA DE FOTO
            uploaded_file = col_img.file_uploader(f"Subir captura", type=["jpg", "png", "jpeg"], key=f"up_{i}", label_visibility="collapsed")
            
            # INICIALIZAR VARIABLES DE ESTADO
            if f"d_{i}" not in st.session_state:
                st.session_state[f"d_{i}"] = {"p": 0.0, "m": 0.0, "path": None}
            
            # LÓGICA DE PROCESADO
            if uploaded_file is not None:
                try:
                    # 1. Guardar temporalmente para PDF
                    img = Image.open(uploaded_file)
                    path_temp = f"temp_testigo_{i}.jpg"
                    
                    # Convertir a RGB por si es PNG con transparencia (evita errores en PDF)
                    if img.mode in ("RGBA", "P"): 
                        img = img.convert("RGB")
                        
                    img.save(path_temp)
                    st.session_state[f"d_{i}"]["path"] = path_temp
                    
                    # 2. Si el precio es 0, llamar a la IA (Solo una vez)
                    if st.session_state[f"d_{i}"]["p"] == 0:
                        with col_datos:
                            with st.spinner("🤖 Leyendo datos..."):
                                datos_ia = analizar_imagen_con_ia(img)
                                st.session_state[f"d_{i}"]["p"] = float(datos_ia.get("precio", 0))
                                st.session_state[f"d_{i}"]["m"] = float(datos_ia.get("m2", 0))
                                
                                if datos_ia.get("precio", 0) > 0:
                                    st.toast(f"Testigo {i}: Datos extraídos correctamente", icon="✅")
                except Exception as e:
                    st.error(f"Error cargando imagen: {e}")

            # MOSTRAR INPUTS (La IA los rellena, tú corriges)
            with col_datos:
                d = st.session_state[f"d_{i}"]
                p_val = st.number_input("Precio (€)", value=d["p"], key=f"pv_{i}", step=1000.0)
                m_val = st.number_input("Metros (m²)", value=d["m"], key=f"mv_{i}", step=1.0)
                
                if p_val > 0:
                    lista_testigos_final.append({
                        "precio": p_val, 
                        "m2": m_val, 
                        "img_path": d["path"]
                    })

st.markdown("---")

# CÁLCULOS Y RESULTADOS
if st.button("ANALIZAR VIABILIDAD", type="primary", use_container_width=True):
    
    if len(lista_testigos_final) == 0:
        st.error("⚠️ Sube al menos una captura o rellena los datos manualmente.")
    else:
        # 1. Calcular Precio Medio m2 de los testigos
        suma_precio_m2 = 0
        validos = 0
        for t in lista_testigos_final:
            if t['m2'] > 0:
                suma_precio_m2 += (t['precio'] / t['m2'])
                validos += 1
        
        precio_m2_zona = suma_precio_m2 / validos if validos > 0 else 0
        
        # 2. Estimar Ventas (Nuestra casa de 180m2 x precio medio zona)
        if validos > 0:
            precio_venta_estimado = precio_m2_zona * m2_objetivo
        else:
            # Fallback: Media simple de precios totales si faltan m2
            precio_venta_estimado = sum([t['precio'] for t in lista_testigos_final]) / len(lista_testigos_final)

        # 3. Costes
        coste_obra = coste_const_m2 * m2_objetivo
        coste_suelo_total = precio_terreno * (1 + impuestos_compra)
        gastos_soft_total = (coste_obra + coste_suelo_total) * gastos_generales
        inversion_total = coste_suelo_total + coste_obra + gastos_soft_total
        
        # 4. Beneficios
        beneficio = precio_venta_estimado - inversion_total
        roi = (beneficio / inversion_total) * 100
        roi_anual = ((1 + (roi/100)) ** (12/meses_proyecto) - 1) * 100
        
        # --- MOSTRAR DATOS ---
        st.header("📊 Resultados del Análisis")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Precio Venta Estimado", f"{precio_venta_estimado:,.0f} €", f"{precio_m2_zona:,.0f} €/m²")
        c2.metric("Inversión Total", f"{inversion_total:,.0f} €")
        c3.metric("Beneficio Neto", f"{beneficio:,.0f} €")
        c4.metric("ROI Anualizado", f"{roi_anual:.1f} %")
        
        st.divider()
        
        # SEMÁFORO DE VIABILIDAD
        col_veredicto, col_graf = st.columns([2, 1])
        
        with col_veredicto:
            if roi > 20:
                st.success(f"✅ PROYECTO VIABLE (ROI {roi:.2f}%)")
                st.write(f"Gran oportunidad debido a la alta rotación ({meses_proyecto} meses).")
                
                # Generar PDF
                pdf_bytes = generar_pdf(
                    {"nombre": nombre_terreno, "precio": precio_terreno},
                    lista_testigos_final,
                    {"inversion": inversion_total, "beneficio": beneficio, "roi": roi, "roi_anual": roi_anual, "meses": meses_proyecto}
                )
                st.download_button("📄 DESCARGAR DOSIER VISUAL", pdf_bytes, "dosier_ia.pdf", "application/pdf")
            
            elif roi > 10:
                st.warning(f"⚠️ MARGEN AJUSTADO (ROI {roi:.2f}%)")
                st.write("Intenta negociar el precio del suelo a la baja.")
            else:
                st.error(f"❌ RIESGO ALTO (ROI {roi:.2f}%)")

        with col_graf:
            datos_graf = pd.DataFrame({
                'Coste': ['Suelo', 'Obra', 'Soft', 'Bº'],
                'Valor': [coste_suelo_total, coste_obra, gastos_soft_total, beneficio]
            })
            st.bar_chart(datos_graf.set_index('Coste'))

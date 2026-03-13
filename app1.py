import streamlit as st
import pandas as pd
import qrcode
import io
import os
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# --- 1. CONFIGURACIÓN ---
URL_BASE = "https://certificado.streamlit.app/" # <--- PON TU URL AQUÍ
X_TEXTO, Y_TEXTO, TAM_LETRA = 300, 240, 20
X_QR, Y_QR, TAM_QR = 690, 425, 100

st.set_page_config(page_title="Acreditación", layout="centered")

# CSS: Cero propaganda y estética limpia
st.markdown("""
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    #stDecoration {display:none;}
    .stApp { background-color: #ffffff; }
    .stButton>button { background-color: #000; color: #fff; border-radius: 4px; width: 100%; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def cargar_datos():
    if os.path.exists("asistentes.xlsx"):
        return pd.read_excel("asistentes.xlsx", dtype={'DNI': str})
    return None

df = cargar_datos()

def generar_pdf(nombre, dni, modo="pdf"):
    if not os.path.exists("plantilla.png"): return None
    
    # Si es para vista previa en pantalla, usamos PIL
    if modo == "previa":
        img = Image.open("plantilla.png").convert("RGB")
        # Aquí podrías usar ImageDraw para dibujar en la previa si quisieras, 
        # pero para mantenerlo simple y rápido mostraremos la plantilla sola 
        # o el PDF generado.
        return img

    # Generación Real del PDF
    buffer = io.BytesIO()
    plantilla = Image.open("plantilla.png")
    ancho, alto = plantilla.size
    c = canvas.Canvas(buffer, pagesize=(ancho, alto))
    c.drawImage("plantilla.png", 0, 0, width=ancho, height=alto)
    c.setFont("Helvetica-Bold", TAM_LETRA)
    c.drawCentredString(X_TEXTO, alto - Y_TEXTO, f"{nombre.upper()} - DNI: {dni}")
    
    # QR con parámetro de validación
    qr = qrcode.make(f"{URL_BASE}?v={dni}")
    qr_buf = io.BytesIO()
    qr.save(qr_buf, format='PNG')
    c.drawImage(ImageReader(qr_buf), X_QR, alto - (Y_QR + TAM_QR), width=TAM_QR, height=TAM_QR)
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- LÓGICA DE VALIDACIÓN (QR) ---
query = st.query_params
if "v" in query:
    dni_v = query["v"]
    if df is not None:
        user = df[df['DNI'] == dni_v]
        if not user.empty:
            st.markdown(f"<div style='text-align:center; border:2px solid #000; padding:20px;'><h2>✅ AUTÉNTICO</h2><h1>{user.iloc[0]['Nombre']}</h1></div>", unsafe_allow_html=True)
            st.balloons()
        else: st.error("No válido")
    st.stop()

# --- INTERFAZ DE USUARIO ---
st.markdown("<h2 style='text-align: center;'>Portal de Acreditación</h2>", unsafe_allow_html=True)

if df is not None:
    dni_input = st.text_input("DNI:", placeholder="Ingrese su documento")
    
    if dni_input:
        res = df[df['DNI'] == dni_input.strip()]
        if not res.empty:
            nombre_doc = res.iloc[0]['Nombre']
            st.success(f"Confirmado: {nombre_doc}")
            
            # MOSTRAR CERTIFICADO EN PANTALLA
            st.image("plantilla.png", caption="Vista previa de su certificado", use_container_width=True)
            
            # BOTÓN DE DESCARGA
            archivo_pdf = generar_pdf(nombre_doc, dni_input.strip())
            st.download_button("DESCARGAR CERTIFICADO OFICIAL", data=archivo_pdf, file_name=f"Certificado_{dni_input}.pdf")
        else:
            st.error("DNI no encontrado.")

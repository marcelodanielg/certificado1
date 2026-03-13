import streamlit as st
import pandas as pd
import qrcode
import io
import os
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# --- 1. CONFIGURACIÓN DE ESTA CHARLA ---
# Ajusta las coordenadas según tu nueva plantilla
X_TEXTO = 300
Y_TEXTO = 240
TAMANO_LETRA = 20

X_QR = 690
Y_QR = 425
TAMANO_QR = 100

# IMPORTANTE: Coloca aquí la URL que te asigne Streamlit para esta nueva App
URL_BASE = "https://nueva-charla.streamlit.app/" 
# ----------------------------------------

st.set_page_config(page_title="Acreditación Oficial", layout="centered")

# CSS para eliminar toda la publicidad, menús y marcas de Streamlit
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    #stDecoration {display:none;}
    [data-testid="stStatusWidget"] {visibility: hidden;}
    .stDeployButton {display:none;}
    .stApp { background-color: #ffffff; }
    /* Estilo para el botón de descarga */
    .stButton>button {
        background-color: #000000;
        color: #ffffff;
        border-radius: 4px;
        border: none;
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data
def cargar_datos():
    if not os.path.exists("asistentes.xlsx"):
        return None
    try:
        return pd.read_excel("asistentes.xlsx", dtype={'DNI': str})
    except:
        return None

df = cargar_datos()

def generar_pdf(nombre, dni):
    if not os.path.exists("plantilla.png"):
        return None
        
    buffer = io.BytesIO()
    plantilla = Image.open("plantilla.png")
    ancho, alto = plantilla.size
    
    c = canvas.Canvas(buffer, pagesize=(ancho, alto))
    c.drawImage("plantilla.png", 0, 0, width=ancho, height=alto)
    
    # Escribir Nombre y DNI
    c.setFont("Helvetica-Bold", TAMANO_LETRA)
    c.drawCentredString(X_TEXTO, alto - Y_TEXTO, f"{nombre.upper()} - DNI: {dni}")
    
    # QR de Validación específico para esta charla
    enlace_v = f"{URL_BASE}?v={dni}"
    qr = qrcode.make(enlace_v)
    qr_buf = io.BytesIO()
    qr.save(qr_buf, format='PNG')
    qr_buf.seek(0)
    
    c.drawImage(ImageReader(qr_buf), X_QR, alto - (Y_QR + TAMANO_QR), width=TAMANO_QR, height=TAMANO_QR)
    
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer

# --- LÓGICA DE VALIDACIÓN QR ---
query = st.query_params
if "v" in query:
    dni_v = query["v"]
    st.markdown("<br><br>", unsafe_allow_html=True)
    if df is not None:
        doc = df[df['DNI'] == dni_v]
        if not doc.empty:
            st.markdown(f"""
                <div style="text-align: center; border: 1px solid #000; padding: 40px; border-radius: 5px;">
                    <h2 style="color: #000;">VERIFICACIÓN DE AUTENTICIDAD</h2>
                    <hr>
                    <h1 style="color: #000;">{doc.iloc[0]['Nombre']}</h1>
                    <p style="color: #333;">DNI: {dni_v}</p>
                    <p style="color: #666; font-size: 12px;">Certificado de Acreditación Válido</p>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.error("Documento no registrado.")
    st.stop()

# --- PANTALLA PRINCIPAL ---
st.markdown("<h2 style='text-align: center; font-weight: 300;'>Portal de Acreditación</h2>", unsafe_allow_html=True)

if df is None:
    st.error("Error técnico: Base de datos no encontrada.")
else:
    dni_input = st.text_input("Ingrese su DNI para descargar el certificado:", placeholder="Documento sin puntos")
    
    if dni_input:
        dni_limpio = dni_input.strip()
        res = df[df['DNI'] == dni_limpio]
        
        if not res.empty:
            nombre_doc = res.iloc[0]['Nombre']
            st.success(f"Acreditación confirmada para: {nombre_doc}")
            
            pdf = generar_pdf(nombre_doc, dni_limpio)
            if pdf:
                st.download_button(
                    label="DESCARGAR CERTIFICADO OFICIAL",
                    data=pdf,
                    file_name=f"Acreditacion_{dni_limpio}.pdf",
                    mime="application/pdf"
                )
        else:
            st.error("El DNI ingresado no se encuentra en la base de datos de esta charla.")

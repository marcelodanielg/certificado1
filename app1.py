import streamlit as st
import pandas as pd
import qrcode
import io
import os
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

# --- 1. CONFIGURACIÓN ---
URL_BASE = "https://certificado.streamlit.app/" 
X_TEXTO, Y_TEXTO, TAM_LETRA = 300, 240, 20
X_QR, Y_QR, TAM_QR = 690, 425, 70  # Reducido de 100 a 70 para que el QR sea más chico

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
        df = pd.read_excel("asistentes.xlsx")
        if 'DNI' in df.columns:
            df = df.dropna(subset=['DNI'])
            df['DNI'] = df['DNI'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        return df
    return None

df = cargar_datos()

# NUEVA FUNCIÓN: Crea una imagen para mostrar en la web
def generar_imagen_previa(nombre, dni):
    img = Image.open("plantilla.png").convert("RGB")
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("Arial.ttf", TAM_LETRA + 10)
    except:
        font = ImageFont.load_default()

    # Dibujar Texto en la imagen
    texto = f"{nombre.upper()} - DNI: {dni}"
    draw.text((X_TEXTO, Y_TEXTO), texto, fill="black", anchor="mm")
    
    # Dibujar QR en la imagen
    qr = qrcode.make(f"{URL_BASE}?v={dni}")
    qr_img = qr.resize((TAM_QR, TAM_QR))
    img.paste(qr_img, (X_QR, Y_QR))
    
    return img

def generar_pdf(nombre, dni):
    buffer = io.BytesIO()
    plantilla = Image.open("plantilla.png")
    ancho, alto = plantilla.size
    c = canvas.Canvas(buffer, pagesize=(ancho, alto))
    c.drawImage("plantilla.png", 0, 0, width=ancho, height=alto)
    c.setFont("Helvetica-Bold", TAM_LETRA)
    c.drawCentredString(X_TEXTO, alto - Y_TEXTO, f"{nombre.upper()} - DNI: {dni}")
    
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
    dni_v = query["v"].strip()
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
        dni_limpio = dni_input.strip()
        res = df[df['DNI'] == dni_limpio]
        if not res.empty:
            nombre_doc = res.iloc[0]['Nombre']
            
            # 1. Generar y mostrar la VISTA PREVIA real
            with st.spinner("Cargando vista previa..."):
                img_previa = generar_imagen_previa(nombre_doc, dni_limpio)
                st.image(img_previa, caption="Vista previa de su constancia de asistencia", use_container_width=True)
            
            # 2. Botón de descarga del PDF
            archivo_pdf = generar_pdf(nombre_doc, dni_limpio)
            st.download_button("⬇️ DESCARGAR CONSTANCIA DE ASISTENCIA OFICIAL (PDF)", data=archivo_pdf, file_name=f"Constancia_{dni_limpio}.pdf")
        else:
            st.error("DNI no registrado.")

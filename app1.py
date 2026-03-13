import streamlit as st
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io

# Configuración de la página
st.set_page_config(page_title="Generador de Certificados", page_icon="🎓")

st.title("🎓 Descarga tu Certificado")
st.write("Ingresa tu DNI para obtener tu certificado de asistencia.")

# --- FUNCIÓN DE GENERACIÓN ---
def generar_certificado(nombre_texto, dni_texto):
    # 1. Abrir la plantilla
    img = Image.open("plantilla.png")
    draw = ImageDraw.Draw(img)

    # 2. Configurar fuentes
    # He puesto un tamaño grande (100) porque tus coordenadas (2351, 1575) 
    # sugieren que la imagen es de alta resolución.
    try:
        font_nombre = ImageFont.truetype("arial.ttf", 100) 
        font_dni = ImageFont.truetype("arial.ttf", 80)
    except:
        font_nombre = font_dni = ImageFont.load_default()

    # 3. UBICACIONES EXACTAS (según tus medidas)
    # Nombre: 2351 (X), 1575 (Y)
    # DNI: 4803 (X), 1575 (Y)
    
    pos_nombre = (2351, 1575)
    pos_dni = (4803, 1575)

    # 4. Dibujar los textos
    # Fill (0,0,0) es negro. Si el fondo es oscuro, usa (255,255,255) para blanco.
    draw.text(pos_nombre, nombre_texto, font=font_nombre, fill=(0, 0, 0))
    draw.text(pos_dni, dni_texto, font=font_dni, fill=(0, 0, 0))

    # 5. Convertir a bytes para descarga
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

# --- LÓGICA DE BÚSQUEDA ---
try:
    # Leemos el Excel tratando el DNI como texto siempre
    df = pd.read_excel("asistentes.xlsx", dtype={'DNI': str})
    df['DNI'] = df['DNI'].str.strip()
    df['Nombre'] = df['Nombre'].str.strip()
except Exception as e:
    st.error(f"Error al cargar el archivo Excel: {e}")
    st.stop()

# Interfaz de usuario
dni_usuario = st.text_input("Escribe tu DNI:")

if dni_usuario:
    # Buscar en el DataFrame
    datos = df[df['DNI'] == dni_usuario]
    
    if not datos.empty:
        nombre_asistente = datos.iloc[0]['Nombre']
        dni_asistente = datos.iloc[0]['DNI']
        
        st.success(f"¡Certificado encontrado para {nombre_asistente}!")
        
        # Generar imagen
        archivo_cert = generar_certificado(nombre_asistente, dni_asistente)
        
        # Mostrar vista previa
        st.image(archivo_cert, caption="Tu Certificado", use_container_width=True)
        
        # Botón de descarga
        st.download_button(
            label="⬇️ Descargar Certificado",
            data=archivo_cert,
            file_name=f"Certificado_{dni_asistente}.png",
            mime="image/png"
        )
    else:
        st.error("DNI no encontrado en la lista de asistentes.")
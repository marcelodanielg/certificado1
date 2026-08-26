import io
import os
import base64
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
import streamlit as st
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN DE PÁGINA ---
X_TEXTO, Y_TEXTO, TAM_LETRA = 300, 265, 20

st.set_page_config(
    page_title="Constancia de Asistencia", 
    page_icon="📜",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS RESPONSIVE COMPACTO (TODO EN UNA PANTALLA) ---
st.markdown(
    """
    <style>
    /* Ocultar elementos secundarios de Streamlit */
    #MainMenu, footer, header, .stDeployButton, #stDecoration { display: none !important; }
    
    /* Ajustar márgenes para que todo quepa en pantallas móviles sin scroll */
    .block-container {
        padding-top: 0.8rem !important;
        padding-bottom: 0.8rem !important;
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
        max-width: 480px !important;
    }
    
    .stApp { background-color: #f4f6f9; }

    /* Encabezado compacto */
    .header-container {
        text-align: center;
        padding: 8px 5px;
        margin-bottom: 8px;
        background: linear-gradient(135deg, #1b4965 0%, #2b5876 100%);
        border-radius: 8px;
        color: white;
    }
    .header-container h1 {
        margin: 0;
        font-size: 19px;
        font-weight: 700;
        font-family: system-ui, -apple-system, sans-serif;
    }
    .header-container p {
        margin: 2px 0 0 0;
        font-size: 11px;
        opacity: 0.9;
    }

    /* Tarjeta de bienvenida bien condensada */
    .tarjeta-bienvenida {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 8px 12px;
        border: 1px solid #e0e0e0;
        margin-bottom: 8px;
        font-size: 12px;
    }
    .tarjeta-bienvenida h4 {
        margin: 0 0 2px 0;
        color: #1b4965;
        font-size: 13px;
    }
    .pasos-lista {
        margin: 2px 0 0 0;
        padding-left: 16px;
        color: #4a5568;
        font-size: 12px;
        line-height: 1.25;
    }

    /* Formulario visualmente destacado y compacto */
    div[data-testid="stForm"] {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 8px;
        border: 2px solid #1b4965;
        margin-bottom: 8px;
    }
    div[data-testid="stForm"] label {
        font-size: 14px !important;
        font-weight: bold !important;
        color: #1b4965 !important;
    }
    div[data-testid="stForm"] input {
        font-size: 16px !important;
        padding: 6px 8px !important;
    }

    /* Tarjeta de información del docente */
    .tarjeta-info {
        background-color: #ffffff;
        border-left: 4px solid #1b4965;
        padding: 8px 10px;
        border-radius: 6px;
        margin-bottom: 8px;
        color: #2c3e50;
        font-size: 13px;
    }

    .tarjeta-aviso-cierre {
        background-color: #e8f5e9;
        border: 1px solid #c8e6c9;
        color: #1b5e20;
        padding: 8px;
        border-radius: 6px;
        text-align: center;
        margin-top: 6px;
        font-size: 12px;
    }

    /* Estilo de los botones */
    .stButton>button, .stDownloadButton>button {
        background-color: #1b4965 !important;
        color: #ffffff !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        padding: 10px !important;
        border-radius: 6px !important;
        border: none !important;
        width: 100% !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# --- 3. OPTIMIZACIÓN DE MEMORIA CON CACHÉ ---

@st.cache_resource
def obtener_plantilla_base():
    """Carga la imagen base en memoria una sola vez para mejorar la velocidad de descarga."""
    if os.path.exists("plantilla.png"):
        return Image.open("plantilla.png").convert("RGB")
    return None

@st.cache_data(ttl=3600)
def cargar_datos():
    """Carga el Excel en la memoria caché para procesar búsquedas al instante."""
    if os.path.exists("asistentes.xlsx"):
        df = pd.read_excel("asistentes.xlsx")
        df.columns = df.columns.str.strip()

        if "Nombre" in df.columns and "DNI" in df.columns:
            muestra_dni = df["DNI"].dropna().astype(str)
            if muestra_dni.str.contains(r"[a-zA-ZñÑ]").any():
                df = df.rename(columns={"Nombre": "DNI_temporal", "DNI": "Nombre"})
                df = df.rename(columns={"DNI_temporal": "DNI"})

            df = df.dropna(subset=["DNI"])
            df["DNI"] = (
                df["DNI"]
                .astype(str)
                .str.replace(r"\.0$", "", regex=True)
                .str.replace(r"\D", "", regex=True)
            )
            df["Nombre"] = df["Nombre"].astype(str).str.strip()
        return df
    return None


df = cargar_datos()
plantilla_img = obtener_plantilla_base()


def generar_imagen_previa(nombre, dni):
    img = plantilla_img.copy()
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("Arial.ttf", TAM_LETRA + 10)
    except Exception:
        font = ImageFont.load_default()

    texto = f"{nombre.upper()} - DNI: {dni}"
    draw.text((X_TEXTO, Y_TEXTO), texto, fill="black", anchor="mm")
    return img


def generar_pdf(nombre, dni):
    buffer = io.BytesIO()
    ancho, alto = plantilla_img.size

    c = canvas.Canvas(buffer, pagesize=(ancho, alto))
    c.drawImage("plantilla.png", 0, 0, width=ancho, height=alto)
    c.setFont("Helvetica-Bold", TAM_LETRA)
    c.drawCentredString(X_TEXTO, alto - Y_TEXTO, f"{nombre.upper()} - DNI: {dni}")
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


def mostrar_visor_interactivo(pil_image):
    buffered = io.BytesIO()
    pil_image.save(buffered, format="PNG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode()

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://unpkg.com/@panzoom/panzoom@4.5.1/dist/panzoom.min.js"></script>
        <style>
            body {{ margin: 0; padding: 0; overflow: hidden; background: transparent; }}
            .panzoom-container {{
                width: 100%;
                height: 200px;
                border-radius: 8px;
                overflow: hidden;
                background: #e2e8f0;
                touch-action: none;
                display: flex;
                justify-content: center;
                align-items: center;
            }}
            #cert-img {{ max-width: 100%; max-height: 100%; object-fit: contain; }}
        </style>
    </head>
    <body>
        <div class="panzoom-container">
            <img id="cert-img" src="data:image/png;base64,{img_b64}" alt="Certificado">
        </div>
        <script>
            const elem = document.getElementById('cert-img');
            const panzoom = Panzoom(elem, {{ maxScale: 4, minScale: 1, contain: 'outside' }});
            elem.parentElement.addEventListener('wheel', panzoom.zoomWithWheel);
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=210)


# --- 4. FLUJO DE PANTALLA ---
if "descargado" not in st.session_state:
    st.session_state.descargado = False

# VISTA TRAS DESCARGAR (COMPACTA)
if st.session_state.descargado:
    if "img_previa" in st.session_state:
        mostrar_visor_interactivo(st.session_state.img_previa)

    st.markdown(
        """
        <div class='tarjeta-aviso-cierre'>
            ✅ <b>¡Descarga completada!</b><br>
            El PDF se guardó en la carpeta <b>DESCARGAS</b> del teléfono.
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("🔄 Generar otro comprobante", use_container_width=True):
        st.session_state.descargado = False
        st.rerun()

# VISTA INICIAL (FORMULARIO EN 1 PANTALLA)
else:
    st.markdown(
        """
        <div class='header-container'>
            <h1>📜 Constancia de Asistencia</h1>
            <p>Sistema Digital de Emisión de Comprobantes</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if df is not None and plantilla_img is not None:
        st.markdown(
            """
            <div class='tarjeta-bienvenida'>
                <b>Pasos rápidos:</b>
                <ol class='pasos-lista'>
                    <li>Ingrese su DNI sin puntos ni espacios.</li>
                    <li>Verifique sus datos y presione Descargar PDF.</li>
                </ol>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form(key="form_dni"):
            dni_input = st.text_input("Ingrese su número de DNI:", placeholder="Ej: 25123456")
            submit_button = st.form_submit_button(label="🔍 Buscar Comprobante", use_container_width=True)

        if submit_button and dni_input:
            dni_limpio = "".join(filter(str.isdigit, dni_input))
            res = df[df["DNI"] == dni_limpio]

            if not res.empty:
                nombre_doc = res.iloc[0]["Nombre"]
                archivo_pdf = generar_pdf(nombre_doc, dni_limpio)
                img_previa = generar_imagen_previa(nombre_doc, dni_limpio)

                st.markdown(
                    f"""
                    <div class='tarjeta-info'>
                        👤 <b>Docente:</b> {nombre_doc}<br>
                        📋 <b>DNI:</b> {dni_limpio}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                def registrar_descarga():
                    st.session_state.descargado = True
                    st.session_state.img_previa = img_previa

                st.download_button(
                    "📥 DESCARGAR PDF AHORA",
                    data=archivo_pdf,
                    file_name=f"Constancia_{dni_limpio}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    on_click=registrar_descarga,
                )

            else:
                st.error("El DNI no se encuentra registrado en la nómina.")
    else:
        st.warning("No se encontraron los archivos 'asistentes.xlsx' o 'plantilla.png'.")
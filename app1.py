import io
import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
import base64
import streamlit as st
import streamlit.components.v1 as components

# --- 1. CONFIGURACIÓN ---
X_TEXTO, Y_TEXTO, TAM_LETRA = 300, 300, 40

st.set_page_config(
    page_title="Constancia de Asistencia", 
    page_icon="📜",
    layout="centered"
)

# CSS: Diseño limpio y resaltados
st.markdown(
    """
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    #stDecoration {display:none;}
    .stApp { background-color: #f4f6f9; }
    
    .header-container {
        text-align: center;
        padding: 20px 10px;
        margin-bottom: 20px;
        background: linear-gradient(135deg, #1b4965 0%, #2b5876 100%);
        border-radius: 12px;
        color: white;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.08);
    }
    .header-container h1 {
        margin: 0;
        font-size: 26px;
        font-weight: 700;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    .header-container p {
        margin-top: 8px;
        font-size: 14px;
        opacity: 0.9;
    }

    .tarjeta-bienvenida {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #e0e0e0;
        box-shadow: 0px 2px 8px rgba(0,0,0,0.04);
        margin-bottom: 25px;
    }
    .tarjeta-bienvenida h4 {
        margin-top: 0;
        color: #1b4965;
        font-size: 16px;
    }
    .pasos-lista {
        margin: 10px 0 0 0;
        padding-left: 20px;
        color: #4a5568;
        font-size: 14px;
        line-height: 1.6;
    }

    /* Resaltado para la etiqueta e input de DNI */
    div[data-testid="stForm"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border: 2px solid #1b4965;
        box-shadow: 0px 4px 12px rgba(27, 73, 101, 0.1);
        margin-bottom: 20px;
    }
    div[data-testid="stForm"] label {
        font-size: 18px !important;
        font-weight: bold !important;
        color: #1b4965 !important;
    }
    div[data-testid="stForm"] input {
        font-size: 18px !important;
        padding: 10px !important;
        border-radius: 6px !important;
        border: 1px solid #cbd5e1 !important;
    }
    div[data-testid="stForm"] button {
        background-color: #1b4965 !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 6px !important;
        margin-top: 10px;
    }

    .tarjeta-info {
        background-color: #ffffff;
        border-left: 5px solid #1b4965;
        padding: 18px 20px;
        border-radius: 8px;
        box-shadow: 0px 2px 8px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
        color: #2c3e50;
        font-size: 15px;
        line-height: 1.5;
    }

    .tarjeta-aviso-cierre {
        background-color: #e8f5e9;
        border: 1px solid #c8e6c9;
        color: #1b5e20;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        margin-top: 15px;
        font-size: 15px;
    }

    .stDownloadButton>button {
        background-color: #1b4965 !important;
        color: #ffffff !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        padding: 16px 20px !important;
        border-radius: 8px !important;
        border: none !important;
        width: 100% !important;
        box-shadow: 0px 4px 10px rgba(27, 73, 101, 0.25) !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stDownloadButton>button:hover {
        background-color: #2b5876 !important;
        color: #ffffff !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def cargar_datos():
    if os.path.exists("asistentes.xlsx"):
        df = pd.read_excel("asistentes.xlsx")
        df.columns = df.columns.str.strip()

        if "Nombre" in df.columns and "DNI" in df.columns:
            muestra_dni = df["DNI"].dropna().astype(str)
            if muestra_dni.str.contains(r"[a-zA-ZñÑ]").any():
                df = df.rename(
                    columns={"Nombre": "DNI_temporal", "DNI": "Nombre"}
                )
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


def generar_imagen_previa(nombre, dni):
    img = Image.open("plantilla.png").convert("RGB")
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
    plantilla = Image.open("plantilla.png")
    ancho, alto = plantilla.size

    c = canvas.Canvas(buffer, pagesize=(ancho, alto))
    c.drawImage("plantilla.png", 0, 0, width=ancho, height=alto)

    c.setFont("Helvetica-Bold", TAM_LETRA)
    c.drawCentredString(
        X_TEXTO, alto - Y_TEXTO, f"{nombre.upper()} - DNI: {dni}"
    )

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


def mostrar_visor_interactivo(pil_image):
    """Genera un componente HTML con Panzoom ajustado al alto de pantalla"""
    buffered = io.BytesIO()
    pil_image.save(buffered, format="PNG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode()

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0, user-scalable=yes">
        <script src="https://unpkg.com/@panzoom/panzoom@4.5.1/dist/panzoom.min.js"></script>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background-color: transparent;
                display: flex;
                justify-content: center;
                align-items: center;
                overflow: hidden;
            }}
            .panzoom-container {{
                width: 100%;
                height: 360px;
                border-radius: 10px;
                overflow: hidden;
                background: #e2e8f0;
                touch-action: none;
                box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.15);
                position: relative;
                display: flex;
                justify-content: center;
                align-items: center;
            }}
            #cert-img {{
                max-width: 100%;
                max-height: 100%;
                object-fit: contain;
            }}
        </style>
    </head>
    <body>
        <div class="panzoom-container">
            <img id="cert-img" src="data:image/png;base64,{img_b64}" alt="Certificado">
        </div>
        <script>
            const elem = document.getElementById('cert-img');
            const panzoom = Panzoom(elem, {{
                maxScale: 5,
                minScale: 1,
                contain: 'outside',
                canvas: true
            }});
            elem.parentElement.addEventListener('wheel', panzoom.zoomWithWheel);
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=380)


# --- ESTADO DE SESIÓN ---
if "descargado" not in st.session_state:
    st.session_state.descargado = False


# --- VISTA POST-DESCARGA (Visor Interactivo Panzoom) ---
if st.session_state.descargado:
    if "img_previa" in st.session_state:
        # Visor interactivo en HTML/JS puro
        mostrar_visor_interactivo(st.session_state.img_previa)

        st.markdown(
            """
            <div class='tarjeta-aviso-cierre'>
                ✅ <b>Descarga completada con éxito.</b><br>
                El archivo ha sido guardado. Ya puede cerrar esta página desde el navegador.
            </div>
            """,
            unsafe_allow_html=True,
        )

# --- VISTA INICIAL Y FORMULARIO DE DESCARGA ---
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

    if df is not None:
        st.markdown(
            """
            <div class='tarjeta-bienvenida'>
                <h4>Bienvenido/a</h4>
                <p style='margin:0; font-size:14px; color:#555;'>
                    Para descargar su comprobante en formato PDF, siga estos pasos:
                </p>
                <ol class='pasos-lista'>
                    <li>Ingrese su número de DNI (sin puntos ni espacios).</li>
                    <li>Verifique sus datos en pantalla.</li>
                    <li>Presione el botón de descarga.</li>
                </ol>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form(key="form_dni"):
            dni_input = st.text_input(
                "Ingrese su número de DNI:", placeholder="Ej: 25123456"
            )
            submit_button = st.form_submit_button(label="Aceptar", use_container_width=True)

        if submit_button and dni_input:
            dni_limpio = "".join(filter(str.isdigit, dni_input))

            res = df[df["DNI"] == dni_limpio]
            if not res.empty:
                nombre_doc = res.iloc[0]["Nombre"]

                with st.spinner("Generando comprobante..."):
                    archivo_pdf = generar_pdf(nombre_doc, dni_limpio)
                    img_previa = generar_imagen_previa(nombre_doc, dni_limpio)

                st.markdown(
                    f"""
                    <div class='tarjeta-info'>
                        <b>Docente:</b> {nombre_doc}<br>
                        Su comprobante ya está listo. Presione el botón a continuación para obtener su PDF:
                    </div>
                """,
                    unsafe_allow_html=True,
                )

                def registrar_descarga():
                    st.session_state.descargado = True
                    st.session_state.img_previa = img_previa

                st.download_button(
                    "📥 DESCARGAR DOCUMENTO (PDF)",
                    data=archivo_pdf,
                    file_name=f"Constancia_{dni_limpio}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    on_click=registrar_descarga,
                )

            else:
                st.error(
                    "El DNI ingresado no se encuentra registrado en la nómina de asistentes."
                )
    else:
        st.warning("No se encontró el archivo 'asistentes.xlsx' en el servidor.")

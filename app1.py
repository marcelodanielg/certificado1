import io
import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
import streamlit as st

# --- 1. CONFIGURACIÓN ---
X_TEXTO, Y_TEXTO, TAM_LETRA = 300, 240, 20

st.set_page_config(
    page_title="Constancia de Asistencia", 
    page_icon="📜",
    layout="centered"
)

# CSS: Estética institucional, responsive para celulares y tarjetas visuales
st.markdown(
    """
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    #stDecoration {display:none;}
    .stApp { background-color: #f4f6f9; }
    
    /* Encabezado Principal Estilizado */
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

    /* Tarjeta de Bienvenida / Instrucciones */
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

    /* Tarjetas Informativas */
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

    .tarjeta-cierre {
        background-color: #e8f5e9;
        border: 1px solid #c8e6c9;
        color: #1b5e20;
        padding: 20px;
        border-radius: 8px;
        text-align: center;
        margin-top: 20px;
        box-shadow: 0px 2px 8px rgba(0, 0, 0, 0.04);
    }

    /* Botón de Descarga */
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

    /* Ajuste de imagen para pantallas de celulares */
    .stImage img {
        border-radius: 8px;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.12);
        max-width: 100% !important;
        height: auto !important;
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


# --- ENCABEZADO INSTITUCIONAL ---
st.markdown(
    """
    <div class='header-container'>
        <h1>📜 Constancia de Asistencia</h1>
        <p>Sistema Digital de Emisión de Comprobantes</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if "descargado" not in st.session_state:
    st.session_state.descargado = False

if df is not None:
    # Tarjeta decorativa de inicio
    st.markdown(
        """
        <div class='tarjeta-bienvenida'>
            <h4>Bienvenido/a</h4>
            <p style='margin:0; font-size:14px; color:#555;'>
                Para obtener su documento oficial en formato PDF, siga estos sencillos pasos:
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

    dni_input = st.text_input("Ingrese su número de DNI:", placeholder="Ej: 25123456")

    if dni_input:
        dni_limpio = "".join(filter(str.isdigit, dni_input))

        res = df[df["DNI"] == dni_limpio]
        if not res.empty:
            nombre_doc = res.iloc[0]["Nombre"]

            with st.spinner("Generando comprobante..."):
                archivo_pdf = generar_pdf(nombre_doc, dni_limpio)
                img_previa = generar_imagen_previa(nombre_doc, dni_limpio)

            # PASO 1: ANTES DE DESCARGAR
            if not st.session_state.descargado:
                st.markdown(
                    f"""
                    <div class='tarjeta-info'>
                        <b>Docente:</b> {nombre_doc}<br>
                        Su comprobante oficial se encuentra listo. Presione el botón a continuación para descargar el archivo en formato PDF:
                    </div>
                """,
                    unsafe_allow_html=True,
                )

                st.download_button(
                    "📥 DESCARGAR DOCUMENTO (PDF)",
                    data=archivo_pdf,
                    file_name=f"Constancia_{dni_limpio}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    on_click=lambda: st.session_state.update(
                        {"descargado": True}
                    ),
                )

            # PASO 2: UNA VEZ DESCARGADO (Muestra certificado adaptado + aviso de cierre)
            else:
                # Muestra el documento adaptado a la pantalla del dispositivo
                st.image(img_previa, use_container_width=True)

                # Confirmación de cierre
                st.markdown(
                    """
                    <div class='tarjeta-cierre'>
                        <h3 style='margin:0 0 10px 0;'>✅ Descarga completada</h3>
                        <p style='margin:0; font-size:16px;'>
                            El archivo ha sido guardado correctamente en su dispositivo.<br>
                            <b>Ya puede cerrar esta página de forma segura.</b>
                        </p>
                    </div>
                """,
                    unsafe_allow_html=True,
                )

        else:
            st.error(
                "El DNI ingresado no se encuentra registrado en la nómina de asistentes."
            )
else:
    st.warning("No se encontró el archivo 'asistentes.xlsx' en el servidor.")

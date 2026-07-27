import io
import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
import streamlit as st

# --- 1. CONFIGURACIÓN ---
X_TEXTO, Y_TEXTO, TAM_LETRA = 300, 240, 20

st.set_page_config(page_title="Acreditación", layout="centered")

# CSS: Estilos para destacar el botón de descarga y llamadas de atención
st.markdown(
    """
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    #stDecoration {display:none;}
    .stApp { background-color: #ffffff; }
    
    /* Botón común */
    .stButton>button { background-color: #000; color: #fff; border-radius: 4px; width: 100%; }

    /* ESTILO PARA EL BOTÓN DE DESCARGA PRINCIPAL (GIGANTE Y VERDE LLAMATIVO) */
    .stDownloadButton>button {
        background-color: #28a745 !important;
        color: white !important;
        font-size: 20px !important;
        font-weight: bold !important;
        padding: 18px 24px !important;
        border-radius: 10px !important;
        border: none !important;
        width: 100% !important;
        box-shadow: 0px 4px 12px rgba(40, 167, 69, 0.4) !important;
        transition: transform 0.2s ease-in-out !important;
    }
    .stDownloadButton>button:hover {
        transform: scale(1.02) !important;
        background-color: #218838 !important;
    }

    /* BANNER DE INSTRUCCIONES */
    .alerta-descarga {
        background-color: #fff3cd;
        color: #856404;
        border: 2px solid #ffeeba;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 15px;
        font-size: 16px;
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


# --- INTERFAZ DE USUARIO ---
st.markdown(
    "<h2 style='text-align: center;'>Portal de Acreditación</h2>",
    unsafe_allow_html=True,
)

if df is not None:
    dni_input = st.text_input("DNI:", placeholder="Ingrese su documento")

    if dni_input:
        dni_limpio = "".join(filter(str.isdigit, dni_input))

        res = df[df["DNI"] == dni_limpio]
        if not res.empty:
            nombre_doc = res.iloc[0]["Nombre"]

            with st.spinner("Generando certificado..."):
                archivo_pdf = generar_pdf(nombre_doc, dni_limpio)
                img_previa = generar_imagen_previa(nombre_doc, dni_limpio)

            # --- MENSAJE Y BOTÓN DE ALTA VISIBILIDAD ---
            st.success(f"¡Certificado encontrado a nombre de **{nombre_doc}**!")

            # Cartel amarillo de instrucción explícita
            st.markdown(
                """
                <div class='alerta-descarga'>
                    👉 <b>¡PASO FINAL OBLIGATORIO!</b><br>
                    Haga clic en el botón verde de abajo para guardar el certificado PDF en su teléfono o computadora.
                </div>
            """,
                unsafe_allow_html=True,
            )

            # Botón destacado en verde grande
            st.download_button(
                "📥 CLIC AQUÍ PARA DESCARGAR SU CERTIFICADO (PDF)",
                data=archivo_pdf,
                file_name=f"Constancia_{dni_limpio}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

            st.write("---")
            st.caption("Vista previa del documento:")
            st.image(img_previa, use_container_width=True)

        else:
            st.error("DNI no registrado.")
else:
    st.warning("No se encontró el archivo 'asistentes.xlsx' en el repositorio.")

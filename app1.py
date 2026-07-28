import io
import os
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
import streamlit as st

# --- 1. CONFIGURACIÓN ---
X_TEXTO, Y_TEXTO, TAM_LETRA = 300, 240, 20

st.set_page_config(page_title="Constancia de Asistencia", layout="centered")

# CSS: Estética limpia, refinada e institucional
st.markdown(
    """
    <style>
    #MainMenu, footer, header, .stDeployButton {visibility: hidden;}
    #stDecoration {display:none;}
    .stApp { background-color: #f8f9fa; }
    
    .titulo-principal {
        text-align: center;
        color: #1a252f;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 600;
        margin-bottom: 25px;
    }

    .tarjeta-info {
        background-color: #ffffff;
        border-left: 4px solid #1b4965;
        padding: 18px 20px;
        border-radius: 6px;
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

    .stDownloadButton>button {
        background-color: #1b4965 !important;
        color: #ffffff !important;
        font-size: 16px !important;
        font-weight: 600 !important;
        padding: 14px 20px !important;
        border-radius: 6px !important;
        border: none !important;
        width: 100% !important;
        box-shadow: 0px 4px 10px rgba(27, 73, 101, 0.25) !important;
        transition: all 0.2s ease-in-out !important;
    }
    .stDownloadButton>button:hover {
        background-color: #62b6cb !important;
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


# --- INTERFAZ DE USUARIO ---
st.markdown(
    "<h2 class='titulo-principal'>Constancia de Asistencia</h2>",
    unsafe_allow_html=True,
)

if "descargado" not in st.session_state:
    st.session_state.descargado = False

if df is not None:
    dni_input = st.text_input("Ingrese su DNI:", placeholder="Ej: 25123456")

    if dni_input:
        dni_limpio = "".join(filter(str.isdigit, dni_input))

        res = df[df["DNI"] == dni_limpio]
        if not res.empty:
            nombre_doc = res.iloc[0]["Nombre"]

            with st.spinner("Generando documento..."):
                archivo_pdf = generar_pdf(nombre_doc, dni_limpio)
                img_previa = generar_imagen_previa(nombre_doc, dni_limpio)

            # Si todavía no descargó, mostramos el botón
            if not st.session_state.descargado:
                st.markdown(
                    f"""
                    <div class='tarjeta-info'>
                        <b>Docente:</b> {nombre_doc}<br>
                        Su comprobante oficial se encuentra listo. Puede obtenerlo en formato PDF a través del siguiente botón:
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

                st.write("---")
                st.caption("Vista previa:")
                st.image(img_previa, use_container_width=True)

            # Si ya hizo clic en descargar, mostramos el mensaje final de cierre
            else:
                st.markdown(
                    """
                    <div class='tarjeta-cierre'>
                        <h3 style='margin:0 0 10px 0;'>✅ Descarga completada</h3>
                        <p style='margin:0; font-size:16px;'>
                            El documento ha sido guardado correctamente en su dispositivo.<br>
                            <b>Ya puede cerrar esta ventana de forma segura.</b>
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

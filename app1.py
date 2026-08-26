import io
import streamlit as st
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
import qrcode

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(
    page_title="Generador de Certificados",
    page_icon="🎓",
    layout="centered"
)

# --- FUNCIÓN OPTIMIZADA PARA GENERAR PDF EN MEMORIA ---
def generar_pdf_en_memoria(nombre_usuario, curso_nombre):
    """
    Genera un archivo PDF en memoria (BytesIO) optimizado para alto tráfico 
    y descargas simultáneas masivas (+600 usuarios).
    """
    buffer = io.BytesIO()
    # Crear el lienzo PDF sobre el buffer
    c = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)

    # Diseño y Contenido del Certificado
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width / 2, height - 120, "CERTIFICADO DE ASISTENCIA")

    c.setFont("Helvetica", 16)
    c.drawCentredString(width / 2, height - 180, "Se otorga el presente certificado a:")

    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width / 2, height - 230, nombre_usuario.upper())

    c.setFont("Helvetica", 16)
    c.drawCentredString(width / 2, height - 280, f"Por su participación en el curso / capacitación:")

    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(width / 2, height - 320, f'"{curso_nombre}"')

    # Generación de Código QR de validación en memoria
    qr_data = f"Certificado Valido: {nombre_usuario} - {curso_nombre}"
    qr_img = qrcode.make(qr_data)
    
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)

    # Insertar QR en el PDF
    from reportlab.lib.utils import ImageReader
    c.drawImage(ImageReader(qr_buffer), width - 150, 40, width=100, height=100)

    # Finalizar y guardar el PDF en el buffer
    c.showPage()
    c.save()

    buffer.seek(0)
    return buffer.getvalue()

# --- ESTILOS CSS PERSONALIZADOS (Aviso grande e destacado) ---
st.markdown("""
    <style>
    .aviso-descargas {
        background-color: #d4edda;
        color: #155724;
        border: 2px solid #c3e6cb;
        border-radius: 10px;
        padding: 25px;
        text-align: center;
        font-size: 26px !important;
        font-weight: bold;
        margin-top: 20px;
        margin-bottom: 25px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
    }
    .subtexto-descargas {
        font-size: 20px;
        color: #155724;
        margin-top: 10px;
        font-weight: normal;
    }
    </style>
""", unsafe_allow_html=True)

# --- INTERFAZ DE USUARIO EN STREAMLIT ---
st.title("🎓 Acreditación y Descarga de Certificado")

# Control de estado de la sesión
if "descargado" not in st.session_state:
    st.session_state.descargado = False

# Formulario de datos
nombre = st.text_input("Ingrese su Nombre y Apellido completo:", placeholder="Ej: Marcelo Gómez")
curso = st.text_input("Nombre de la Capacitación / Taller:", value="Capacitación Docente 2026")

if nombre:
    # Generar el binario del PDF en memoria instantáneamente
    pdf_bytes = generar_pdf_en_memoria(nombre, curso)

    st.markdown("---")
    
    # Botón de Descarga Optimizado para Alto Tráfico
    boton_descarga = st.download_button(
        label="📥 DESCARGAR CERTIFICADO EN PDF",
        data=pdf_bytes,
        file_name=f"Certificado_{nombre.replace(' ', '_')}.pdf",
        mime="application/pdf",
        key=f"dl_btn_{nombre}",  # Key dinámica para evitar duplicaciones de render
        use_container_width=True
    )

    if boton_descarga:
        st.session_state.descargado = True

    # Cartel destacado una vez iniciada la descarga
    if st.session_state.descargado:
        st.markdown("""
            <div class="aviso-descargas">
                ✅ ¡SU CERTIFICADO SE DESCARGÓ CON ÉXITO!
                <div class="subtexto-descargas">
                    Revise la carpeta 📂 <b>DESCARGAS</b> de su dispositivo (Celular o Computadora).
                </div>
            </div>
        """, unsafe_allow_html=True)

        st.write("")
        
        # Opción de Salir en lugar de reimprimir
        if st.button("🚪 Salir / Finalizar", use_container_width=True, type="secondary"):
            st.session_state.clear()
            st.success("Ha salido correctamente del sistema. Ya puede cerrar esta pestaña.")
            st.rerun()

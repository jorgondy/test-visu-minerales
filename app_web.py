import streamlit as st
import fitz  # PyMuPDF
import io
import random
from PIL import Image

# Configuración inicial de la página (debe ser el primer comando)
st.set_page_config(page_title="Visu Minerales", page_icon="💎", layout="centered")

# --- DISEÑO COZY Y RESPONSIVE (CSS Personalizado) ---
st.markdown("""
<style>
    /* Fondo principal cálido (beige claro) */
    .stApp {
        background-color: #FDFBF7;
    }
    /* Color de los textos principales */
    h1, h2, h3, h4 {
        color: #4A403A !important;
        font-family: 'Helvetica Neue', sans-serif;
    }
    p, label {
        color: #5C524D !important;
    }
    /* Estilo de los botones (Opciones) */
    div.stButton > button {
        background-color: #E27D60;
        color: white;
        border-radius: 15px;
        border: none;
        padding: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        transition: all 0.2s ease-in-out;
        font-weight: 600;
        font-size: 16px;
        height: auto;
        min-height: 80px;
        white-space: normal; /* Permite que textos largos bajen de línea */
    }
    /* Efecto al pasar el ratón por encima de las opciones */
    div.stButton > button:hover {
        background-color: #C7674D;
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        color: white;
        border-color: #C7674D;
    }
    /* Tarjetas flotantes para métricas (Aciertos/Fallos) */
    div[data-testid="metric-container"] {
        background-color: white;
        border-radius: 15px;
        padding: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    /* Centrar la imagen y darle esquinas redondeadas */
    img {
        border-radius: 15px;
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
    }
    /* Ocultar elementos técnicos para aspecto de App nativa */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {background-color: transparent !important;}
</style>
""", unsafe_allow_html=True)

# --- VARIABLES DE MEMORIA ---
if 'minerales_indexados' not in st.session_state:
    st.session_state.minerales_indexados = []
if 'pregunta_actual' not in st.session_state:
    st.session_state.pregunta_actual = None
if 'opciones' not in st.session_state:
    st.session_state.opciones = []
if 'aciertos' not in st.session_state:
    st.session_state.aciertos = 0
if 'fallos' not in st.session_state:
    st.session_state.fallos = 0
if 'mensaje' not in st.session_state:
    st.session_state.mensaje = None
if 'minerales_activos' not in st.session_state:
    st.session_state.minerales_activos = []
if 'animacion' not in st.session_state:
    st.session_state.animacion = None

# --- FUNCIÓN DE LECTURA DE PDFs ---
@st.cache_data(show_spinner="Analizando PDFs y extrayendo datos...")
def procesar_pdfs(archivos_subidos):
    lista_minerales = []
    
    for archivo in archivos_subidos:
        doc = fitz.open(stream=archivo.getvalue(), filetype="pdf")
        
        for num_pagina in range(doc.page_count):
            pagina = doc[num_pagina]
            imagenes = pagina.get_images(full=True)
            
            # Solo páginas con 1 o 2 imágenes (ignoramos el índice)
            if 0 < len(imagenes) <= 2:
                texto = pagina.get_text("text").strip()
                if texto:
                    # CORRECCIÓN: Unimos todo el texto de la página para que salga nombre y familia completos
                    lineas = [linea.strip() for linea in texto.split('\n') if linea.strip()]
                    nombre_mineral = " - ".join(lineas)
                    
                    if len(nombre_mineral) > 5:
                        lista_minerales.append({
                            "pdf_name": archivo.name,
                            "pagina_pdf": num_pagina,
                            "nombre": nombre_mineral
                        })
    return lista_minerales

# --- LÓGICA DEL JUEGO ---
def verificar_respuesta(opcion_elegida):
    if opcion_elegida == st.session_state.pregunta_actual['nombre_correcto']:
        st.session_state.aciertos += 1
        st.session_state.mensaje = ("success", f"✅ ¡Correcto! Era {opcion_elegida}")
        st.session_state.animacion = "acierto"
    else:
        st.session_state.fallos += 1
        st.session_state.mensaje = ("error", f"❌ Fallaste. La respuesta correcta era:\n{st.session_state.pregunta_actual['nombre_correcto']}")
        st.session_state.animacion = "fallo"
    # Borramos la pregunta actual para forzar la creación de una nueva
    st.session_state.pregunta_actual = None

def generar_nueva_pregunta(archivos_subidos):
    st.session_state.mensaje = None
    
    # Elegimos un mineral al azar de los PDFs activos
    mineral_correcto = random.choice(st.session_state.minerales_activos)
    
    # Buscamos el archivo en memoria y extraemos la foto
    archivo_pdf = next(f for f in archivos_subidos if f.name == mineral_correcto["pdf_name"])
    doc = fitz.open(stream=archivo_pdf.getvalue(), filetype="pdf")
    pagina = doc[mineral_correcto['pagina_pdf']]
    imagenes = pagina.get_images(full=True)
    
    xref = imagenes[0][0]
    base_image = doc.extract_image(xref)
    image_bytes = base_image["image"]
    
    # OPTIMIZACIÓN: Sacar las opciones incorrectas del MISMO PDF
    minerales_mismo_pdf = [m['nombre'] for m in st.session_state.minerales_activos if m['pdf_name'] == mineral_correcto['pdf_name']]
    
    opciones = [mineral_correcto['nombre']]
    # Intentamos rellenar con minerales del mismo tema
    while len(opciones) < 4 and len(opciones) < len(minerales_mismo_pdf):
        mineral_al_azar = random.choice(minerales_mismo_pdf)
        if mineral_al_azar not in opciones:
            opciones.append(mineral_al_azar)
            
    # Si ese PDF no tiene suficientes, rellenamos con cualquiera de los temas seleccionados
    todos_los_nombres_activos = [m['nombre'] for m in st.session_state.minerales_activos]
    while len(opciones) < 4:
        mineral_al_azar = random.choice(todos_los_nombres_activos)
        if mineral_al_azar not in opciones:
            opciones.append(mineral_al_azar)
            
    random.shuffle(opciones)
    
    st.session_state.pregunta_actual = {
        "imagen": image_bytes,
        "nombre_correcto": mineral_correcto['nombre']
    }
    st.session_state.opciones = opciones


# --- INTERFAZ DE USUARIO (WEB) ---

st.title("💎 Test de Visu: Minerales")
st.markdown("Arrastra tus PDFs aquí abajo. ¡Puedes subir todos los temas a la vez!")

archivos_subidos = st.file_uploader("", type="pdf", accept_multiple_files=True)

if archivos_subidos:
    st.session_state.minerales_indexados = procesar_pdfs(archivos_subidos)
    nombres_archivos = [archivo.name for archivo in archivos_subidos]
    
    st.markdown("### 📚 Elige qué temas quieres repasar hoy")
    pdfs_seleccionados = st.multiselect(
        "Tus opciones se generarán en base a los PDFs que dejes seleccionados:",
        options=nombres_archivos,
        default=nombres_archivos
    )
    
    st.session_state.minerales_activos = [m for m in st.session_state.minerales_indexados if m['pdf_name'] in pdfs_seleccionados]
    total_minerales = len(st.session_state.minerales_activos)
    
    if total_minerales >= 4:
        st.divider()
        
        # Disparar animaciones
        if st.session_state.animacion == "acierto":
            st.balloons()
            st.session_state.animacion = None
        elif st.session_state.animacion == "fallo":
            st.snow()
            st.session_state.animacion = None
            
        # Marcadores
        col1, col2 = st.columns(2)
        col1.metric("✅ Aciertos", st.session_state.aciertos)
        col2.metric("❌ Fallos", st.session_state.fallos)
        
        # Mensajes de respuesta anterior
        if st.session_state.mensaje:
            tipo, texto = st.session_state.mensaje
            if tipo == "success":
                st.success(texto)
            else:
                st.error(texto)
                
        # Generar pregunta si no hay
        if st.session_state.pregunta_actual is None:
            generar_nueva_pregunta(archivos_subidos)
            
        # Mostrar Foto de la pregunta
        st.markdown("<h3 style='text-align: center;'>¿A qué mineral corresponde esta fotografía?</h3>", unsafe_allow_html=True)
        image = Image.open(io.BytesIO(st.session_state.pregunta_actual['imagen']))
        st.image(image, use_container_width=True)
        
        # Botones en cuadrícula 2x2
        st.markdown("<br>", unsafe_allow_html=True)
        col_opc1, col_opc2 = st.columns(2)
        
        with col_opc1:
            st.button(st.session_state.opciones[0], on_click=verificar_respuesta, args=(st.session_state.opciones[0],), use_container_width=True)
            st.button(st.session_state.opciones[2], on_click=verificar_respuesta, args=(st.session_state.opciones[2],), use_container_width=True)
            
        with col_opc2:
            st.button(st.session_state.opciones[1], on_click=verificar_respuesta, args=(st.session_state.opciones[1],), use_container_width=True)
            st.button(st.session_state.opciones[3], on_click=verificar_respuesta, args=(st.session_state.opciones[3],), use_container_width=True)
            
    elif total_minerales > 0 and total_minerales < 4:
        st.warning("⚠️ Necesitas tener seleccionados temas que sumen al menos 4 minerales en total para poder generar el test de 4 opciones.")
    else:
        st.warning("👆 Selecciona al menos un PDF en la barra superior para empezar.")
else:
    st.info("👆 Esperando a que subas tus archivos PDF para comenzar la magia.")
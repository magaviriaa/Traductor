import os
import time
import glob
import streamlit as st
from PIL import Image

from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events

from gtts import gTTS
from deep_translator import GoogleTranslator  # << reemplazo estable de googletrans


# ==========================
# UI: Cabecera e imagen
# ==========================
st.title("SWIFTIE TRADUCTOR DE LETRAS")
st.subheader("Escucho tu frase y la traduzco al idioma que necesites — Taylor's Version.")

# Carga segura de imagen
IMG_PATH = "swift_microfono.jpg"
if os.path.exists(IMG_PATH):
    image = Image.open(IMG_PATH)
    st.image(image, width=300)
else:
    st.info("⚠️ Sube una imagen llamada 'swift_microfono.jpg' a la carpeta del proyecto.")

with st.sidebar:
    st.subheader("¿Cómo usarlo?")
    st.write(
        "1) Presiona **Escuchar** y, cuando oigas la señal, di/canta la frase.\n"
        "2) Elige idioma de entrada y salida.\n"
        "3) (Opcional) Ajusta el acento para inglés.\n"
        "4) Convierte a audio y descárgalo."
    )

st.write("Toca el botón y di/canta la línea que quieres traducir:")

# ==========================
# Botón de captura por voz (Web Speech API via Bokeh)
# ==========================
stt_button = Button(label=" Escuchar  🎤 (Eras Mode)", width=300, height=50)
stt_button.js_on_event("button_click", CustomJS(code="""
    // Requiere navegador con webkitSpeechRecognition (Chrome, Edge)
    var recognition = new webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;

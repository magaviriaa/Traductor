import os
import time
import glob
import streamlit as st
from PIL import Image

from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events

from gtts import gTTS
from googletrans import Translator


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

    recognition.onresult = function (e) {
        var value = "";
        for (var i = e.resultIndex; i < e.results.length; ++i) {
            if (e.results[i].isFinal) {
                value += e.results[i][0].transcript;
            }
        }
        if (value != "") {
            document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
        }
    }
    recognition.start();
"""))

result = streamlit_bokeh_events(
    stt_button,
    events="GET_TEXT",
    key="listen",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0
)

# ==========================
# Lógica posterior a la captura
# ==========================
if result:
    if "GET_TEXT" in result:
        st.write(result.get("GET_TEXT"))

    # carpeta temporal para audios
    os.makedirs("temp", exist_ok=True)

    st.title("Letra → Audio")
    translator = Translator()

    text = str(result.get("GET_TEXT") or "").strip()

    # ---- Mapas de idioma y acento (robustos y compactos)
    lang_options = ["Inglés", "Español", "Bengali", "Coreano", "Mandarín", "Japonés"]
    lang_code = {
        "Inglés": "en",
        "Español": "es",
        "Bengali": "bn",
        "Coreano": "ko",
        "Mandarín": "zh-cn",
        "Japonés": "ja",
    }

    in_lang = st.selectbox("Selecciona el lenguaje de Entrada", lang_options)
    input_language = lang_code[in_lang]

    out_lang = st.selectbox("Selecciona el lenguaje de salida", lang_options, index=1)
    output_language = lang_code[out_lang]

    accent_options = [
        "Defecto",
        "Español",
        "Reino Unido",
        "Estados Unidos",
        "Canada",
        "Australia",
        "Irlanda",
        "Sudáfrica",
    ]
    tld_map = {
        "Defecto": "com",
        "Español": "com.mx",
        "Reino Unido": "co.uk",
        "Estados Unidos": "com",
        "Canada": "ca",
        "Australia": "com.au",
        "Irlanda": "ie",
        "Sudáfrica": "co.za",
    }
    english_accent = st.selectbox("Selecciona el acento (si eliges inglés)", accent_options)
    tld = tld_map.get(english_accent, "com")

    # ---- Utilidades
    def safe_filename(s: str, maxlen: int = 20) -> str:
        base = (s or "audio").strip()[:maxlen]
        base = "".join(ch for ch in base if ch.isalnum() or ch in (" ", "-", "_")).strip()
        return base or "audio"

    def text_to_speech(input_language: str, output_language: str, text: str, tld: str):
        if not text:
            return None, "No recibí texto desde el micrófono."
        translation = translator.translate(text, src=input_language, dest=output_language)
        trans_text = translation.text
        tts = gTTS(trans_text, lang=output_language, tld=tld, slow=False)
        file_name = safe_filename(text)
        path = f"temp/{file_name}.mp3"
        tts.save(path)
        return file_name, trans_text

    display_output_text = st.checkbox("Mostrar el texto traducido")

    if st.button("Convertir a audio"):
        file_id, output_text = text_to_speech(input_language, output_language, text, tld)
        if file_id is None:
            st.warning(output_text)
        else:
            with open(f"temp/{file_id}.mp3", "rb") as audio_file:
                audio_bytes = audio_file.read()
            st.markdown("## Tu audio:")
            st.audio(audio_bytes, format="audio/mp3", start_time=0)

            if display_output_text:
                st.markdown("## Texto de salida:")
                st.write(output_text)

    # Limpieza de archivos antiguos
    def remove_files(days: int = 7):
        mp3_files = glob.glob("temp/*.mp3")
        if not mp3_files:
            return
        now = time.time()
        ttl = days * 86400
        for f in mp3_files:
            try:
                if os.stat(f).st_mtime < now - ttl:
                    os.remove(f)
            except FileNotFoundError:
                pass

    remove_files(7)

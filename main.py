import os
import urllib.request
import zipfile
import speech_recognition as sr
from google import genai
from gtts import gTTS
import pygame
import time
import threading
import math
import tkinter as tk
from dotenv import load_dotenv

# Quitar los logs molestos de Vosk
try:
    import vosk
    vosk.SetLogLevel(-1)
except ImportError:
    pass

# Cargar variables de entorno
load_dotenv()

# ===== SISTEMA DE ESTADOS PARA LA GUI =====
class AsistenteState:
    INICIALIZANDO = 0
    ESPERANDO_WAKE = 1
    ESCUCHANDO_CONSULTA = 2
    PENSANDO = 3
    HABLANDO = 4

ESTADO_ACTUAL = AsistenteState.INICIALIZANDO

# Configurar API de Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    print("Error: No se encontró la API key de Gemini. Asegúrate de configurarla en el archivo .env")
    os._exit(1)

client = genai.Client()

# ===== CONFIGURACIÓN DEL MODELO OFFLINE (VOSK) =====
MODELO_VOSK_DIR = "model-es"
MODELO_VOSK_URL = "https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip"

def descargar_modelo_vosk():
    """Descarga y extrae el modelo en español para Vosk si no existe localmente."""
    import speech_recognition as sr
    import shutil
    
    sr_dir = os.path.dirname(sr.__file__)
    vosk_model_dir = os.path.join(sr_dir, "models", "vosk")
    
    if not os.path.exists(vosk_model_dir):
        print("\n[!] Modelo de voz offline (Vosk) no encontrado en la librería.")
        
        # Si ya lo descargamos antes en la carpeta local, lo movemos al lugar correcto
        if os.path.exists(MODELO_VOSK_DIR):
            print("Moviendo el modelo previamente descargado a su ubicación correcta...")
            os.makedirs(os.path.dirname(vosk_model_dir), exist_ok=True)
            os.rename(MODELO_VOSK_DIR, vosk_model_dir)
            print("¡Modelo configurado con éxito!\n")
            return
            
        print(f"Descargando modelo en español desde {MODELO_VOSK_URL} (aprox 40MB)...")
        zip_path = "vosk_model.zip"
        urllib.request.urlretrieve(MODELO_VOSK_URL, zip_path)
        
        print("Extrayendo el modelo...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(".")
            
        # Renombrar la carpeta extraída al directorio esperado por la librería
        carpeta_extraida = "vosk-model-small-es-0.42"
        if os.path.exists(carpeta_extraida):
            os.makedirs(os.path.dirname(vosk_model_dir), exist_ok=True)
            os.rename(carpeta_extraida, vosk_model_dir)
            
        # Limpiar el zip
        if os.path.exists(zip_path):
            os.remove(zip_path)
        print("¡Modelo descargado y configurado con éxito!\n")

# ===== FUNCIONES PRINCIPALES =====

def escuchar_audio(source, recognizer, timeout=5, phrase_time_limit=15, modo_offline=False):
    """
    Función de ayuda para escuchar audio del micrófono.
    Si modo_offline es True, utiliza Vosk (local, privado).
    Si modo_offline es False, utiliza Google (nube, alta precisión).
    """
    try:
        if modo_offline:
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=5)
            try:
                # recognize_vosk toma el modelo de la ruta por defecto de la librería
                resultado_raw = recognizer.recognize_vosk(audio)
                try:
                    import json
                    resultado = json.loads(resultado_raw).get("text", "")
                except Exception:
                    # En versiones más recientes ya devuelve el string directamente
                    resultado = str(resultado_raw)
                return resultado
            except Exception as e:
                return None
        else:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            return recognizer.recognize_google(audio, language="es-ES")
            
    except sr.WaitTimeoutError:
        return None
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        if not modo_offline:
            print(f"Error al conectar con Google STT: {e}")
        return None
    except Exception as e:
        return None

def preguntar_a_gemini(texto):
    """Envía el texto a Gemini y devuelve la respuesta."""
    global ESTADO_ACTUAL
    ESTADO_ACTUAL = AsistenteState.PENSANDO
    print("Consultando a Gemini...")
    try:
        interaction = client.interactions.create(
            model="gemini-3.6-flash",
            input=texto
        )
        respuesta_texto = interaction.output_text
        print(f"Gemini: {respuesta_texto}")
        return respuesta_texto
    except Exception as e:
        print(f"Error al consultar a Gemini: {e}")
        return "Lo siento, tuve un problema al procesar tu consulta con Gemini."

def hablar(texto):
    """Convierte el texto a voz usando gTTS y lo reproduce usando pygame."""
    global ESTADO_ACTUAL
    print("Generando audio de la respuesta...")
    try:
        tts = gTTS(text=texto, lang='es')
        archivo_audio = "respuesta.mp3"
        tts.save(archivo_audio)
        
        ESTADO_ACTUAL = AsistenteState.HABLANDO
        
        # Inicializar pygame mixer
        pygame.mixer.init()
        pygame.mixer.music.load(archivo_audio)
        pygame.mixer.music.play()
        
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
        pygame.mixer.quit()
        time.sleep(0.1)
        if os.path.exists(archivo_audio):
            os.remove(archivo_audio)
            
    except Exception as e:
        print(f"Error al intentar hablar: {e}")

def bucle_asistente():
    """Este es el hilo en segundo plano que corre la lógica del asistente."""
    global ESTADO_ACTUAL
    
    PALABRA_CLAVE = "gemini"
    print("=== Asistente de Voz Privado (Vosk + Gemini) Iniciado ===")
    
    # Asegurar que el modelo local exista antes de comenzar
    descargar_modelo_vosk()
    
    print(f"Di 'Hola {PALABRA_CLAVE}' o simplemente '{PALABRA_CLAVE}' para activarme.")
    print("Usa la 'X' en la ventanita para salir.")
    
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        print("\nAjustando el ruido de fondo... por favor, quédate en silencio un momento.")
        recognizer.adjust_for_ambient_noise(source, duration=2)
        print("¡Listo y escuchando de forma local y privada!")
        
        ESTADO_ACTUAL = AsistenteState.ESPERANDO_WAKE
        
        while True:
            try:
                # [LOCAL] Búsqueda de palabra clave con Vosk
                ESTADO_ACTUAL = AsistenteState.ESPERANDO_WAKE
                texto_detectado = escuchar_audio(source, recognizer, modo_offline=True)
                
                if texto_detectado:
                    print(f"  [VOSK-Debug] Escuché localmente: '{texto_detectado}'")
                    texto_lower = texto_detectado.lower()
                    
                    variaciones_gemini = ["gemini", "géminis", "yemini", "jemini", "hemini", "asistente", "hola"]
                    
                    if any(palabra in texto_lower for palabra in variaciones_gemini):
                        print(f"\n[!] Palabra clave detectada localmente: '{texto_detectado}'")
                        
                        hablar("Dime, ¿qué es lo que necesitas?")
                        
                        while True:
                            # [NUBE] Escuchando la consulta real con Google
                            print("\n[GOOGLE] Escuchando tu consulta...")
                            ESTADO_ACTUAL = AsistenteState.ESCUCHANDO_CONSULTA
                            consulta = escuchar_audio(source, recognizer, timeout=5, phrase_time_limit=15, modo_offline=False)
                            
                            if consulta:
                                print(f"Tú dijiste (Google): {consulta}")
                                respuesta = preguntar_a_gemini(consulta)
                                hablar(respuesta)
                                
                                hablar("¿Quieres realizar otra consulta?")
                                print("\n[VOSK] Esperando respuesta de control (sí/no)...")
                                
                                # [LOCAL] Confirmación de continuación con Vosk
                                ESTADO_ACTUAL = AsistenteState.ESCUCHANDO_CONSULTA
                                respuesta_continuar = escuchar_audio(source, recognizer, timeout=5, phrase_time_limit=5, modo_offline=True)
                                
                                if respuesta_continuar:
                                    resp_lower = respuesta_continuar.lower()
                                    print(f"  [VOSK-Debug] Respondiste localmente: '{respuesta_continuar}'")
                                    
                                    if any(palabra in resp_lower for palabra in ["sí", "si", "seguir", "claro", "otra", "dale"]):
                                        hablar("Te escucho.")
                                        continue
                                    elif any(palabra in resp_lower for palabra in ["no", "nada", "cortar", "suficiente", "listo", "gracias", "basta"]):
                                        hablar("De acuerdo. Estaré aquí si me necesitas.")
                                        break
                                    else:
                                        hablar("Entendido, vuelvo a modo privado.")
                                        break
                                else:
                                    print("No escuché respuesta, volviendo a modo privado.")
                                    break
                            else:
                                print("No escuché ninguna consulta. Volviendo a modo privado.")
                                break
                        
                        print("\nVolviendo a escuchar de forma local y privada...")
                        recognizer.adjust_for_ambient_noise(source, duration=1)
                        
            except Exception as e:
                print(f"Ocurrió un error inesperado en el bucle principal: {e}")

# ===== INTERFAZ GRÁFICA =====

def cerrar_aplicacion(evento=None):
    print("Cerrando aplicación...")
    os._exit(0) # Forzar cierre de todos los hilos

def iniciar_gui():
    root = tk.Tk()
    root.title("Asistente Gemini")
    
    # Dimensiones y posición (esquina inferior derecha)
    w, h = 320, 100
    sw = root.winfo_screenwidth()
    sh = root.winfo_screenheight()
    x = sw - w - 20
    y = sh - h - 60
    
    root.geometry(f'{w}x{h}+{x}+{y}')
    root.attributes('-topmost', True)
    root.overrideredirect(True) # Quitar bordes de ventana
    root.configure(bg='#1A1A1D')
    
    # Botón para cerrar oculto/sutil
    btn_cerrar = tk.Label(root, text="X", bg='#1A1A1D', fg='#4E4E50', font=("Arial", 12, "bold"), cursor="hand2")
    btn_cerrar.place(x=w-25, y=5)
    btn_cerrar.bind("<Button-1>", cerrar_aplicacion)
    
    # Título/Estado
    lbl_estado = tk.Label(root, text="Iniciando...", bg='#1A1A1D', fg='#FFFFFF', font=("Segoe UI", 10))
    lbl_estado.place(x=10, y=5)
    
    # Canvas para la onda
    canvas = tk.Canvas(root, width=w, height=60, bg='#1A1A1D', highlightthickness=0)
    canvas.place(x=0, y=40)
    
    tiempo = 0
    
    def actualizar_animacion():
        nonlocal tiempo
        canvas.delete("onda")
        tiempo += 0.1
        
        ancho = w
        alto_medio = 30
        
        color_onda = "#4CAF50" # Verde por defecto
        amplitud = 2 # Casi plano (esperando)
        frecuencia = 0.05
        velocidad = 1
        texto_estado = "Iniciando..."
        
        # Configurar animación según estado
        global ESTADO_ACTUAL
        if ESTADO_ACTUAL == AsistenteState.INICIALIZANDO:
            texto_estado = "Cargando motor de voz..."
            color_onda = "#888888"
        elif ESTADO_ACTUAL == AsistenteState.ESPERANDO_WAKE:
            texto_estado = "Esperando palabra clave..."
            color_onda = "#4CAF50" # Verde
            amplitud = 3
        elif ESTADO_ACTUAL == AsistenteState.ESCUCHANDO_CONSULTA:
            texto_estado = "Escuchando consulta..."
            color_onda = "#00BCD4" # Cyan (Google STT)
            amplitud = 15
            velocidad = 2.5
        elif ESTADO_ACTUAL == AsistenteState.PENSANDO:
            texto_estado = "Gemini pensando..."
            color_onda = "#9C27B0" # Morado (IA)
            amplitud = 8
            velocidad = 4
        elif ESTADO_ACTUAL == AsistenteState.HABLANDO:
            texto_estado = "Hablando..."
            color_onda = "#FF9800" # Naranja
            amplitud = 20
            velocidad = 3
            
        lbl_estado.config(text=texto_estado, fg=color_onda)
        
        # Dibujar onda (3 capas para efecto visual)
        for capa in range(3):
            puntos = []
            desfase = capa * 30 # Desfase para cada capa
            amp_modificada = amplitud * (1 - capa*0.2)
            for i in range(0, ancho, 5):
                # Onda seno animada
                y_punto = alto_medio + math.sin(i * frecuencia + (tiempo * velocidad) + desfase) * amp_modificada
                puntos.append((i, y_punto))
                
            if len(puntos) > 1:
                # Hacer las capas traseras más transparentes (usando colores más oscuros simulados)
                if capa == 0:
                    canvas.create_line(puntos, fill=color_onda, width=3, tags="onda", smooth=True)
                else:
                    # Usar gris/mezcla simple si es muy difícil hacer transparencia en canvas puro
                    canvas.create_line(puntos, fill="#333333", width=2, tags="onda", smooth=True)
        
        root.after(30, actualizar_animacion) # ~33 FPS
        
    actualizar_animacion()
    root.mainloop()

if __name__ == "__main__":
    # Iniciar el asistente en un hilo separado (daemon para que muera con la app)
    hilo_asistente = threading.Thread(target=bucle_asistente, daemon=True)
    hilo_asistente.start()
    
    # Iniciar la interfaz gráfica en el hilo principal
    iniciar_gui()

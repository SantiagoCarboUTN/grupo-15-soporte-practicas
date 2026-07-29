import os
import sys
import json
import queue
import shutil
import threading
import subprocess
import tkinter as tk
from PIL import Image, ImageTk
import pyaudio
from vosk import Model, KaldiRecognizer

INPUT_DIR = "input_images"
OUTPUT_DIR = "selected_images"
MODEL_PATH = "model"

class VoiceGalleryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Controlled Gallery")
        self.root.geometry("800x600")

        os.makedirs(INPUT_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        self.images = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        self.current_index = 0

        self.label_image = tk.Label(root)
        self.label_image.pack(expand=True)
        
        self.label_status = tk.Label(root, text="Iniciando motor de voz...", font=("Arial", 14), fg="gray")
        self.label_status.pack(pady=10)

        self.command_queue = queue.Queue()

        self.show_current_image()

        self.voice_thread = threading.Thread(target=self.listen_loop, daemon=True)
        self.voice_thread.start()

        self.root.after(100, self.process_queue)

    def show_current_image(self):
        if not self.images:
            self.label_status.config(text="No hay imágenes en la carpeta input_images", fg="red")
            return

        img_name = self.images[self.current_index]
        img_path = os.path.join(INPUT_DIR, img_name)

        img = Image.open(img_path)
        img.thumbnail((700, 500), Image.Resampling.LANCZOS)
        
        self.tk_img = ImageTk.PhotoImage(img)
        self.label_image.config(image=self.tk_img)
        self.label_status.config(text=f"Mostrando: {img_name} ({self.current_index + 1}/{len(self.images)})", fg="black")

    def open_selected_folder(self):
        """Abre la carpeta de destino en el explorador de archivos del sistema"""
        path = os.path.abspath(OUTPUT_DIR)
        if sys.platform == "win32":
            os.startfile(path)
        elif sys.platform == "darwin": # macOS
            subprocess.Popen(["open", path])
        else: # Linux
            subprocess.Popen(["xdg-open", path])
        
        self.label_status.config(text="Carpeta de seleccionadas abierta", fg="blue")

    def process_queue(self):
        """Revisa si el hilo de audio envió algún comando"""
        try:
            command = self.command_queue.get_nowait()
            
            if command == "next":
                if self.current_index < len(self.images) - 1:
                    self.current_index += 1
                self.show_current_image()
                
            elif command == "previous":
                if self.current_index > 0:
                    self.current_index -= 1
                self.show_current_image()
                
            elif command == "ok":
                if self.images:
                    src = os.path.join(INPUT_DIR, self.images[self.current_index])
                    dst = os.path.join(OUTPUT_DIR, self.images[self.current_index])
                    shutil.copy2(src, dst)
                    self.label_status.config(text=f"¡Imagen guardada en seleccionadas!", fg="green")
                    
            elif command == "open folder":
                self.open_selected_folder()
                
        except queue.Empty:
            pass
        
        self.root.after(100, self.process_queue)

    def listen_loop(self):
        """Hilo dedicado al reconocimiento de voz continuo"""
        if not os.path.exists(MODEL_PATH):
            print("Error: No se encontró la carpeta 'model'.")
            return

        model = Model(MODEL_PATH)
        recognizer = KaldiRecognizer(model, 16000)

        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=8000)
        stream.start_stream()

        print("Escuchando comandos (next, previous, ok, open folder)...")

        while True:
            data = stream.read(4000, exception_on_overflow=False)
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").lower()
                
                if "next" in text:
                    self.command_queue.put("next")
                elif "previous" in text:
                    self.command_queue.put("previous")
                elif "ok" in text or "okay" in text:
                    self.command_queue.put("ok")
                elif "open folder" in text or "open" in text:
                    self.command_queue.put("open folder")

# Ejecución de la app
if __name__ == "__main__":
    root = tk.Tk()
    app = VoiceGalleryApp(root)
    root.mainloop()
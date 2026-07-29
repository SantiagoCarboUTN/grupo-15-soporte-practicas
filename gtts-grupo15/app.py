import tkinter as tk
import pygame
import os

class TriviaAppVisual:
    def __init__(self, root):
        self.root = root
        self.root.title("Trivia Visual y Auditiva")
        self.root.geometry("500x450")
        self.root.eval('tk::PlaceWindow . center')

        pygame.mixer.init()

        # Agregamos la clave "correcta" que indica el índice (0, 1 o 2) de la respuesta ganadora
        self.preguntas = [
            {
                "texto": "¿De qué color es el cuadrado?", 
                "figura": "cuadrado",
                "color_figura": "red",
                "audio_pregunta": "audios/pregunta_0.mp3",
                "opciones": [
                    {"texto": "Rojo", "audio": "audios/q0_opt0.mp3"},
                    {"texto": "Negro", "audio": "audios/q0_opt1.mp3"},
                    {"texto": "Azul", "audio": "audios/q0_opt2.mp3"}
                ],
                "correcta": 0  # El índice 0 es "Rojo"
            },
            {
                "texto": "¿Qué figura geométrica tiene tres lados?", 
                "figura": "triangulo",
                "color_figura": "blue",
                "audio_pregunta": "audios/pregunta_1.mp3",
                "opciones": [
                    {"texto": "Cuadrado", "audio": "audios/q1_opt0.mp3"},
                    {"texto": "Triángulo", "audio": "audios/q1_opt1.mp3"},
                    {"texto": "Círculo", "audio": "audios/q1_opt2.mp3"}
                ],
                "correcta": 1  # El índice 1 es "Triángulo"
            }
        ]
        self.indice_actual = 0
        self.pausa_activa = False # Para evitar que lea audios mientras mostramos el resultado

        self.lbl_pregunta = tk.Label(root, text="", font=("Helvetica", 16, "bold"), wraplength=450, justify="center")
        self.lbl_pregunta.pack(pady=20)

        self.canvas = tk.Canvas(root, width=150, height=150, bg=root.cget('bg'), highlightthickness=0)
        self.canvas.pack(pady=10)

        self.frame_botones = tk.Frame(root)
        self.frame_botones.pack(pady=20)

        self.botones = []
        for i in range(3):
            btn = tk.Button(self.frame_botones, text="", font=("Helvetica", 12, "bold"), width=12,
                            command=lambda idx=i: self.verificar_respuesta(idx))
            btn.pack(side="left", padx=10)
            btn.bind("<Enter>", lambda event, idx=i: self.reproducir_hover(idx))
            self.botones.append(btn)
            
        # Guardamos el color original del botón para restaurarlo después
        self.color_btn_original = self.botones[0].cget("background")

        self.cargar_pregunta()

    def reproducir_audio(self, ruta_archivo):
        if os.path.exists(ruta_archivo):
            pygame.mixer.music.load(ruta_archivo)
            pygame.mixer.music.play()

    def reproducir_hover(self, index_opcion):
        # Solo reproduce si NO estamos en la pausa mostrando si acertó o no
        if self.indice_actual < len(self.preguntas) and not self.pausa_activa:
            q = self.preguntas[self.indice_actual]
            ruta_audio_opcion = q["opciones"][index_opcion]["audio"]
            self.reproducir_audio(ruta_audio_opcion)

    def dibujar_figura(self, tipo, color):
        self.canvas.delete("all")
        if tipo == "cuadrado":
            self.canvas.create_rectangle(25, 25, 125, 125, fill=color, outline="black", width=2)
        elif tipo == "triangulo":
            self.canvas.create_polygon(75, 25, 25, 125, 125, 125, fill=color, outline="black", width=2)

    def cargar_pregunta(self):
        self.pausa_activa = False # Habilitamos que el mouse vuelva a leer botones
        
        if self.indice_actual < len(self.preguntas):
            q = self.preguntas[self.indice_actual]
            
            self.lbl_pregunta.config(text=q["texto"])
            self.dibujar_figura(q["figura"], q["color_figura"])
            
            for i, btn in enumerate(self.botones):
                # Restauramos texto, color original y reactivamos el botón
                btn.config(text=q["opciones"][i]["texto"], bg=self.color_btn_original, state="normal")
            
            self.reproducir_audio(q["audio_pregunta"])
        else:
            self.lbl_pregunta.config(text="¡Juego terminado!")
            self.canvas.pack_forget()
            self.frame_botones.pack_forget()
            self.reproducir_audio("audios/fin.mp3")

    def verificar_respuesta(self, btn_index):
        # Desactivamos los botones y el hover temporalmente
        self.pausa_activa = True
        for btn in self.botones:
            btn.config(state="disabled")

        q = self.preguntas[self.indice_actual]
        
        # Chequeamos si la respuesta es correcta
        if btn_index == q["correcta"]:
            self.botones[btn_index].config(bg="lightgreen", disabledforeground="black")
            self.reproducir_audio("audios/correcta.mp3")
        else:
            self.botones[btn_index].config(bg="salmon", disabledforeground="black")
            self.botones[q["correcta"]].config(bg="lightgreen", disabledforeground="black") # Le mostramos cuál era la correcta
            self.reproducir_audio("audios/incorrecta.mp3")

        # Usamos el método after() de Tkinter para esperar 2 segundos (2000 ms) antes de avanzar
        self.root.after(2000, self.siguiente_pregunta)

    def siguiente_pregunta(self):
        self.indice_actual += 1
        self.cargar_pregunta()

if __name__ == "__main__":
    root = tk.Tk()
    app = TriviaAppVisual(root)
    root.mainloop()
from gtts import gTTS
import os

if not os.path.exists("audios"):
    os.makedirs("audios")

datos = [
    {
        "pregunta": "¿De qué color es el cuadrado?",
        "opciones": ["Rojo", "Negro", "Azul"]
    },
    {
        "pregunta": "¿Qué figura geométrica tiene tres lados?",
        "opciones": ["Cuadrado", "Triángulo", "Círculo"]
    }
]

for i, item in enumerate(datos):
    gTTS(text=item["pregunta"], lang='es').save(f"audios/pregunta_{i}.mp3")
    for j, opcion in enumerate(item["opciones"]):
        gTTS(text=opcion, lang='es').save(f"audios/q{i}_opt{j}.mp3")

# Audios de fin, acierto y error
gTTS(text="¡Juego terminado! Gracias por participar.", lang='es').save("audios/fin.mp3")
gTTS(text="¡Opción correcta!", lang='es').save("audios/correcta.mp3")
gTTS(text="Opción incorrecta.", lang='es').save("audios/incorrecta.mp3")

print("¡Todos los audios generados con éxito!")
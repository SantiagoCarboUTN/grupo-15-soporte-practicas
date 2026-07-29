

import cv2
import numpy as np
import time
import os
from datetime import datetime

# ─── Configuración ───────────────────────────────────────────────
CARPETA_SALIDA = "capturas"
os.makedirs(CARPETA_SALIDA, exist_ok=True)

TIEMPO_TEMPORIZADOR = 5        # segundos antes de tomar la foto
FPS_VIDEO           = 20.0
RESOLUCION          = (640, 480)

# ─── Estado de la app ────────────────────────────────────────────
grabando         = False
temporizador_on  = False
video_writer     = None
tiempo_inicio    = 0.0

# ─── Botones (x, y, ancho, alto) ─────────────────────────────────
BTN_GRABAR = (20,  20, 200, 55)
BTN_FOTO   = (240, 20, 200, 55)


def timestamp():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def nombre_archivo(ext):
    return os.path.join(CARPETA_SALIDA, f"{timestamp()}.{ext}")


def dibujar_boton(frame, rect, texto, activo=False, hover=False):
    x, y, w, h = rect
    # Fondo
    if activo:
        color_fondo = (0, 60, 200)
    elif hover:
        color_fondo = (60, 60, 60)
    else:
        color_fondo = (30, 30, 30)

    cv2.rectangle(frame, (x, y), (x + w, y + h), color_fondo, -1)
    # Borde
    borde = (0, 120, 255) if activo else (100, 100, 100)
    cv2.rectangle(frame, (x, y), (x + w, y + h), borde, 2)
    # Texto centrado
    fuente    = cv2.FONT_HERSHEY_SIMPLEX
    escala    = 0.6
    grosor    = 1
    tam_texto = cv2.getTextSize(texto, fuente, escala, grosor)[0]
    tx = x + (w - tam_texto[0]) // 2
    ty = y + (h + tam_texto[1]) // 2
    cv2.putText(frame, texto, (tx, ty), fuente, escala, (255, 255, 255), grosor, cv2.LINE_AA)


def punto_en_boton(px, py, rect):
    x, y, w, h = rect
    return x <= px <= x + w and y <= py <= y + h


def dibujar_indicador_grabacion(frame):
    """Punto rojo parpadeante + texto REC."""
    if int(time.time() * 2) % 2 == 0:          # parpadeo cada 0.5s
        cv2.circle(frame, (RESOLUCION[0] - 30, 35), 10, (0, 0, 220), -1)
    cv2.putText(frame, "REC", (RESOLUCION[0] - 65, 42),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 220), 2, cv2.LINE_AA)


def dibujar_temporizador(frame, segundos_restantes):
    """Número grande centrado con cuenta regresiva."""
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), RESOLUCION, (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.35, frame, 0.65, 0, frame)

    texto = str(int(segundos_restantes) + 1)
    fuente = cv2.FONT_HERSHEY_SIMPLEX
    escala = 6
    grosor = 12
    tam    = cv2.getTextSize(texto, fuente, escala, grosor)[0]
    cx     = (RESOLUCION[0] - tam[0]) // 2
    cy     = (RESOLUCION[1] + tam[1]) // 2
    # Sombra
    cv2.putText(frame, texto, (cx + 3, cy + 3), fuente, escala, (0, 0, 0),    grosor, cv2.LINE_AA)
    cv2.putText(frame, texto, (cx,     cy),     fuente, escala, (0, 200, 255), grosor, cv2.LINE_AA)

    # Barra de progreso
    progreso = 1.0 - (segundos_restantes / TIEMPO_TEMPORIZADOR)
    bw = int(RESOLUCION[0] * progreso)
    cv2.rectangle(frame, (0, RESOLUCION[1] - 10), (bw, RESOLUCION[1]), (0, 200, 255), -1)


def flash_foto(frame):
    """Efecto de flash blanco al tomar la foto."""
    overlay = np.ones_like(frame, dtype=np.uint8) * 255
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)


# ─── Callbacks del mouse ─────────────────────────────────────────
mouse_pos = (0, 0)

def on_mouse(event, x, y, flags, param):
    global grabando, temporizador_on, video_writer, tiempo_inicio, mouse_pos
    mouse_pos = (x, y)

    if event != cv2.EVENT_LBUTTONDOWN:
        return

    # Botón GRABAR / DETENER
    if punto_en_boton(x, y, BTN_GRABAR):
        if not grabando:
            nombre = nombre_archivo("avi")
            fourcc = cv2.VideoWriter_fourcc(*"XVID")
            video_writer = cv2.VideoWriter(nombre, fourcc, FPS_VIDEO, RESOLUCION)
            grabando = True
            print(f"[REC] Grabando → {nombre}")
        else:
            grabando = False
            video_writer.release()
            video_writer = None
            print("[REC] Video guardado.")

    # Botón FOTO con temporizador
    elif punto_en_boton(x, y, BTN_FOTO):
        if not temporizador_on and not grabando:
            temporizador_on = True
            tiempo_inicio   = time.time()
            print(f"[FOTO] Temporizador iniciado ({TIEMPO_TEMPORIZADOR}s)...")


# ─── Loop principal ───────────────────────────────────────────────
def main():
    global grabando, temporizador_on, video_writer, tiempo_inicio

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  RESOLUCION[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUCION[1])

    if not cap.isOpened():
        print("Error: no se pudo abrir la cámara.")
        return

    cv2.namedWindow("Camara")
    cv2.setMouseCallback("Camara", on_mouse)

    foto_flash = 0   # frames de flash restantes

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # ── Grabación ────────────────────────────────────────────
        if grabando and video_writer:
            video_writer.write(frame)
            dibujar_indicador_grabacion(frame)

        # ── Temporizador de foto ──────────────────────────────────
        if temporizador_on:
            transcurrido   = time.time() - tiempo_inicio
            restante       = TIEMPO_TEMPORIZADOR - transcurrido

            if restante > 0:
                dibujar_temporizador(frame, restante)
            else:
                # Tomar foto
                temporizador_on = False
                nombre = nombre_archivo("jpg")
                cv2.imwrite(nombre, frame)
                foto_flash = 4
                print(f"[FOTO] Guardada → {nombre}")

        # ── Flash ─────────────────────────────────────────────────
        if foto_flash > 0:
            flash_foto(frame)
            foto_flash -= 1

        # ── Botones ───────────────────────────────────────────────
        mx, my = mouse_pos
        texto_grabar = "[ DETENER ]" if grabando else "[ GRABAR ]"
        texto_foto   = "[ FOTO :  5s ]"

        btn_foto_activo = temporizador_on
        btn_foto_hover  = punto_en_boton(mx, my, BTN_FOTO) and not grabando

        dibujar_boton(frame, BTN_GRABAR, texto_grabar,
        activo=grabando,
        hover=punto_en_boton(mx, my, BTN_GRABAR))
        dibujar_boton(frame, BTN_FOTO, texto_foto,
        activo=btn_foto_activo,
        hover=btn_foto_hover)

        # ── Ayuda ─────────────────────────────────────────────────
        cv2.putText(frame, "Q: salir", (RESOLUCION[0] - 90, RESOLUCION[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 150, 150), 1, cv2.LINE_AA)

        cv2.imshow("Camara", frame)

        tecla = cv2.waitKey(1) & 0xFF
        if tecla == ord("q") or tecla == 27:
            break

    # Limpieza
    if video_writer:
        video_writer.release()
    cap.release()
    cv2.destroyAllWindows()
    print("App cerrada.")


if __name__ == "__main__":
    main()
import cv2
import numpy as np
import math

def iniciar_contador(ruta_video):
    cap = cv2.VideoCapture(ruta_video)
    
    if not cap.isOpened():
        print("Error: No se pudo abrir el video.")
        return

    sustractor = cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=40, detectShadows=True)

    contador_autos = 0
    linea_y = 350 

    vehiculos_registrados = {}
    proximo_id = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame = cv2.resize(frame, (800, 600))
        mascara = sustractor.apply(frame)

        _, mascara = cv2.threshold(mascara, 254, 255, cv2.THRESH_BINARY)
        kernel_chico = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mascara = cv2.erode(mascara, kernel_chico, iterations=1)
        
        kernel_cierre = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
        mascara = cv2.morphologyEx(mascara, cv2.MORPH_CLOSE, kernel_cierre, iterations=2)
        mascara = cv2.dilate(mascara, kernel_chico, iterations=1)

        mascara[0:200, :] = 0 

        contornos, _ = cv2.findContours(mascara, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        cv2.line(frame, (0, linea_y), (frame.shape[1], linea_y), (0, 255, 255), 2)

        centros_actuales = []

        for contorno in contornos:
            area = cv2.contourArea(contorno)
            if area > 800: 
                x, y, ancho, alto = cv2.boundingRect(contorno)
                centro_x = int(x + ancho / 2)
                centro_y = int(y + alto / 2)
                centros_actuales.append((centro_x, centro_y, x, y, ancho, alto))

        nuevos_vehiculos = {}
        
        for (cx, cy, x, y, w, h) in centros_actuales:
            match_id = None
            distancia_minima = 50 
            
            for vid, (v_cx, v_cy) in vehiculos_registrados.items():
                distancia = math.hypot(cx - v_cx, cy - v_cy)
                if distancia < distancia_minima:
                    distancia_minima = distancia
                    match_id = vid
            
            if match_id is not None:
                v_cx, v_cy = vehiculos_registrados[match_id]
                nuevos_vehiculos[match_id] = (cx, cy)
                
                if v_cy <= linea_y and cy > linea_y:
                    contador_autos += 1
            else:
                nuevos_vehiculos[proximo_id] = (cx, cy)
                proximo_id += 1
                
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)

        vehiculos_registrados = nuevos_vehiculos

        cv2.putText(frame, f"Autos detectados: {contador_autos}", (30, 50), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 3)

        cv2.imshow("Tracking Original", frame)
        cv2.imshow("Filtros y Mascara", mascara)

        if cv2.waitKey(30) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    ruta = 'C:/Users/ignac/OneDrive/Desktop/ejemplo-tracking-opencv/video-autopista.mp4'
    iniciar_contador(ruta)

#El video lo descargamos de Youtube, link: https://youtu.be/PJ5xXXcfuTc?si=B3_SmPu8I2t0cF8_&t=12
import cv2

def video_a_panorama(ruta_video, salto_frames=30):
    print(f"Abriendo el video: {ruta_video}")
    captura = cv2.VideoCapture(ruta_video)
    
    if not captura.isOpened():
        print("Error: No se pudo abrir el video.")
        return

    frames_extraidos = []
    contador = 0
    
    # 1. Extraer fotogramas del video
    while True:
        exito, frame = captura.read()
        
        if not exito:
            break
            
        if contador % salto_frames == 0:
            frames_extraidos.append(frame)
            print(f"Fotograma extraído en la posición: {contador}")
            
        contador += 1

    captura.release()
    total_imagenes = len(frames_extraidos)
    print(f"Se extrajeron {total_imagenes} imágenes del video. Procesando el panorama...")

    # validacion de imagenes
    if total_imagenes < 2:
        print("Error: El video es muy corto o el salto_frames es muy alto. Se necesitan al menos 2 imágenes.")
        return

    stitcher = cv2.Stitcher_create()
    estado, panorama = stitcher.stitch(frames_extraidos)

    if estado == cv2.Stitcher_OK:
        print("¡Stitching completado con éxito!")
        ruta_salida = 'panorama_desde_video.jpg'
        cv2.imwrite(ruta_salida, panorama)
        print(f"Panorama guardado como: {ruta_salida}")
        
        # redimencion
        alto, ancho = panorama.shape[:2]
        panorama_pequeno = cv2.resize(panorama, (int(ancho * 0.5), int(alto * 0.5)))
        
        cv2.imshow('Resultado Panoramico', panorama_pequeno)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print(f"Falló el proceso de cosido. Código de error: {estado}")

# Ejecución
if __name__ == "__main__":
    video_a_panorama('C:/Users/ignac/OneDrive/Desktop/ejemplo-stitching-opencv/mi-video-paneo.mp4', salto_frames=30) #para variar los frames del video
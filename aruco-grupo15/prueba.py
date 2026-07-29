import cv2
import numpy as np


# Imagen que reemplazará al marcador
overlay = cv2.imread("reemplazo.png")


aruco_dict = cv2.aruco.getPredefinedDictionary(
    cv2.aruco.DICT_6X6_250
)

detector_params = cv2.aruco.DetectorParameters()
detector = cv2.aruco.ArucoDetector(
    aruco_dict,
    detector_params
)

# Webcam
cap = cv2.VideoCapture(0)

while True:

    ret, frame = cap.read()

    if not ret:
        break

    corners, ids, rejected = detector.detectMarkers(frame)

    if ids is not None:

        for marker_corners in corners:

            pts_dst = marker_corners[0].astype(np.float32)

            h, w = overlay.shape[:2]

            pts_src = np.array([
                [0, 0],
                [w, 0],
                [w, h],
                [0, h]
            ], dtype=np.float32)

            # Homografía
            H = cv2.getPerspectiveTransform(
                pts_src,
                pts_dst
            )

            warped = cv2.warpPerspective(
                overlay,
                H,
                (frame.shape[1], frame.shape[0])
            )

            # Crear máscara del marcador
            mask = np.zeros(
                (frame.shape[0], frame.shape[1]),
                dtype=np.uint8
            )

            cv2.fillConvexPoly(
                mask,
                pts_dst.astype(np.int32),
                255
            )

            mask_inv = cv2.bitwise_not(mask)

            fondo = cv2.bitwise_and(
                frame,
                frame,
                mask=mask_inv
            )

            reemplazo = cv2.bitwise_and(
                warped,
                warped,
                mask=mask
            )

            frame = cv2.add(
                fondo,
                reemplazo
            )

        cv2.aruco.drawDetectedMarkers(
            frame,
            corners,
            ids
        )

    cv2.imshow(
        "Reemplazo ArUco",
        frame
    )

    key = cv2.waitKey(1)

    if key == 27:  # ESC
        break

cap.release()
cv2.destroyAllWindows()
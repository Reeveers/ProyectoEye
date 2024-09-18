import cv2
import dlib
import numpy as np
from screeninfo import get_monitors

# Obtener las dimensiones del monitor
monitor = get_monitors()[0]
screen_width, screen_height = monitor.width, monitor.height

# Cargar el detector de rostros de dlib y el predictor de puntos de referencia
detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

# Variables para almacenar las referencias de calibración
calibration_points = {'top_left': None, 'top_right': None, 'bottom_left': None, 'bottom_right': None}
calibrated = False

# Función para calcular el centro de la pupila
def midpoint(p1, p2):
    return int((p1.x + p2.x) / 2), int((p1.y + p2.y) / 2)

# Función para obtener los puntos clave de un ojo
def get_eye_coordinates(landmarks, eye_points):
    left_corner = (landmarks.part(eye_points[0]).x, landmarks.part(eye_points[0]).y)
    right_corner = (landmarks.part(eye_points[3]).x, landmarks.part(eye_points[3]).y)
    return left_corner, right_corner

# Función de mapeo para traducir las posiciones de los ojos a la pantalla
def map_to_screen(eye_pos, calibration_points):
    if not calibration_points['top_left'] or not calibration_points['bottom_right']:
        return 0, 0  # Si no está calibrado, devolver 0

    # Obtener la distancia de la posición del ojo en relación a los puntos de referencia de la pantalla
    x_ratio = (eye_pos[0] - calibration_points['top_left'][0]) / \
              (calibration_points['top_right'][0] - calibration_points['top_left'][0])

    y_ratio = (eye_pos[1] - calibration_points['top_left'][1]) / \
              (calibration_points['bottom_left'][1] - calibration_points['top_left'][1])

    # Mapeo a la resolución de la pantalla
    screen_x = int(x_ratio * screen_width)
    screen_y = int(y_ratio * screen_height)

    return screen_x, screen_y

# Captura de la cámara
cap = cv2.VideoCapture(0)

while True:
    _, frame = cap.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detectar los rostros
    faces = detector(gray)
    for face in faces:
        landmarks = predictor(gray, face)

        # Obtener los puntos clave de los ojos
        left_eye_left, left_eye_right = get_eye_coordinates(landmarks, [36, 39, 40, 41])  # Ojo izquierdo
        right_eye_left, right_eye_right = get_eye_coordinates(landmarks, [42, 45, 46, 47])  # Ojo derecho

        # Calcular el centro de los ojos
        left_center = midpoint(landmarks.part(36), landmarks.part(39))  # Centro del ojo izquierdo
        right_center = midpoint(landmarks.part(42), landmarks.part(45))  # Centro del ojo derecho

        # Dibujar los puntos de referencia en los ojos
        cv2.circle(frame, left_center, 3, (255, 0, 0), -1)
        cv2.circle(frame, right_center, 3, (255, 0, 0), -1)

        # Calibración: El usuario debe mirar a las cuatro esquinas de la pantalla.
        if not calibrated:
            cv2.putText(frame, "Mira las esquinas para calibrar", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            if cv2.waitKey(1) & 0xFF == ord('1'):
                calibration_points['top_left'] = ((left_center[0] + right_center[0]) // 2, (left_center[1] + right_center[1]) // 2)
                print("Punto superior izquierdo calibrado")
            if cv2.waitKey(1) & 0xFF == ord('2'):
                calibration_points['top_right'] = ((left_center[0] + right_center[0]) // 2, (left_center[1] + right_center[1]) // 2)
                print("Punto superior derecho calibrado")
            if cv2.waitKey(1) & 0xFF == ord('3'):
                calibration_points['bottom_left'] = ((left_center[0] + right_center[0]) // 2, (left_center[1] + right_center[1]) // 2)
                print("Punto inferior izquierdo calibrado")
            if cv2.waitKey(1) & 0xFF == ord('4'):
                calibration_points['bottom_right'] = ((left_center[0] + right_center[0]) // 2, (left_center[1] + right_center[1]) // 2)
                print("Punto inferior derecho calibrado")
                calibrated = True
        else:
            # Una vez calibrado, obtener la dirección de la mirada
            eye_position = ((left_center[0] + right_center[0]) // 2, (left_center[1] + right_center[1]) // 2)
            screen_x, screen_y = map_to_screen(eye_position, calibration_points)

            # Mostrar el punto en la pantalla donde se está mirando
            cv2.putText(frame, f"Mirada en pantalla: {screen_x}, {screen_y}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    # Mostrar la imagen con los ojos detectados
    cv2.imshow("Seguimiento Ocular", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

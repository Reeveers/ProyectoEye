import os
import sys
import cv2
import pygame
import numpy as np
import collections
import keyboard
import warnings
import json
from datetime import datetime

warnings.filterwarnings("ignore", category=UserWarning, module='google.protobuf.symbol_database')

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f'{dir_path}/..')

from eyeGestures.utils import VideoCapture
from eyeGestures.eyegestures import EyeGestures_v2

gestures = EyeGestures_v2()
cap = VideoCapture(0)

# Initialize Pygame
pygame.init()
pygame.font.init()

font = pygame.font.SysFont('Arial', 25)

# Get the display dimensions
screen_info = pygame.display.Info()
screen_width = screen_info.current_w
screen_height = screen_info.current_h

# Set up the screen
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption("Fullscreen Red Cursor")

# Set up colors
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

# Contador de pasos
step_count = 0
steps_data = []

# Mantén un historial de las últimas coordenadas del cursor
history_length = 10
cursor_x_history = collections.deque(maxlen=history_length)
cursor_y_history = collections.deque(maxlen=history_length)

clock = pygame.time.Clock()

# Inicializar la variable calibration
calibration = None

# Inicializar el contador de fijaciones
fixation_count = 0

# Inicializar el contador de sacadas
saccade_count = 0

# Inicializar el contador de regresiones
regression_count = 0

# Umbral de velocidad angular para detectar sacadas (en grados por segundo)
saccade_threshold = 1000

# Función para calcular la velocidad angular
def calculate_angular_velocity(x1, y1, x2, y2, delta_t):
    distance = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return distance / delta_t

# Mantén un historial de las últimas fijaciones
fixation_history_length = 10
fixation_history = collections.deque(maxlen=fixation_history_length)

# Mantén un historial de las posiciones de fijación para detectar regresiones
fixation_positions = collections.deque(maxlen=50)

# Listas para almacenar los historiales de eventos
fixation_log = []
regression_log = []
saccade_log = []

# Main game loop
running = True
isCalibrated = False
iterator = 0
previous_time = pygame.time.get_ticks()
previous_x, previous_y = 0, 0

# Inicializar las coordenadas anteriores
previous_cursor_x, previous_cursor_y = 0, 0

while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q and pygame.key.get_mods() & pygame.KMOD_CTRL:
                running = False

    # Generate new random position for the cursor
    ret, frame = cap.read()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    calibrate = (iterator <= 600)
    iterator += 1

    event, calibration = gestures.step(frame,
        calibrate,
        screen_width,
        screen_height,
        context="my_context")
        
    cursor_x, cursor_y = event.point[0], event.point[1]
    fixation = event.fixation

    # Añadir el valor de fijación actual al historial
    fixation_history.append(fixation)

    # Calcular el promedio de las fijaciones
    average_fixation = sum(fixation_history) / len(fixation_history)

    # Incrementar el contador de fijaciones si el promedio de fijación es superior a 0.8
    if abs(cursor_x - previous_cursor_x) > 15 and abs(cursor_y - previous_cursor_y) > 15 and isCalibrated == True:
        fixation_count += 1
        fixation_log.append({
            "type": "fixation",
            "from": (previous_cursor_x, previous_cursor_y),
            "to": (cursor_x, cursor_y),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    # Actualizar las coordenadas anteriores
    previous_cursor_x, previous_cursor_y = cursor_x, cursor_y

    # Añadir las coordenadas actuales al historial
    cursor_x_history.append(cursor_x)
    cursor_y_history.append(cursor_y)

    # Calcular la media de las coordenadas para suavizar el movimiento
    smooth_cursor_x = int(sum(cursor_x_history) / len(cursor_x_history))
    smooth_cursor_y = int(sum(cursor_y_history) / len(cursor_y_history))

    # Limitar las coordenadas del círculo dentro de los límites de la pantalla
    smooth_cursor_x = max(50, min(smooth_cursor_x, screen_width - 50))
    smooth_cursor_y = max(50, min(smooth_cursor_y, screen_height - 50))

    screen.fill((0, 0, 0))
    frame = np.rot90(frame)
    frame = pygame.surfarray.make_surface(frame)
    frame = pygame.transform.scale(frame, (400, 400))

    # Display frame on Pygame screen
    screen.blit(frame, (0, 0))

    if calibrate:
        # Limitar las coordenadas del círculo de calibración dentro de los límites de la pantalla
        calibration_x = max(calibration.acceptance_radius, min(calibration.point[0], screen_width - calibration.acceptance_radius))
        calibration_y = max(calibration.acceptance_radius, min(calibration.point[1], screen_height - calibration.acceptance_radius))
        pygame.draw.circle(screen, BLUE, (calibration_x, calibration_y), calibration.acceptance_radius)
    else:
        calibration_x = max(calibration.acceptance_radius, min(calibration.point[0], screen_width - calibration.acceptance_radius))
        calibration_y = max(calibration.acceptance_radius, min(calibration.point[1], screen_height - calibration.acceptance_radius))
        pygame.draw.circle(screen, YELLOW, (calibration_x, calibration_y), calibration.acceptance_radius)
        isCalibrated = True

    # Cambiar el color del círculo dependiendo del valor de fixation
    circle_color = GREEN if fixation > 0.6 else RED
    pygame.draw.circle(screen, circle_color, (smooth_cursor_x, smooth_cursor_y), 50)

    # Calcular la velocidad angular y detectar sacadas
    current_time = pygame.time.get_ticks()
    delta_t = (current_time - previous_time) / 1000.0  # Convertir a segundos
    angular_velocity = calculate_angular_velocity(previous_x, previous_y, smooth_cursor_x, smooth_cursor_y, delta_t)
    sacada = angular_velocity > saccade_threshold

    if sacada and isCalibrated == True:
        saccade_count += 1
        saccade_log.append({
            "type": "saccade",
            "from": (previous_x, previous_y),
            "to": (smooth_cursor_x, smooth_cursor_y),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

    # Detectar regresiones
    regression_detected = False
    for (prev_x, prev_y) in fixation_positions:
        distance = np.sqrt((smooth_cursor_x - prev_x) ** 2 + (smooth_cursor_y - prev_y) ** 2)
        if distance < 50:  # Umbral para considerar una regresión
            regression_detected = True
            regression_log.append({
                "type": "regression",
                "from": (previous_x, previous_y),
                "to": (smooth_cursor_x, smooth_cursor_y),
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            break

    if regression_detected and isCalibrated == True:
        regression_count += 1

    # Añadir la posición actual de fijación al historial
    fixation_positions.append((smooth_cursor_x, smooth_cursor_y))

    # Actualizar las variables anteriores
    previous_time = current_time
    previous_x, previous_y = smooth_cursor_x, smooth_cursor_y

    # Renderiza el texto con el promedio de fijación
    text_surface = font.render(f'X: {smooth_cursor_x}, Y: {smooth_cursor_y}, Avg Fixation: {average_fixation:.2f}', True, (255, 255, 255))  # Blanco
    screen.blit(text_surface, (10, 10))  # Coordenadas (10, 10)

    # Mostrar el contador de fijaciones en la pantalla
    fixation_text = font.render(f"Fixations: {fixation_count}", True, (255, 255, 255))
    screen.blit(fixation_text, (50, 50))

    # Mostrar el contador de sacadas en la pantalla
    saccade_text = font.render(f"Saccades: {saccade_count}", True, (255, 255, 255))
    screen.blit(saccade_text, (50, 80))

    # Mostrar el contador de regresiones en la pantalla
    regression_text = font.render(f"Regressions: {regression_count}", True, (255, 255, 255))
    screen.blit(regression_text, (50, 110))

    pygame.display.flip()  

    if step_count < 4 and isCalibrated:
        # Detect pressing of the 'c' key
        if keyboard.is_pressed('c'):
            steps_data.append((smooth_cursor_x, smooth_cursor_y, fixation))
            step_count += 1
            print(f"Step {step_count}: {smooth_cursor_x}, {smooth_cursor_y}, {fixation}")
                
            # Wait for the 'c' key to be released to avoid multiple detections.
            while keyboard.is_pressed('c'):
                pass
                
            # If all 4 steps have been completed, exit the loop.
            if step_count >= 4:
                break

    # Cap the frame rate
    clock.tick(60)

# Quit Pygame
pygame.quit()
cap.close()

# Crear un diccionario con los historiales de eventos
event_logs = {
    "fixation_log": fixation_log,
    "regression_log": regression_log,
    "saccade_log": saccade_log
}

# Crear la carpeta 'logs' si no existe
logs_dir = "C:/Users/jgrios/Desktop/ProyectoEye/logs"
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

# Guardar los historiales de eventos en un archivo JSON en la carpeta 'logs'
with open(os.path.join(logs_dir, "event_logs.json"), "w") as json_file:
    json.dump(event_logs, json_file, indent=4)

# Imprimir los historiales de eventos
print("Fixation Log:")
for log in fixation_log:
    print(log)

print("\nRegression Log:")
for log in regression_log:
    print(log)

print("\nSaccade Log:")
for log in saccade_log:
    print(log)
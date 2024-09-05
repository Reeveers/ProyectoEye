import os
import sys
import cv2
import pygame
import numpy as np
import collections
import warnings
import json
from datetime import datetime, timedelta
from screeninfo import get_monitors

# Configuración de advertencias
warnings.filterwarnings("ignore", category=UserWarning, module='google.protobuf.symbol_database')

# Configuración de rutas
dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f'{dir_path}/..')

# Importaciones de módulos personalizados
from eyeGestures.utils import VideoCapture
from eyeGestures.eyegestures import EyeGestures_v2

# Inicialización de objetos
gestures = EyeGestures_v2()
gestures.uploadCalibrationMap([[0.20,0.13], [0.20, 1], [0.8, 0.13], [0.8, 1]], context = "my_context")
#gestures.enableCNCalib()
gestures.setClassicImpact(10) # by default it is five
cap = VideoCapture(0)

# Inicialización de Pygame
pygame.init()
pygame.font.init()

# PARAMETROS A MODIFICAR SEGUN EL USUARIO
NValuesCalibration = 2000 # Numero iteraciones para calibrar

# Obtener las dimensiones de la pantalla
monitor = get_monitors()[0]
screen_width = monitor.width
screen_height = monitor.height
print(f"Screen Width: {screen_width}, Screen Height: {screen_height}")

font = pygame.font.SysFont('Arial', 25)
screen_info = pygame.display.Info()
#screen_width = screen_info.current_w
#screen_height = screen_info.current_h
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption("Eye Tracker")

# Definición de colores
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)

# Inicialización de variables
history_length = 10
cursor_x_history = collections.deque(maxlen=history_length)
cursor_y_history = collections.deque(maxlen=history_length)
cursor_history = []
clock = pygame.time.Clock()
fixation_count = 0
saccade_count = 0
regression_count = 0
saccade_threshold = 1000
fixation_history_length = 10
fixation_history = collections.deque(maxlen=fixation_history_length)
fixation_log = []
regression_log = []
saccade_log = []
running = True
isCalibrated = False
iterator = 0
previous_time = pygame.time.get_ticks()
previous_x, previous_y = 0, 0

# Variables para registrar el tiempo y la posición del cursor
last_cursor_position = None
last_cursor_time = None
fixation_duration_threshold = timedelta(milliseconds=250)
last_cursor_position_logged = False

# Variable de estado para regresiones
regression_in_progress = False

# Función para calcular la velocidad angular
def calculate_angular_velocity(x1, y1, x2, y2, delta_t):
    distance = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    return distance / delta_t

# Función para detectar fijaciones
def detect_fixations(cursor_x, cursor_y):
    global last_cursor_position, last_cursor_time, fixation_duration_threshold, cursor_history, fixation_count, last_cursor_position_logged

    current_time = datetime.now()
    current_position = (cursor_x, cursor_y)

    if last_cursor_position is not None:
        if current_position == last_cursor_position:
            duration = current_time - last_cursor_time
            if duration >= fixation_duration_threshold and not last_cursor_position_logged:
                fixation_count += 1
                cursor_history.append({
                    "position": current_position,
                    "type": "fixation",
                    "time": current_time.strftime("%Y-%m-%d %H:%M:%S")
                })
                last_cursor_position_logged = True
        else:
            last_cursor_time = current_time
            last_cursor_position_logged = False
    else:
        last_cursor_time = current_time
        last_cursor_position_logged = False

    last_cursor_position = current_position

# Leer el archivo JSON existente
logs_dir = "C:/Users/jgrios/Desktop/ProyectoEye/logs"
json_file_path = f"{logs_dir}/event_logs.json"
try:
    with open(json_file_path, "r") as json_file:
        event_logs = json.load(json_file)
except FileNotFoundError:
    event_logs = {}

# Bucle principal del programa
while running:
    # Manejo de eventos
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q and pygame.key.get_mods() & pygame.KMOD_CTRL:
                running = False

    # Captura de frame y procesamiento / CALIBRACIÓN
    ret, frame = cap.read()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    if isCalibrated == False:
        calibrate = (iterator <= NValuesCalibration)
        iterator += 1

    event, calibration = gestures.step(frame, calibrate, screen_width, screen_height, context="my_context")
    cursor_x, cursor_y = event.point[0], event.point[1]
    fixation = event.fixation

    # Renderizado de la pantalla
    screen.fill((0, 0, 0))
    frame = np.rot90(frame)
    frame = pygame.surfarray.make_surface(frame)
    frame = pygame.transform.scale(frame, (400, 400))
    screen.blit(frame, (0, 0))

    # Dibujar círculos de calibración y fijación
    if calibrate:
        pygame.draw.circle(screen, BLUE, calibration.point, calibration.acceptance_radius)
    else:
        pygame.draw.circle(screen, YELLOW, calibration.point, calibration.acceptance_radius)
        isCalibrated = True

    circle_color = GREEN if fixation == 1 else RED
    pygame.draw.circle(screen, circle_color, (cursor_x, cursor_y), 50)
    # FINALIZAR CALIBRACIÓN

    # Actualización de historiales y cálculos
    fixation_history.append(fixation)
    average_fixation = sum(fixation_history) / len(fixation_history)

    #------------------------------DETECCIONES-----------------------------------------

    if isCalibrated:

        # Calcular la velocidad angular y detectar sacadas
        current_time = pygame.time.get_ticks()
        delta_t = (current_time - previous_time) / 1000.0
        angular_velocity = calculate_angular_velocity(previous_x, previous_y, cursor_x, cursor_y, delta_t)

        distance = np.linalg.norm([cursor_x - previous_x, cursor_y - previous_y])
        
        # Detección de fijaciones
        detect_fixations(cursor_x, cursor_y)

        # Detección de sacadas
        if distance > 100:
            print(f"Angular Velocity: {angular_velocity}")
            if angular_velocity > saccade_threshold:   
                saccade_count += 1
                cursor_history.append({
                    "previous_position": (previous_x, previous_y),
                    "actual_position": (cursor_x, cursor_y),
                    "type": "saccade",
                    "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

        # Detección de regresiones
        if cursor_x < previous_x and not regression_in_progress:
            regression_in_progress = True
            regression_count += 1
            cursor_history.append({
                "position": (cursor_x, cursor_y),
                "type": "regression",
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        elif cursor_x >= previous_x and regression_in_progress:
            regression_in_progress = False

        cursor_history.append({
            "position": (cursor_x, cursor_y),
            "type": "cursor",
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })

        # Actualizar variables
        previous_time = current_time
        previous_x, previous_y = cursor_x, cursor_y

    #------------------------------DETECCIONES-----------------------------------------

    # Renderizar texto en pantalla
    text_surface = font.render(f'X: {cursor_x}, Y: {cursor_y}, Avg Fixation: {average_fixation:.2f}', True, (255, 255, 255))
    screen.blit(text_surface, (10, 10))
    fixation_text = font.render(f"Fixations: {fixation_count}", True, (255, 255, 255))
    screen.blit(fixation_text, (50, 50))
    saccade_text = font.render(f"Saccades: {saccade_count}", True, (255, 255, 255))
    screen.blit(saccade_text, (50, 80))
    regression_text = font.render(f"Regressions: {regression_count}", True, (255, 255, 255))
    screen.blit(regression_text, (50, 110))

    NivelCalibracion = iterator / NValuesCalibration * 100
    regression_text = font.render(f"Calibracion: {NivelCalibracion}", True, (255, 255, 255))
    screen.blit(regression_text, (50, 200))


    pygame.display.flip()
    clock.tick(60)

# Finalización y guardado de logs
pygame.quit()
cap.close()

# Agregar smooth_cursor_history a los datos
event_logs["cursor_history"] = cursor_history

# Escribir los datos actualizados de vuelta al archivo JSON
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

with open(json_file_path, "w") as json_file:
    json.dump(event_logs, json_file, indent=4)

# Calcular el número total de puntos del cursor]
total_points = len(cursor_history)

# Calcular el porcentaje de fijaciones, sacadas y regresiones
fixation_percentage = (fixation_count / total_points) * 100 if total_points > 0 else 0
saccade_percentage = (saccade_count / total_points) * 100 if total_points > 0 else 0
regression_percentage = (regression_count / total_points) * 100 if total_points > 0 else 0

# Imprimir los resultados en la terminal
print(f"Total Cursor Points: {total_points}")
print(f"Fixations: {fixation_count} ({fixation_percentage:.2f}%)")
print(f"Saccades: {saccade_count} ({saccade_percentage:.2f}%)")
print(f"Regressions: {regression_count} ({regression_percentage:.2f}%)")

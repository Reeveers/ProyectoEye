import os
import sys
import cv2
import pygame
import numpy as np
import json
import time
import warnings
import matplotlib.pyplot as plt
from screeninfo import get_monitors

warnings.filterwarnings("ignore", category=UserWarning, module='google.protobuf.symbol_database')

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append(f'{dir_path}/..')

from eyeGestures.utils import VideoCapture
from eyeGestures.eyegestures import EyeGestures_v2

gestures = EyeGestures_v2()
gestures.enableCNCalib()
gestures.setClassicImpact(10)
cap = VideoCapture(0)

# inicializar Pygame
pygame.init()
pygame.font.init()

# Obtener las dimensiones de la pantalla del portátil (1920x1080)
monitor = get_monitors()[0]
screen_width = monitor.width
screen_height = monitor.height
print(f"Screen Width: {screen_width}, Screen Height: {screen_height}")

# Set up the screen
screen = pygame.display.set_mode((screen_width, screen_height), pygame.FULLSCREEN)
pygame.display.set_caption("Eye Tracker")

# Set up colors
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
YELLOW = (255, 255, 0)
BLACK = (0, 0, 0)

clock = pygame.time.Clock()

# Variables
running = True
iterator = 0
isCalibrated = False
cursor_history = []  # Guardar el historial de posiciones del cursor
identDetect = 0 # Identificador de cada detección
duracion_punto = 10000  # Duración de cada punto de estímulo en ms 
inicio_punto = None  # Tiempo de inicio de cada punto
min_puntos_capturados = 15  # Aumentamos el mínimo de puntos capturados por estímulo a 15
tolerancia_duplicados = 5  # Tolerancia para evitar capturar puntos demasiado cercanos

start_time = time.time()

# Puntos de estímulo escalados para la pantalla 1920x1080 en una cuadrícula de 3x3
puntos_estimulo = [
    (screen_width // 6, screen_height // 6),      # Esquina superior izquierda
    (screen_width // 2, screen_height // 6),      # Centro superior
    (5 * screen_width // 6, screen_height // 6),  # Esquina superior derecha
    (screen_width // 6, screen_height // 2),      # Centro izquierda
    (screen_width // 2, screen_height // 2),      # Centro de la pantalla
    (5 * screen_width // 6, screen_height // 2),  # Centro derecha
    (screen_width // 6, 5 * screen_height // 6),  # Esquina inferior izquierda
    (screen_width // 2, 5 * screen_height // 6),  # Centro inferior
    (5 * screen_width // 6, 5 * screen_height // 6)  # Esquina inferior derecha
]

indice_punto = 0  # Para controlar qué punto de estímulo se está mostrando

puntos_capturados_actual = []  # Lista para almacenar las posiciones reales capturadas para el punto actual
todas_las_posiciones_capturadas = []  # Lista para almacenar todas las posiciones capturadas para calcular el RMSE

# Función para calcular la raíz del error cuadrático medio (RMSE)
def calcular_rmse(estimulados, estimados):
    return np.sqrt(np.mean((np.array(estimulados) - np.array(estimados)) ** 2))

# Función para verificar si un punto es suficientemente diferente de los anteriores
def es_punto_nuevo(punto, puntos_capturados, tolerancia=tolerancia_duplicados):
    if len(puntos_capturados) == 0:
        return True
    distancia = np.linalg.norm(np.array(punto) - np.array(puntos_capturados[-1]))
    return distancia > tolerancia

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q and pygame.key.get_mods() & pygame.KMOD_CTRL:
                running = False

    ret, frame = cap.read()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    calibrate = (iterator <= 2000)
    iterator += 1

    event, calibration = gestures.step(frame, calibrate, screen_width, screen_height, context="my_context")

    screen.fill((0, 0, 0))
    frame = np.rot90(frame)
    frame = pygame.surfarray.make_surface(frame)
    frame = pygame.transform.scale(frame, (400, 400))

    if event is not None or calibration is not None:
        screen.blit(frame, (0, 0))
        my_font = pygame.font.SysFont('Comic Sans MS', 30)
        text_surface = my_font.render(f'{event.fixation}', False, (0, 0, 0))
        screen.blit(text_surface, (0, 0))

        if calibrate:
            pygame.draw.circle(screen, BLUE, calibration.point, calibration.acceptance_radius)
        else:
            pygame.draw.circle(screen, YELLOW, calibration.point, calibration.acceptance_radius)
            isCalibrated = True

        circle_color = GREEN if event.fixation == 1 else RED
        pygame.draw.circle(screen, circle_color, (event.point[0], event.point[1]), 50)

        elapsed_time_ms = int((time.time() - start_time) * 1000)

        if isCalibrated:
            # Guardar la posición estimada en cursor_history
            cursor_history.append({
                "id": identDetect,  
                "position": (event.point[0], event.point[1]),
                "time": elapsed_time_ms,
                "fixation": event.fixation  
            })
            
            identDetect += 1

            # Controlar el tiempo de permanencia de cada punto de estímulo
            if inicio_punto is None:
                inicio_punto = time.time()  # Iniciar el temporizador del punto actual

            if indice_punto < len(puntos_estimulo):
                # Mostrar el punto de estímulo actual
                punto_actual = puntos_estimulo[indice_punto]
                pygame.draw.circle(screen, RED, punto_actual, 10)  # Dibujar punto de estímulo

                # Capturar las coordenadas del usuario mientras mira el punto
                if event.fixation == 1 and es_punto_nuevo(event.point, puntos_capturados_actual):  # Evitar capturar puntos muy cercanos
                    puntos_capturados_actual.append((event.point[0], event.point[1]))
                    print(f'Capturado: {event.point[0]}, {event.point[1]}')

                # Si ha pasado suficiente tiempo o si se han capturado suficientes puntos, pasar al siguiente punto
                if ((time.time() - inicio_punto) * 1000 >= duracion_punto) or (len(puntos_capturados_actual) >= min_puntos_capturados):
                    if len(puntos_capturados_actual) > 0:  # Asegurarse de haber capturado datos
                        todas_las_posiciones_capturadas.append(np.mean(puntos_capturados_actual, axis=0))  # Promediar
                        print(f'Promedio capturado: {todas_las_posiciones_capturadas[-1]} para el punto {indice_punto + 1}.')
                    else:
                        print(f"No se capturaron suficientes datos para el punto {indice_punto + 1}.")
                    puntos_capturados_actual = []  # Limpiar capturas para el siguiente punto
                    indice_punto += 1
                    inicio_punto = None  # Reiniciar el temporizador para el siguiente punto

            # Si ya hemos mostrado todos los puntos de estímulo, calcular el RMSE
            if indice_punto == len(puntos_estimulo):
                # Asegurarse de tener suficientes capturas
                if len(todas_las_posiciones_capturadas) == len(puntos_estimulo):
                    # Calcular RMSE por cada estímulo y el global
                    rmse_por_estimulo = []
                    for i in range(len(puntos_estimulo)):
                        rmse_por_estimulo.append(calcular_rmse([puntos_estimulo[i]], [todas_las_posiciones_capturadas[i]]))

                    # Calcular RMSE global
                    rmse_global = calcular_rmse(puntos_estimulo, todas_las_posiciones_capturadas)

                    # Imprimir RMSE global
                    print(f"RMSE Global: {rmse_global}")

                    # Crear un mapa de calor con una cuadrícula 3x3
                    heatmap = np.array(rmse_por_estimulo).reshape(3, 3)

                    plt.figure(figsize=(6, 6))
                    ax = plt.gca()

                    # Generar el mapa de calor
                    cax = ax.matshow(heatmap, cmap='autumn')

                    # Marcar cada celda con el valor del RMSE
                    for (i, j), val in np.ndenumerate(heatmap):
                        ax.text(j, i, f'{val:.2f}', ha='center', va='center', color='black', fontsize=16)

                    # Añadir barra de color con la marca del RMSE global en negro
                    cbar = plt.colorbar(cax)
                    cbar.ax.plot([0, 1], [rmse_global, rmse_global], color='black', lw=4)

                    # Configurar la cuadrícula
                    plt.title('Mapa de calor del RMSE por estímulo')
                    plt.xticks(np.arange(3), ['1', '2', '3'])
                    plt.yticks(np.arange(3), ['7', '4', '1'])
                    plt.grid(False)
                    plt.show()

                else:
                    print("No se capturaron suficientes puntos para calcular el RMSE.")
                running = False  # Finalizar después de calcular el RMSE

    pygame.display.flip()
    clock.tick(60)

# Guardar el historial de cursor en un archivo JSON
with open('cursor_history.json', 'w') as json_file:
    json.dump(cursor_history, json_file, indent=4)

pygame.quit()
cap.close()
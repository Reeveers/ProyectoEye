import os
import sys
import cv2
import pygame
import numpy as np
import collections
import keyboard
import warnings

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

# Main game loop
running = True
isCalibrated = False
iterator = 0
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
    circle_color = GREEN if fixation == 1 else RED
    pygame.draw.circle(screen, circle_color, (smooth_cursor_x, smooth_cursor_y), 50)

    # Renderiza el texto
    text_surface = font.render(f'X: {smooth_cursor_x}, Y: {smooth_cursor_y}, Fixation: {fixation}', True, (255, 255, 255))  # Blanco
    # Blit la superficie del texto en la pantalla
    screen.blit(text_surface, (10, 10))  # Coordenadas (10, 10)

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
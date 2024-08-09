from eyeGestures.utils import VideoCapture
from eyeGestures.eyegestures import EyeGestures_v2

import keyboard
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module='google.protobuf.symbol_database')

# Initialize gesture engine and video capture
gestures = EyeGestures_v2()
cap = VideoCapture(0)  
calibrate = True
screen_width = 1920
screen_height = 1080

# Contador de pasos
step_count = 0
steps_data = []

# Process each frame
while step_count < 4:
  ret, frame = cap.read()
  event, cevent = gestures.step(frame,
    calibrate,
    screen_width,
    screen_height,
    context="my_context")
  
  cursor_x, cursor_y = event.point[0], event.point[1]
  fixation = event.fixation
  #fixation: Se toman N muestras de N frames y se determina cuantas muestras de esas N muestras estan dentro de un radio determinado
  # calibration_radius: radius for data collection during calibration

  #print(cursor_x, cursor_y, fixation)

    # Detect pressing of the 'c' key
  if keyboard.is_pressed('c'):
    steps_data.append((cursor_x, cursor_y, fixation))
    step_count += 1
    print(f"Step {step_count}: {cursor_x}, {cursor_y}, {fixation}")
        
    # Wait for the 'c' key to be released to avoid multiple detections.
    while keyboard.is_pressed('c'):
        pass
        
    # If all 4 steps have been completed, exit the loop.
    if step_count >= 4:
        break
    
cap.close()

import json
import matplotlib.pyplot as plt
import numpy as np
from screeninfo import get_monitors

# Obtener las dimensiones de la pantalla
monitor = get_monitors()[0]
screen_width = monitor.width
screen_height = monitor.height
print(f"Screen Width: {screen_width}, Screen Height: {screen_height}")

# Leer el archivo JSON
json_file_path = "C:/Users/jgrios/Desktop/ProyectoEye/logs/event_logs.json"
with open(json_file_path, "r") as json_file:
    event_logs = json.load(json_file)

# Extraer cursor_history
cursor_history = event_logs.get("cursor_history", [])

# Clasificar los datos según el tipo de detección
fixations = [entry for entry in cursor_history if isinstance(entry, dict) and entry.get("type") == "fixation"]
saccades = [entry for entry in cursor_history if isinstance(entry, dict) and entry.get("type") == "saccade"]
regressions = [entry for entry in cursor_history if isinstance(entry, dict) and entry.get("type") == "regression"]
cursors = [entry for entry in cursor_history if isinstance(entry, dict) and entry.get("type") == "cursor"]

# Crear la gráfica
plt.figure(figsize=(10, 6))

# Establecer los límites de los ejes
plt.xlim(0, screen_width)
plt.ylim(0, screen_height)

# Graficar cada tipo de detección con un color diferente
if fixations:
    plt.scatter([entry["position"][0] for entry in fixations], [entry["position"][1] for entry in fixations], color='green', label='Fixations')
if saccades:
    plt.scatter([entry["previous_position"][0] for entry in saccades], [entry["previous_position"][1] for entry in saccades], color='pink', label='Previous_Saccades')
    plt.scatter([entry["actual_position"][0] for entry in saccades], [entry["actual_position"][1] for entry in saccades], color='red', label='Actual_Saccades')
if regressions:
    plt.scatter([entry["position"][0] for entry in regressions], [entry["position"][1] for entry in regressions], color='blue', label='Regressions')
if cursors:
    cursor_positions = [entry["position"] for entry in cursors]
    plt.plot([pos[0] for pos in cursor_positions], [pos[1] for pos in cursor_positions], color='yellow', label='Cursor Movements')


# Configurar la gráfica
plt.title('Grafica Detecciones')
plt.xlabel('Ancho pantalla')
plt.ylabel('Altura pantalla')
plt.legend()
plt.grid(True)

# Mostrar la gráfica
plt.show()
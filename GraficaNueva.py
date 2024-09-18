import json
import matplotlib.pyplot as plt
from screeninfo import get_monitors

# Leer el archivo cursor_history.json
with open('cursor_history.json', 'r') as json_file:
    cursor_history = json.load(json_file)

# Extraer las posiciones y los tiempos
fixations = [entry['fixation'] for entry in cursor_history]
positions_x = [entry['position'][0] for entry in cursor_history]
positions_y = [entry['position'][1] for entry in cursor_history]

# Obtener las dimensiones de la pantalla
monitor = get_monitors()[0]
screen_width = monitor.width
screen_height = monitor.height
print(f"Screen Width: {screen_width}, Screen Height: {screen_height}")

# Crear la gráfica
plt.figure(figsize=(10, 6))

# Graficar cada punto (x, y)
plt.scatter(positions_x, positions_y, label='Posiciones del cursor')

# Fijar los ejes a las dimensiones de la pantalla
plt.xlim(0, screen_width)
plt.ylim(0, screen_height)

# Añadir etiquetas y título
plt.xlabel('Posición X')
plt.ylabel('Posición Y')
plt.title('Posiciones del cursor en función del tiempo')
plt.legend()

# Mostrar la gráfica
plt.show()
import json

# Ruta al archivo JSON
logs_dir = "C:/Users/jgrios/Desktop/ProyectoEye/logs"
json_file_path = f"{logs_dir}/event_logs.json"

# Leer el archivo JSON
with open(json_file_path, "r") as json_file:
    event_logs = json.load(json_file)

# Extraer coordenadas de los eventos
smooth_cursor_history = event_logs.get("smooth_cursor_history", [])
fixation_points = [(log["to"][0], log["to"][1]) for log in event_logs["fixation_log"]]
saccade_points = [(log["to"][0], log["to"][1]) for log in event_logs["saccade_log"]]
regression_points = [(log["to"][0], log["to"][1]) for log in event_logs["regression_log"]]

# Imprimir los datos para verificar
print("Smooth Cursor History:")
print(smooth_cursor_history[:10])  # Imprimir los primeros 10 puntos

print("\nFixation Points:")
print(fixation_points[:10])  # Imprimir los primeros 10 puntos

print("\nSaccade Points:")
print(saccade_points[:10])  # Imprimir los primeros 10 puntos

print("\nRegression Points:")
print(regression_points[:10])  # Imprimir los primeros 10 puntos

# Convertir smooth_cursor_history a un conjunto para una búsqueda rápida
smooth_cursor_set = set(tuple(point) for point in smooth_cursor_history)

# Verificar si todos los puntos están en smooth_cursor_history
all_fixations_in_smooth = all(tuple(point) in smooth_cursor_set for point in fixation_points)
all_saccades_in_smooth = all(tuple(point) in smooth_cursor_set for point in saccade_points)
all_regressions_in_smooth = all(tuple(point) in smooth_cursor_set for point in regression_points)

print(f"\nAll fixation points in smooth_cursor_history: {all_fixations_in_smooth}")
print(f"All saccade points in smooth_cursor_history: {all_saccades_in_smooth}")
print(f"All regression points in smooth_cursor_history: {all_regressions_in_smooth}")

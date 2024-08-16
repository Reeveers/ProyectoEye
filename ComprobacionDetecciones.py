import json

# Ruta al archivo JSON
logs_dir = "C:/Users/jgrios/Desktop/ProyectoEye/logs"
json_file_path = f"{logs_dir}/event_logs.json"

# Leer el archivo JSON
with open(json_file_path, "r") as json_file:
    event_logs = json.load(json_file)

# Extraer coordenadas de los eventos
smooth_cursor_history = event_logs.get("smooth_cursor_history", [])
fixation_points = [(log["position"][0], log["position"][1]) for log in smooth_cursor_history if log["type"] == "fixation"]
saccade_points = [(log["position"][0], log["position"][1]) for log in smooth_cursor_history if log["type"] == "saccade"]
regression_points = [(log["position"][0], log["position"][1]) for log in smooth_cursor_history if log["type"] == "regression"]

# Convertir smooth_cursor_history a un conjunto para una búsqueda rápida
smooth_cursor_set = set((log["position"][0], log["position"][1]) for log in smooth_cursor_history)

# Verificar si todos los puntos están en smooth_cursor_history
all_fixations_in_smooth = all(point in smooth_cursor_set for point in fixation_points)
all_saccades_in_smooth = all(point in smooth_cursor_set for point in saccade_points)
all_regressions_in_smooth = all(point in smooth_cursor_set for point in regression_points)

print(f"All fixation points in smooth_cursor_history: {all_fixations_in_smooth}")
print(f"All saccade points in smooth_cursor_history: {all_saccades_in_smooth}")
print(f"All regression points in smooth_cursor_history: {all_regressions_in_smooth}")
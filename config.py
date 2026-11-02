"""
Configuración central del Visor BIPV Sumicol.

Todo lo "técnico" (nombres de analizadores, sensores, umbrales de filtrado)
vive aquí. La app y el script de datos lo leen de este archivo, así que si
algo cambia (otra base de datos, otro umbral) solo se toca este archivo.
"""
from pathlib import Path

# --------------------------------------------------------------------------
# Rutas
# --------------------------------------------------------------------------
CARPETA_APP = Path(__file__).resolve().parent            # .../Visor_BIPV
CARPETA_PROYECTO = CARPETA_APP.parent                     # .../Sumicol_Cowork

# Base de datos ORIGINAL (solo se lee, nunca se modifica)
DB_ORIGEN = CARPETA_PROYECTO / "Data" / "Base_Datos_BIPV.db"
# Cronograma de orientaciones (Excel, hoja "seguimiento": INICIO, FIN, ORIENTACION)
CRONOGRAMA_XLSX = CARPETA_PROYECTO / "Data" / "update_cronograma_bipv.xlsx"
CRONOGRAMA_HOJA = "seguimiento"

# Base de datos LIVIANA que usa la plataforma (la genera preparar_datos.py)
DB_VISOR = CARPETA_APP / "data" / "visor.db"

# --------------------------------------------------------------------------
# Instalación
# --------------------------------------------------------------------------
AREA_PANEL_M2 = 0.72

# Caras: clave interna -> datos para mostrar
CARAS = {
    "superior":  {"nombre": "Cara superior",  "angulo": 0,  "eload": "Eload3", "etiqueta": "Superior (0°)", "sensor_irr": "IR3"},
    "inclinada": {"nombre": "Cara inclinada", "angulo": 60, "eload": "Eload2", "etiqueta": "Inclinada (60°)", "sensor_irr": "IR1"},
    "vertical":  {"nombre": "Cara vertical",  "angulo": 90, "eload": "Eload1", "etiqueta": "Vertical (90°)", "sensor_irr": "IR2"},
}
ORDEN_CARAS = ["superior", "inclinada", "vertical"]

# Transmitancia (%) de cada posición de panel en cada analizador
TRANSMITANCIA = {
    "Eload1": {"P1": 30, "P2": 80, "P3": 10, "P4": 40},
    "Eload2": {"P1": 10, "P2": 80, "P3": 40, "P4": 30},
    "Eload3": {"P1": 40, "P2": 10, "P3": 30, "P4": 80},
}
VIDRIOS = [10, 30, 40, 80]

# Cambios de sensor de irradiancia en el tiempo (por cara).
# Desde cada fecha-hora indicada la cara usa ese sensor; None = sin sensor (no hay irradiancia).
# Cara superior: IR3 dejó de registrar el 21-jun-2026 11:35 y el 30-jul-2026 se instaló IR4 en su lugar.
CAMBIOS_SENSOR_IRR = {
    "superior": [("2026-06-21 11:36", None), ("2026-07-30 09:40", "IR4")],
}

# Sensores de temperatura de los vidrios (solo cara superior)
SENSOR_TEMP_VIDRIO = {"Eload3_P2": "TS11", "Eload3_P3": "TS10", "Eload3_P1": "TS9", "Eload3_P4": "TS8"}
# Sensor de temperatura ambiente de referencia
SENSOR_TEMP_AMBIENTE = "TA4"
# Sensor de velocidad del viento (m/s)
SENSOR_VIENTO = "W_Sp23"

# --------------------------------------------------------------------------
# Procesamiento
# --------------------------------------------------------------------------
# Corrección lineal de la irradiancia de referencia: G_corr = a*G + b
CORR_IRR_A = 1.2240
CORR_IRR_B = -34.3052

# Ventana horaria analizada: desde HORA_INICIO:00 hasta antes de HORA_FIN:00
HORA_INICIO = 5
HORA_FIN = 19

# Filtro híbrido por transmitancia (etapa 1: límites físicos frente a la potencia STC)
PARAMS_LIMPIEZA = {
    10: {"stc_pmax": 90.0, "ghost_pct": 0.04},
    30: {"stc_pmax": 70.0, "ghost_pct": 0.05},
    40: {"stc_pmax": 60.0, "ghost_pct": 0.05},
    80: {"stc_pmax": 20.0, "ghost_pct": 0.06},
}
IRR_MIN = 10          # W/m² (irradiancia corregida)
IRR_MAX = 1300        # W/m² (irradiancia corregida)
IRR_LOGICA = 100      # W/m² umbral para "potencia fantasma" / "panel muerto"
MIN_P_PCT = 0.005     # fracción de la potencia STC por debajo de la cual se descarta
# Etapa 2: "tubo" estadístico sobre la densidad de potencia
TUBO_BIN = 10         # W/m²
TUBO_Q_BAJO, TUBO_Q_ALTO = 0.20, 0.80
TUBO_VENTANA = 15     # bins para el suavizado
TUBO_EXPANSION = 0.5  # fracción del rango intercuartílico
TUBO_MARGEN_MIN = 4.0 # W/m²

# Un día de un panel cuenta como válido para energía si tiene al menos
# este número de mediciones limpias (minutos) dentro de la ventana horaria.
UMBRAL_REGISTROS_DIA = 470

# Eficiencia: solo minutos con irradiancia corregida >= este valor
IRR_MIN_EFICIENCIA = 100

# Un día cuenta como válido para irradiancia/HSP si tiene al menos esta
# fracción de los minutos que el equipo registraba normalmente por día
# (el sistema medía de 6:00 a 18:00, es decir ~720 minutos).
MINUTOS_ESPERADOS_DIA = 720
FRACCION_MIN_DIA_IRR = 0.80

# Viento: se descartan lecturas <= 0 y mayores a este valor (m/s)
VIENTO_MAX = 10.0
# Temperaturas plausibles (°C)
TEMP_MIN, TEMP_MAX = -5.0, 90.0

# Muestreo para la gráfica de dispersión potencia vs irradiancia
DISPERSION_MINUTOS = 10

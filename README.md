# Visor BIPV Sumicol · Proyecto Integra

Plataforma web (Dash + Plotly) con los datos históricos del prototipo BIPV instalado en Sumicol:
12 vidrios fotovoltaicos semitransparentes (10, 30, 40 y 80 % de transmitancia) en tres caras (0°, 60° y 90°).

## Usarla en el computador (3 pasos)

Abre una terminal en esta carpeta (`Visor_BIPV`) y ejecuta:

```bash
pip install -r requirements.txt     # 1. instalar dependencias (la primera vez y cuando cambie requirements.txt)
python preparar_datos.py            # 2. generar data/visor.db desde la base original
python app.py                       # 3. abrir http://127.0.0.1:8050 en el navegador
```

El paso 2 tarda menos de un minuto. `data/visor.db` ya viene generada con la base actual, así que
puedes saltarlo hasta que cambies la base de datos o el cronograma.

## Cuando llegue la base de datos nueva o cambie el cronograma

1. Reemplaza `../Data/Base_Datos_BIPV.db` (y/o `../Data/update_cronograma_bipv.xlsx`, hoja `seguimiento`,
   columnas `INICIO`, `FIN`, `ORIENTACION`).
2. Ejecuta `python preparar_datos.py`.
3. Reinicia `python app.py`.

Las fechas de la plataforma (rango del proyecto, rangos rápidos, meses) se leen de los datos,
así que no hay que cambiar nada en el código.

Si los archivos están en otra ubicación:
`python preparar_datos.py --origen "ruta/Base.db" --cronograma "ruta/cronograma.xlsx"`

## Qué hace `preparar_datos.py`

Lee la base original **solo en lectura** (nunca la modifica) y genera `data/visor.db` con:

| Paso | Detalle |
|---|---|
| Irradiancia | `irradiancia_ref` corregida: `1.2240·G − 34.3052` (negativos → 0). Donde `irradiancia_ref` está vacía (mar–jun 2026) se completa con el mismo sensor (IR1/IR2/IR3) de `meteorologia_data` en el mismo minuto. |
| Ventana horaria | Solo datos de 5:00 a 19:00. |
| Filtro de paneles | Etapa 1: límites frente a la potencia STC (potencia fantasma / panel muerto). Etapa 2: tubo estadístico Q20–Q80 por bins de 10 W/m², suavizado y ampliado. |
| Días válidos (energía) | Un día de un panel cuenta si tiene ≥ 470 mediciones limpias. |
| Eficiencia | `P / (G_corregida × 0,72 m²)`, solo con G ≥ 100 W/m². |
| HSP | Suma horaria de la irradiancia corregida / 1000, por cara; día válido con ≥ 80 % de los minutos habituales. |
| Temperatura ambiente | Sensor TA4. Vidrios de la cara superior: TS11 (10 %), TS10 (30 %), TS9 (40 %), TS8 (80 %). |
| Viento | Se descartan lecturas ≤ 0 y > 10 m/s. |

Todos los umbrales y la correspondencia de sensores están en `config.py`.

## Estructura

```
Visor_BIPV/
├── app.py              # aplicación Dash (navegación, filtros, selector de fechas)
├── paginas.py          # contenido de Resumen, Clima, Energía y Desempeño
├── graficas.py         # gráficas Plotly con el estilo de la plataforma
├── componentes.py      # encabezado, pie, filtros, tarjetas
├── datos.py            # consultas a data/visor.db
├── config.py           # rutas, sensores, umbrales
├── preparar_datos.py   # genera data/visor.db
├── data/visor.db       # base liviana (≈20 MB)
└── assets/             # estilo.css, fuentes (fonts/), logos, fotos, capturas de la guía
```

## Publicarla en internet (más adelante)

La app ya está lista para servidores: `server = app.server` en `app.py` y `gunicorn` en
`requirements.txt`. Opciones gratuitas: **Hugging Face Spaces** (Docker) o **Render** (plan free).
Se sube esta carpeta, incluida `data/visor.db` (no hace falta subir la base original de 742 MB),
y se usa el comando de inicio `gunicorn app:server`.

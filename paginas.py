"""Contenido de cada pestaña."""
from datetime import date

from dash import dcc, html

import config as C
import datos as D
import graficas as G
from componentes import aviso, f_corta, kpi, tarjeta_grafica

TITULOS = {
    "/clima": ("Clima y recurso solar",
               "Cuánto sol recibió cada cara, qué tan calientes estuvieron el ambiente y los vidrios, y cuánto viento hubo."),
    "/energia": ("Energía generada",
                 "Energía de cada vidrio seleccionado en la cara elegida."),
    "/desempeno": ("Desempeño: potencia y eficiencia",
                   "Cómo responde cada vidrio al sol a lo largo del día. La eficiencia es el porcentaje de la energía "
                   "solar que llega al vidrio y se convierte en electricidad."),
}


def _num(x, dec=1):
    return f"{x:,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")


# =================================================================== RESUMEN
def resumen():
    meta = D.metadatos()
    ini, fin = date.fromisoformat(meta["fecha_inicio"]), date.fromisoformat(meta["fecha_fin"])
    meses = max(1, round((fin - ini).days / 30.44))
    crono = D.cronograma()
    caras = [
        ("0°", "Cara superior", "Siempre orientada hacia el cenit (mira al cielo)"),
        ("60°", "Cara inclinada", "Se giró entre Norte, Sur, Este y Oeste"),
        ("90°", "Cara vertical", "Se giró entre Norte, Sur, Este y Oeste"),
    ]
    pasos = [
        ("1", "Elige los filtros", "Un rango de fechas (o un rango rápido), una cara y los vidrios que quieres "
                                   "comparar. Aplican a todas las pestañas.", "captura-filtros.png"),
        ("2", "Mira el clima", "Radiación solar, horas de sol, temperatura ambiente y de los vidrios, y viento.",
         "captura-clima.png"),
        ("3", "Compara la energía", "Cuánta energía generó cada vidrio por día, en total y en promedio.",
         "captura-energia.png"),
        ("4", "Revisa el desempeño", "Potencia y eficiencia de cada vidrio a lo largo del día.",
         "captura-desempeno.png"),
    ]
    return html.Div([
        html.Section(className="hero", children=html.Div(className="contenedor hero-int", children=[
            html.Div(className="hero-texto", children=[
                html.Div("Prototipo BIPV · Sumicol, Medellín", className="ceja"),
                html.H1("Vidrios fotovoltaicos que generan energía en la fachada"),
                html.P("Esta plataforma muestra los datos históricos del prototipo de integración fotovoltaica en "
                       "edificaciones (BIPV) instalado en Sumicol: 12 módulos de vidrio semitransparente con cuatro "
                       "niveles de transmitancia, montados en tres caras con inclinaciones de 0°, 60° y 90°.",
                       className="parrafo"),
                html.Div(className="hero-botones", children=[
                    html.A("Explorar los datos", href="/clima", className="btn btn-pri"),
                    html.A("¿Cómo funciona?", href="#como", className="btn btn-sec"),
                ]),
            ]),
            html.Div(className="hero-foto", children=[
                html.Img(src="/assets/img/montaje-1.jpg", alt="Prototipo BIPV en la terraza de Sumicol"),
                html.Div(className="hero-sello", children=[f"{f_corta(meta['fecha_inicio'])} – {f_corta(meta['fecha_fin'])}",
                                                         html.Br(), html.Span("datos históricos")]),
            ]),
        ])),
        html.Div(className="contenedor", children=[
            html.Div(className="rejilla-4 bloque", children=[
                html.Div(className="tarjeta cifra", children=[html.Div(v, className="cifra-v"), html.Div(t)])
                for v, t in [("12", "módulos BIPV de 0,72 m²"), ("3", "caras: 0°, 60° y 90°"),
                             ("4", "vidrios: 10, 30, 40 y 80 % de transmitancia"),
                             (str(meses), "meses de medición, minuto a minuto")]]),
            html.Section(className="bloque-grande dos-col", children=[
                html.Div(className="col-texto", children=[
                    html.Div("El montaje", className="ceja"),
                    html.H2("Tres caras, cuatro vidrios"),
                    html.P("En cada cara se midió, minuto a minuto, la electricidad que produce cada vidrio y la "
                           "radiación solar que recibe. La cara superior mira siempre al cielo; la inclinada y la "
                           "vertical se fueron girando para mirar al Norte, Sur, Este y Oeste.", className="parrafo"),
                    html.Div(className="lista-caras", children=[
                        html.Div(className="cara-item", children=[
                            html.Div(a, className="cara-ang"),
                            html.Div([html.Div(n, className="cara-nom"), html.Div(d, className="cara-det")])])
                        for a, n, d in caras]),
                ]),
                html.Img(src="/assets/img/montaje-2.jpg", alt="Vista del prototipo con las caras inclinada y vertical",
                         className="foto-grande"),
            ]),
            html.Div(className="rejilla-3 galeria", children=[
                html.Img(src="/assets/img/montaje-3.jpg", alt="Detalle de los vidrios semitransparentes"),
                html.Img(src="/assets/img/montaje-4.jpg", alt="Otra vista del prototipo"),
                html.Img(src="/assets/img/montaje-1.jpg", alt="Prototipo con la ciudad de fondo"),
            ]),
            html.Section(className="bloque-grande", children=[
                html.Div("Instrumentación", className="ceja"),
                html.H2("Equipos de medición"),
                html.Div(className="tarjeta equipo-principal", children=[
                    html.Img(src="/assets/img/trazador-iv.jpg", alt="Trazador de curvas I-V instalado en su caja",
                             className="equipo-foto-grande"),
                    html.Div(className="equipo-texto", children=[
                        html.Span("Desarrollo propio del grupo", className="etiqueta-sol"),
                        html.H3("Trazador de curvas I-V"),
                        html.P("Equipo diseñado por el grupo de investigación que, mediante la técnica de carga "
                               "electrónica, recorre la curva corriente–voltaje de cada vidrio fotovoltaico. De cada "
                               "curva se obtiene la potencia máxima, el voltaje y la corriente del vidrio en ese "
                               "momento. Hay un trazador por cara, que mide sus cuatro vidrios minuto a minuto.",
                               className="parrafo"),
                    ]),
                ]),
                html.Div(className="rejilla-4", children=[
                    html.Div(className="tarjeta equipo", children=[
                        html.Img(src=f"/assets/img/{img}", alt=nombre, className="equipo-foto"),
                        html.Div(qué, className="equipo-mide"),
                        html.Div(nombre, className="equipo-nombre"),
                        html.P(desc)])
                    for img, qué, nombre, desc in [
                        ("sensor-radiacion.png", "Radiación solar", "Piranómetro RK200-04",
                         "Mide la radiación solar que llega a cada cara. Hay uno en el mismo plano de cada cara."),
                        ("sensor-termistor.png", "Temperatura de los vidrios", "Termistor NTC B3950 10K de película delgada",
                         "Sensor delgado adherido a los vidrios de la cara superior para medir su temperatura."),
                        ("sensor-ambiente.png", "Temperatura ambiente", "Sensor SHT31",
                         "Mide la temperatura y la humedad del aire alrededor del prototipo."),
                        ("sensor-viento.png", "Viento", "Sensor JXCT-3001-FSFX",
                         "Estación de viento que mide la velocidad del aire sobre el prototipo."),
                    ]]),
            ]),
            html.Section(className="bloque-grande", children=[
                html.Div("Metodología", className="ceja"),
                html.H2("Cómo se procesaron los datos"),
                html.Div(className="rejilla-3", children=[
                    html.Div(className="tarjeta metodo", children=[html.H3(t), html.P(d)]) for t, d in [
                        ("Horario analizado",
                         "Se tienen en cuenta solo las mediciones tomadas entre las 5:00 y las 19:00, cuando hay luz solar."),
                        ("Datos confiables",
                         "Se eliminaron las mediciones que no eran confiables: lecturas fuera de rango, fallas "
                         "momentáneas de los equipos o sombras parciales. Los días con muy pocas mediciones válidas no "
                         "se cuentan en la energía."),
                        ("Promedios",
                         "Las gráficas «a lo largo del día» muestran el promedio de cada hora entre todos los días del "
                         "rango elegido, incluyendo días soleados y nublados."),
                    ]]),
            ]),
            html.Section(id="como", className="bloque-grande", children=[
                html.Div("Guía rápida", className="ceja"),
                html.H2("Cómo usar la plataforma"),
                html.Div(className="rejilla-4", children=[
                    html.Div(className="tarjeta paso", children=[
                        html.Img(src=f"/assets/img/{img}", alt=f"Captura: {t}", className="paso-img"),
                        html.Div(className="paso-tit", children=[html.Span(n, className="paso-num"), t]),
                        html.P(d)]) for n, t, d, img in pasos]),
            ]),
            html.Section(className="bloque-grande dos-col cronograma", children=[
                html.Div(className="col-texto", children=[
                    html.Div("Referencia", className="ceja"),
                    html.H2("Cronograma de orientaciones"),
                    html.P("La cara inclinada y la vertical se giraron periódicamente. Esta tabla indica hacia dónde "
                           "miraba cada una en cada periodo, para interpretar los datos de una fecha concreta.",
                           className="parrafo"),
                ]),
                html.Div(className="tarjeta tabla-caja", children=html.Table(className="tabla", children=[
                    html.Thead(html.Tr([html.Th("Desde"), html.Th("Hasta"),
                                        html.Th("Cara inclinada (60°) mira al"), html.Th("Cara vertical (90°) mira al")])),
                    html.Tbody([html.Tr([html.Td(f_corta(r.desde)), html.Td(f_corta(r.hasta)),
                                         html.Td(r.inclinada, className="fuerte"), html.Td(r.vertical, className="fuerte")])
                                for r in crono.itertuples()]),
                ])),
            ]),
        ]),
    ])


# =================================================================== CLIMA
def clima(f):
    ini, fin, vid = f["ini"], f["fin"], f["vidrios"]
    irr = D.irr_hora(ini, fin)
    hsp = D.hsp_dia(ini, fin)
    met = D.meteo_hora(ini, fin)
    tv = D.temp_vidrio_hora(ini, fin, vid)

    kp = []
    for cara in C.ORDEN_CARAS:
        h = hsp[hsp.cara == cara].hsp
        kp.append(kpi(f"Horas de sol pico · {C.CARAS[cara]['nombre'].lower()}",
                      _num(h.mean()) if len(h) else "–", "h/día", G.COLOR_CARA[cara]))
    ta = met.ta_media.dropna()
    kp.append(kpi("Temperatura ambiente (día)", _num(ta.mean()) if len(ta) else "–", "°C", G.AMBIENTE))

    return html.Div(className="contenedor pila", children=[
        html.Div(className="rejilla-4", children=kp),
        tarjeta_grafica("Radiación solar a lo largo del día",
                        "Línea = promedio por hora · franja = rango donde cae la mitad de los días",
                        G.perfil_irradiancia(irr)),
        tarjeta_grafica("Horas de sol pico por día (HSP)",
                        "Horas equivalentes de sol a 1000 W/m² que recibió cada cara",
                        G.hsp_diaria(hsp)),
        tarjeta_matriz(),
        html.Div(className="rejilla-2", children=[
            tarjeta_grafica("Temperatura de los vidrios y temperatura ambiente",
                            "Cara superior · promedio por hora del día",
                            G.temperatura_vidrios(tv, met)),
            tarjeta_grafica("Velocidad del viento por hora del día",
                            "Promedio por hora",
                            G.viento(met)),
        ]),
        tarjeta_grafica("Temperaturas en el tiempo",
                        "Vidrios de la cara superior y temperatura ambiente · promedio de cada hora · "
                        "usa la barra inferior para acercarte",
                        G.temperaturas_tiempo(tv, met)),
        tarjeta_grafica("Velocidad del viento en el tiempo",
                        "Promedio de cada hora · usa la barra inferior para acercarte",
                        G.viento_tiempo(met)),
    ])


# ------------------------------------------------------------------ matriz de irradiancia
ESCALA_MATRIZ = [(0, (255, 253, 245)), (250, (251, 239, 196)), (500, (246, 216, 115)),
                 (750, (240, 181, 74)), (1000, (229, 138, 46))]


def color_irradiancia(v):
    if v != v:  # NaN
        return "#ffffff"
    v = max(0.0, min(float(v), ESCALA_MATRIZ[-1][0]))
    for (a, ca), (b, cb) in zip(ESCALA_MATRIZ, ESCALA_MATRIZ[1:]):
        if v <= b:
            t = (v - a) / (b - a)
            r, g, bl = (round(x + (y - x) * t) for x, y in zip(ca, cb))
            return f"rgb({r},{g},{bl})"
    return "rgb(229,138,46)"


def tarjeta_matriz():
    return html.Section(className="tarjeta tarjeta-grafica", children=[
        html.Div(className="tarjeta-cab", children=[
            html.H3("Matriz de irradiancia por hora"),
            html.P("Irradiancia promedio de cada hora (W/m²) en cada día · Σ Día = energía solar que llegó "
                   "a la cara ese día (Wh/m²)")]),
        html.Div(className="matriz-barra", children=[
            dcc.RadioItems(id="tabs-matriz", value="superior", inline=True, className="chips",
                           inputClassName="chip-input", labelClassName="chip",
                           options=[{"label": "Cara " + C.CARAS[k]["etiqueta"].lower(), "value": k}
                                    for k in C.ORDEN_CARAS]),
            html.Button("Descargar datos", id="btn-descargar-matriz", n_clicks=0, className="btn btn-sec btn-peq"),
        ]),
        html.Div(className="matriz-info", children=[
            html.Span(id="matriz-texto"),
            html.Button("Ver todo el rango", id="btn-matriz-todo", n_clicks=0, className="enlace-btn")]),
        dcc.Loading(type="dot", color="#1b554f", children=html.Div(id="matriz-tabla", className="matriz-caja")),
        html.Div(className="matriz-leyenda", children=[
            html.Span("0 W/m²"), html.Span(className="matriz-gradiente"), html.Span("1000 W/m² o más")]),
    ])


DIAS_MATRIZ = 7   # por defecto se muestran solo los últimos días del rango (más rápido)


def tabla_matriz(ini, fin, cara, todo=False):
    """Devuelve (tabla, texto informativo, etiqueta del botón)."""
    piv = D.matriz_irradiancia(ini, fin, cara)
    if piv.empty:
        return html.Div("No hay datos de irradiancia para este rango.", className="aviso"), "", "Ver todo el rango"
    n = len(piv)
    if not todo and n > DIAS_MATRIZ:
        piv = piv.tail(DIAS_MATRIZ)
        texto = f"Mostrando los últimos {DIAS_MATRIZ} días del rango elegido."
        boton = f"Ver todo el rango ({n} días)"
    else:
        texto = f"Mostrando {n} días." if n > DIAS_MATRIZ else ""
        boton = f"Ver solo los últimos {DIAS_MATRIZ} días" if n > DIAS_MATRIZ else ""
    horas = list(piv.columns)
    cab = html.Thead(html.Tr([html.Th("Fecha")] + [html.Th(f"{h:02d}") for h in horas]
                             + [html.Th("Σ Día", className="suma")]))
    filas = []
    for fecha, fila in piv.iterrows():
        celdas = [html.Td(f_corta(fecha))]
        for h in horas:
            v = fila[h]
            celdas.append(html.Td("" if v != v else f"{v:.0f}", style={"background": color_irradiancia(v)}))
        celdas.append(html.Td(_num(fila.sum(skipna=True), 0), className="suma"))
        filas.append(html.Tr(celdas))
    return html.Table(className="matriz", children=[cab, html.Tbody(filas)]), texto, boton


def csv_matriz(ini, fin, cara):
    piv = D.matriz_irradiancia(ini, fin, cara)
    if piv.empty:
        return None
    out = piv.round(1)
    out.columns = [f"{h:02d}:00" for h in out.columns]
    out["Suma_dia_Wh_m2"] = piv.sum(axis=1, skipna=True).round(1)
    out.index.name = "fecha"
    return "\ufeff" + out.reset_index().to_csv(sep=";", decimal=",", index=False)


# =================================================================== ENERGÍA
def _barras_html(filas, unidad, dec=0):
    if not filas:
        return html.Div()
    mx = max(v for _, v, _ in filas) or 1
    return html.Div(className="barras-h", children=[
        html.Div(className="barra-fila", children=[
            html.Div(n, className="barra-nom"),
            html.Div(className="barra-pista", children=html.Div(
                className="barra-relleno", style={"width": f"{100 * v / mx:.0f}%", "background": c})),
            html.Div([_num(v, dec), html.Span(f" {unidad}", className="kpi-uni")], className="barra-val"),
        ]) for n, v, c in filas])


def energia(f):
    ini, fin, cara, vid = f["ini"], f["fin"], f["cara"], f["vidrios"]
    if not vid:
        return html.Div(className="contenedor", children=aviso("Elige al menos un vidrio en los filtros."))
    en = D.energia_dia(ini, fin, cara, vid)
    tarjetas, filas = [], []
    for v in C.VIDRIOS:
        if v not in vid:
            continue
        d = en[en.vidrio == v].energia_wh
        col = G.COLOR_VIDRIO[v]
        tarjetas.append(html.Div(className="tarjeta kpi kpi-vidrio", style={"borderTopColor": col}, children=[
            html.Div(G.nombre_vidrio(v), className="kpi-nombre"),
            html.Div("Energía total", className="kpi-etq"),
            html.Div(className="kpi-val", children=[_num(d.sum() / 1000, 2) if len(d) else "–",
                                                     html.Span(" kWh", className="kpi-uni")]),
            html.Div(className="kpi-pie", children=[
                html.Span(["Promedio ", html.B(f"{_num(d.mean(), 0)} Wh/día" if len(d) else "–")]),
                html.Span(f"{len(d)} días")]),
        ]))
        if len(d):
            filas.append((G.nombre_vidrio(v), d.mean(), col))
    nombre_cara = C.CARAS[cara]["nombre"]
    nota = None
    if len(filas) >= 2:
        filas_o = sorted(filas, key=lambda x: -x[1])
        r = filas_o[0][1] / filas_o[-1][1] if filas_o[-1][1] else 0
        nota = html.P(f"En este periodo, el {filas_o[0][0].lower()} generó {_num(r, 1)} veces lo del "
                      f"{filas_o[-1][0].lower()}. Entre más oscuro el vidrio, más luz convierte en electricidad "
                      "y menos deja pasar.", className="nota")
    return html.Div(className="contenedor pila", children=[
        html.Div(className="rejilla-4", children=tarjetas),
        tarjeta_grafica("Energía diaria por vidrio",
                        nombre_cara, G.energia_diaria(en)),
        html.Div(className="rejilla-2", children=[
            tarjeta_grafica("Energía acumulada", "Suma día a día en el periodo elegido", G.energia_acumulada(en)),
            html.Section(className="tarjeta tarjeta-grafica", children=[
                html.Div(className="tarjeta-cab", children=[html.H3("Energía promedio por día"),
                                                            html.P("Promedio en el periodo elegido")]),
                _barras_html(filas, "Wh/día"), nota]),
        ]),
    ])


# =================================================================== DESEMPEÑO
def desempeno(f):
    ini, fin, cara, vid = f["ini"], f["fin"], f["cara"], f["vidrios"]
    if not vid:
        return html.Div(className="contenedor", children=aviso("Elige al menos un vidrio en los filtros."))
    iv = D.iv_hora(ini, fin, cara, vid)
    disp = D.dispersion(ini, fin, cara, vid)
    tarjetas, filas = [], []
    for v in C.VIDRIOS:
        if v not in vid:
            continue
        d = iv[iv.vidrio == v]
        col = G.COLOR_VIDRIO[v]
        p12 = d[d.hora == 12].p_media.mean() / C.AREA_PANEL_M2 if len(d) else float("nan")
        ef = 100 * d.p_ef.sum() / d.ga_ef.sum() if d.ga_ef.sum() > 0 else float("nan")
        tarjetas.append(html.Div(className="tarjeta kpi kpi-vidrio", style={"borderTopColor": col}, children=[
            html.Div(G.nombre_vidrio(v), className="kpi-nombre"),
            html.Div(className="kpi-doble", children=[
                html.Div([html.Div("Potencia 12:00", className="kpi-etq"),
                          html.Div(className="kpi-val kpi-val-s", children=[
                              _num(p12) if p12 == p12 else "–", html.Span(" W/m²", className="kpi-uni")])]),
                html.Div([html.Div("Eficiencia media", className="kpi-etq"),
                          html.Div(className="kpi-val kpi-val-s", children=[
                              _num(ef) if ef == ef else "–", html.Span(" %", className="kpi-uni")])]),
            ]),
        ]))
        if ef == ef:
            filas.append((G.nombre_vidrio(v), ef, col))
    return html.Div(className="contenedor pila", children=[
        html.Div(className="rejilla-4", children=tarjetas),
        html.Div(className="rejilla-2", children=[
            tarjeta_grafica("Potencia a lo largo del día", "Promedio por hora", G.perfil_potencia(iv)),
            tarjeta_grafica("Potencia según la radiación solar",
                            f"Cada punto es el promedio de {C.DISPERSION_MINUTOS} minutos de medición",
                            G.potencia_vs_irradiancia(disp)),
            tarjeta_grafica("Eficiencia a lo largo del día",
                            "Promedio por hora", G.perfil_eficiencia(iv)),
            html.Section(className="tarjeta tarjeta-grafica", children=[
                html.Div(className="tarjeta-cab", children=[html.H3("Eficiencia media por vidrio"),
                                                            html.P("Promedio del periodo elegido")]),
                _barras_html(filas, "%", 1)]),
        ]),
    ])

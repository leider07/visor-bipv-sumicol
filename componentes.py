"""Piezas de interfaz reutilizables: encabezado, pie, filtros y selector de fechas."""
from datetime import date, timedelta

import pandas as pd
from dash import dcc, html

import config as C
from graficas import COLOR_VIDRIO

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
MESES_LARGO = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto",
               "Septiembre", "Octubre", "Noviembre", "Diciembre"]

PAGINAS = [("/", "Resumen"), ("/clima", "Clima"), ("/energia", "Energía"), ("/desempeno", "Desempeño")]


# ---------------------------------------------------------------- fechas
def f_corta(iso):
    d = date.fromisoformat(iso)
    return f"{d.day:02d} {MESES[d.month - 1]} {d.year}"


def rango_texto(ini, fin):
    return f"{f_corta(ini)} – {f_corta(fin)}" if ini != fin else f_corta(ini)


def rangos_rapidos(meta):
    ini, fin = date.fromisoformat(meta["fecha_inicio"]), date.fromisoformat(meta["fecha_fin"])

    def atras(dias):
        return max(ini, fin - timedelta(days=dias - 1)).isoformat()

    def meses_atras(n):
        return max(ini, (pd.Timestamp(fin) - pd.DateOffset(months=n) + pd.Timedelta(days=1)).date()).isoformat()

    r = [("Todo el proyecto", ini.isoformat(), fin.isoformat()),
         ("Último día con datos", fin.isoformat(), fin.isoformat()),
         ("Últimos 7 días", atras(7), fin.isoformat()),
         ("Último mes", meses_atras(1), fin.isoformat()),
         ("Últimos 3 meses", meses_atras(3), fin.isoformat()),
         ("Últimos 6 meses", meses_atras(6), fin.isoformat())]
    for an in range(ini.year, fin.year + 1):
        r.append((f"Año {an}", max(ini, date(an, 1, 1)).isoformat(), min(fin, date(an, 12, 31)).isoformat()))
    return r


def meses_disponibles(meta):
    ini, fin = pd.Timestamp(meta["fecha_inicio"]), pd.Timestamp(meta["fecha_fin"])
    out = []
    for p in pd.period_range(ini, fin, freq="M"):
        a = max(ini, p.start_time).date().isoformat()
        b = min(fin, p.end_time).date().isoformat()
        out.append((f"{MESES_LARGO[p.month - 1]} {p.year}", a, b, p.strftime("%Y-%m")))
    return out


def icono_calendario(tam=18):
    return html.Img(src="/assets/img/calendario.svg", alt="", width=tam, height=tam, className="icono")


def selector_fechas(meta):
    rr = rangos_rapidos(meta)
    meses = meses_disponibles(meta)
    return html.Div(className="selector-fechas", children=[
        html.Span("Fechas", className="filtro-titulo"),
        html.Button(id="btn-fechas", className="btn-fechas", n_clicks=0, **{"aria-haspopup": "dialog"}, children=[
            icono_calendario(),
            html.Span(className="btn-fechas-texto", children=[
                html.Span(id="fechas-rango", className="btn-fechas-rango"),
                html.Span(id="fechas-texto")]),
            html.Img(src="/assets/img/flecha.svg", alt="", width=14, height=14, className="icono"),
        ]),
        html.Div(id="pop-fechas", className="pop-fechas", style={"display": "none"},
                 role="dialog", **{"aria-label": "Elegir rango de fechas"}, children=[
            html.Div(className="pop-col pop-rapidos", children=[
                html.Div("Rangos rápidos", className="pop-cabecera"),
                html.Div(className="pop-lista", children=[
                    html.Button(lbl, id={"type": "preset", "index": i}, n_clicks=0, className="preset")
                    for i, (lbl, _, _) in enumerate(rr)]),
            ]),
            html.Div(className="pop-col pop-personal", children=[
                html.Div("Personalizado", className="pop-cabecera"),
                dcc.Tabs(id="tabs-fechas", value="rango", className="tabs-fechas", children=[
                    dcc.Tab(label="Rango de fechas", value="rango", className="tab", selected_className="tab-activa",
                            children=html.Div(className="pop-rango", children=[
                                html.Label("Fecha inicial", htmlFor="fecha-ini"),
                                dcc.Input(id="fecha-ini", type="date", min=meta["fecha_inicio"],
                                          max=meta["fecha_fin"], className="input-fecha", debounce=True),
                                html.Label("Fecha final", htmlFor="fecha-fin"),
                                dcc.Input(id="fecha-fin", type="date", min=meta["fecha_inicio"],
                                          max=meta["fecha_fin"], className="input-fecha", debounce=True),
                                html.P(f"Hay datos del {f_corta(meta['fecha_inicio'])} al {f_corta(meta['fecha_fin'])}. "
                                       "Los rangos rápidos se cuentan hacia atrás desde el último día con datos.",
                                       className="pop-nota"),
                            ])),
                    dcc.Tab(label="Por mes", value="mes", className="tab", selected_className="tab-activa",
                            children=html.Div(className="pop-meses", children=[
                                html.Button(lbl, id={"type": "mes", "index": key}, n_clicks=0, className="mes")
                                for lbl, _, _, key in meses])),
                ]),
                html.Div(className="pop-acciones", children=[
                    html.Button("Cancelar", id="btn-cancelar", n_clicks=0, className="btn btn-sec"),
                    html.Button("Aplicar", id="btn-aplicar", n_clicks=0, className="btn btn-pri"),
                ]),
            ]),
        ]),
    ])


# ---------------------------------------------------------------- filtros
def barra_filtros(meta):
    opciones_cara = [{"label": C.CARAS[k]["etiqueta"], "value": k} for k in C.ORDEN_CARAS]
    opciones_vid = [{"label": html.Span([html.Span(className="punto", style={"background": COLOR_VIDRIO[v]}),
                                         f"Vidrio {v} %"]), "value": v} for v in C.VIDRIOS]
    return html.Div(className="barra-filtros", children=[
        selector_fechas(meta),
        html.Div(id="grupo-cara", className="grupo-filtro", children=[
            html.Span("Cara (elige una)", className="filtro-titulo"),
            dcc.RadioItems(id="filtro-cara", options=opciones_cara, value="superior", inline=True,
                           className="chips", inputClassName="chip-input", labelClassName="chip"),
        ]),
        html.Div(className="grupo-filtro", children=[
            html.Span("Vidrio (% de transmitancia)", className="filtro-titulo"),
            dcc.Checklist(id="filtro-vidrios", options=opciones_vid, value=list(C.VIDRIOS), inline=True,
                          className="chips", inputClassName="chip-input", labelClassName="chip chip-claro"),
        ]),
        html.Div(id="nota-filtros", className="nota-filtros"),
    ])


# ---------------------------------------------------------------- marco
def encabezado(meta):
    return html.Header(className="encabezado", children=[
        html.Div(className="franja", children=html.Div(className="contenedor franja-int", children=[
            html.Span("Plataforma de monitoreo BIPV · Prototipo Sumicol"),
            html.Span(f"Datos históricos · {rango_texto(meta['fecha_inicio'], meta['fecha_fin'])}"),
        ])),
        html.Div(className="contenedor barra-nav", children=[
            dcc.Link(href="/", className="marca", children=[
                html.Img(src="/assets/img/integra-logo.png",
                         alt="Integra – Plataforma de Integración Fotovoltaica en Edificaciones", className="logo"),
                html.Span(className="separador"),
                html.Span(className="marca-texto", children=["Visor BIPV", html.Br(),
                                                              html.Small("Sumicol · Medellín")]),
            ]),
            html.Nav(**{"aria-label": "Secciones"}, className="nav", children=[
                dcc.Link(nombre, href=ruta, id=f"nav-{i}", className="nav-link")
                for i, (ruta, nombre) in enumerate(PAGINAS)]),
        ]),
    ])


def pie():
    return html.Footer(className="pie", children=[
        html.Div(className="pie-logos", children=html.Div(className="contenedor", children=html.Img(
            src="/assets/img/logos-aliados.png",
            alt="Entidades aliadas: SGR, Universidad de Antioquia, Corantioquia, Sumicol, SAI, Andercol, "
                "Gobernaciones de Antioquia, Caldas, Quindío y Risaralda", className="logos-aliados"))),
        html.Div(className="pie-franja", children=html.Div(className="contenedor pie-int", children=[
            html.Span(className="pie-marca", children=[
                html.Img(src="/assets/img/favicon.png", alt="", className="pie-icono"),
                "Proyecto Integra · Plataforma de Integración Fotovoltaica en Edificaciones"]),
            html.A("proyecto-integra.site", href="https://proyecto-integra.site/", target="_blank", rel="noopener"),
        ])),
    ])


# ---------------------------------------------------------------- tarjetas
def tarjeta_grafica(titulo, subtitulo, figura, extra=None):
    from graficas import CONFIG
    hijos = [html.Div(className="tarjeta-cab", children=[html.H3(titulo), html.P(subtitulo)])]
    hijos.append(dcc.Graph(figure=figura, config=CONFIG, className="grafica"))
    if extra is not None:
        hijos.append(extra)
    return html.Section(className="tarjeta tarjeta-grafica", children=hijos)


def kpi(etiqueta, valor, unidad, color):
    return html.Div(className="tarjeta kpi", children=[
        html.Div(etiqueta, className="kpi-etq"),
        html.Div(className="kpi-val", children=[valor, html.Span(f" {unidad}", className="kpi-uni")]),
        html.Div(className="kpi-barra", style={"background": color}),
    ])


def aviso(texto):
    return html.Div(texto, className="tarjeta aviso")

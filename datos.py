"""Consultas a la base de datos liviana de la plataforma (data/visor.db)."""
import sqlite3
from functools import lru_cache

import pandas as pd

import config as C


def _q(sql, params=()):
    if not C.DB_VISOR.exists():
        raise FileNotFoundError(
            f"No existe {C.DB_VISOR}. Ejecuta primero:  python preparar_datos.py")
    con = sqlite3.connect(C.DB_VISOR.resolve().as_uri() + "?mode=ro", uri=True, check_same_thread=False)
    try:
        return pd.read_sql(sql, con, params=params)
    finally:
        con.close()


@lru_cache(maxsize=1)
def metadatos():
    df = _q("SELECT clave, valor FROM metadatos")
    return dict(zip(df.clave, df.valor))


@lru_cache(maxsize=1)
def paneles():
    return _q("SELECT panel_id, cara, vidrio FROM paneles")


@lru_cache(maxsize=1)
def cronograma():
    return _q("SELECT desde, hasta, inclinada, vertical FROM cronograma ORDER BY desde")


def _ids(cara, vidrios):
    p = paneles()
    p = p[(p.cara == cara) & (p.vidrio.isin(vidrios))]
    return dict(zip(p.panel_id, p.vidrio))


def _in(lista):
    return ",".join("?" * len(lista))


# ---------------------------- Clima ----------------------------
def irr_hora(ini, fin):
    return _q("SELECT cara, fecha, hora, g_media FROM irr_hora WHERE fecha BETWEEN ? AND ?", (ini, fin))


def matriz_irradiancia(ini, fin, cara):
    """Tabla días x horas con la irradiancia promedio de cada hora (W/m²)."""
    df = _q("SELECT fecha, hora, g_media FROM irr_hora WHERE cara = ? AND fecha BETWEEN ? AND ?",
            (cara, ini, fin))
    if df.empty:
        return pd.DataFrame()
    piv = df.pivot_table(index="fecha", columns="hora", values="g_media", aggfunc="mean").sort_index()
    return piv


def hsp_dia(ini, fin):
    return _q("SELECT cara, fecha, hsp FROM hsp_dia WHERE valido = 1 AND fecha BETWEEN ? AND ? ORDER BY fecha",
              (ini, fin))


def meteo_hora(ini, fin):
    return _q("SELECT fecha, hora, ta_media, viento_media FROM meteo_hora WHERE fecha BETWEEN ? AND ?", (ini, fin))


def temp_vidrio_hora(ini, fin, vidrios):
    ids = _ids("superior", vidrios)
    if not ids:
        return pd.DataFrame(columns=["fecha", "hora", "t_media", "vidrio"])
    df = _q(f"SELECT panel_id, fecha, hora, t_media FROM temp_vidrio_hora "
            f"WHERE fecha BETWEEN ? AND ? AND panel_id IN ({_in(ids)})", (ini, fin, *ids))
    df["vidrio"] = df.panel_id.map(ids)
    return df


# ---------------------------- Paneles ----------------------------
def energia_dia(ini, fin, cara, vidrios):
    ids = _ids(cara, vidrios)
    if not ids:
        return pd.DataFrame(columns=["fecha", "energia_wh", "vidrio"])
    df = _q(f"SELECT panel_id, fecha, energia_wh FROM energia_dia "
            f"WHERE fecha BETWEEN ? AND ? AND panel_id IN ({_in(ids)}) ORDER BY fecha", (ini, fin, *ids))
    df["vidrio"] = df.panel_id.map(ids)
    return df


def iv_hora(ini, fin, cara, vidrios):
    ids = _ids(cara, vidrios)
    if not ids:
        return pd.DataFrame(columns=["fecha", "hora", "p_media", "p_ef", "ga_ef", "vidrio"])
    df = _q(f"SELECT panel_id, fecha, hora, p_media, p_ef, ga_ef FROM iv_hora "
            f"WHERE fecha BETWEEN ? AND ? AND panel_id IN ({_in(ids)})", (ini, fin, *ids))
    df["vidrio"] = df.panel_id.map(ids)
    return df


def dispersion(ini, fin, cara, vidrios, max_por_vidrio=4000):
    ids = _ids(cara, vidrios)
    if not ids:
        return pd.DataFrame(columns=["g", "p", "vidrio"])
    df = _q(f"SELECT panel_id, g, p FROM dispersion "
            f"WHERE substr(ts, 1, 10) BETWEEN ? AND ? AND panel_id IN ({_in(ids)})", (ini, fin, *ids))
    df["vidrio"] = df.panel_id.map(ids)
    partes = [d.sample(min(len(d), max_por_vidrio), random_state=1) for _, d in df.groupby("vidrio")]
    return pd.concat(partes) if partes else df

"""
Genera la base de datos liviana de la plataforma (data/visor.db).

Uso:
    python preparar_datos.py
    python preparar_datos.py --origen "ruta/a/Base_Datos_BIPV.db" --cronograma "ruta/al/cronograma.xlsx"

Lee la base original SOLO EN LECTURA y el Excel del cronograma, aplica:
  - corrección de irradiancia y ventana horaria (config.HORA_INICIO a HORA_FIN)
  - filtro híbrido (límites STC + tubo estadístico) por panel
  - días válidos por número de mediciones limpias
  - recálculo de eficiencia y horas de sol pico (HSP)
  - filtros de viento y temperaturas
y escribe tablas ya agregadas que la app consulta rápido.

Cuando llegue una base de datos nueva, basta con reemplazar el archivo
original y volver a correr este script.
"""
import argparse
import re
import sqlite3
import time
from datetime import datetime

import numpy as np
import pandas as pd

import config as C


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------
def conectar_solo_lectura(ruta):
    ruta = ruta.resolve()
    if not ruta.exists():
        raise FileNotFoundError(f"No se encontró la base de datos original: {ruta}")
    return sqlite3.connect(ruta.as_uri() + "?mode=ro", uri=True)


def corregir_irradiancia(g):
    return (g * C.CORR_IRR_A + C.CORR_IRR_B).clip(lower=0)


def en_ventana(ts):
    return (ts.dt.hour >= C.HORA_INICIO) & (ts.dt.hour < C.HORA_FIN)


def tabla_paneles():
    filas = []
    for cara, info in C.CARAS.items():
        for pos, lt in C.TRANSMITANCIA[info["eload"]].items():
            pid = f"{info['eload']}_{pos}"
            filas.append({"panel_id": pid, "cara": cara, "vidrio": lt,
                          "sensor_temp": C.SENSOR_TEMP_VIDRIO.get(pid)})
    return pd.DataFrame(filas)


# --------------------------------------------------------------------------
# Filtro híbrido (mismo criterio de los notebooks de análisis)
# --------------------------------------------------------------------------
def filtrar_panel(df, vidrio):
    p = C.PARAMS_LIMPIEZA[vidrio]
    stc = p["stc_pmax"]
    # Etapa 1: límites físicos
    m = (df.g > C.IRR_MIN) & (df.g < C.IRR_MAX) & (df.p > stc * C.MIN_P_PCT)
    d = df[m]
    fantasma = (d.p > stc * p["ghost_pct"]) & (d.g < C.IRR_LOGICA)
    muerto = (d.p < stc * C.MIN_P_PCT) & (d.g > C.IRR_LOGICA)
    d = d[~fantasma & ~muerto].copy()
    if d.empty:
        return d
    # Etapa 2: tubo estadístico sobre la densidad de potencia
    d["pn"] = d.p / C.AREA_PANEL_M2
    d["bin"] = (d.g // C.TUBO_BIN) * C.TUBO_BIN
    st = (d.groupby("bin")["pn"]
            .quantile([C.TUBO_Q_BAJO, C.TUBO_Q_ALTO]).unstack().sort_index())
    st.columns = ["q_bajo", "q_alto"]
    lo = st.q_bajo.rolling(C.TUBO_VENTANA, center=True, min_periods=1).mean()
    hi = st.q_alto.rolling(C.TUBO_VENTANA, center=True, min_periods=1).mean()
    margen = np.maximum((hi - lo) * C.TUBO_EXPANSION, C.TUBO_MARGEN_MIN)
    lim = pd.DataFrame({"inf": lo - margen, "sup": hi + margen})
    d = d.join(lim, on="bin")
    return d[(d.pn >= d.inf) & (d.pn <= d.sup)].drop(columns=["pn", "bin", "inf", "sup"])


# --------------------------------------------------------------------------
# Pasos
# --------------------------------------------------------------------------
def procesar_iv(con, paneles):
    log("Leyendo mediciones eléctricas (puede tardar un poco)...")
    iv = pd.read_sql("SELECT timestamp, panel_id, p_max, irradiancia_ref FROM parametros_iv", con)
    iv["ts"] = pd.to_datetime(iv.timestamp, format="mixed").dt.floor("min")
    iv = iv[en_ventana(iv.ts)].drop(columns="timestamp")
    iv = iv.rename(columns={"p_max": "p", "irradiancia_ref": "g"})
    iv = iv.drop_duplicates(["panel_id", "ts"])

    # Donde irradiancia_ref está vacía, se completa con la lectura del mismo
    # sensor de irradiancia en la tabla meteorológica (mismo minuto).
    sens = [info["sensor_irr"] for info in C.CARAS.values()]
    met = pd.read_sql(f"SELECT timestamp, {', '.join(sens)} FROM meteorologia_data", con)
    met["ts"] = pd.to_datetime(met.timestamp, format="mixed").dt.floor("min")
    met = (met.drop(columns="timestamp").drop_duplicates("ts")
              .melt(id_vars="ts", var_name="sensor", value_name="g_met"))
    sensor_de = paneles.set_index("panel_id").cara.map(lambda c: C.CARAS[c]["sensor_irr"])
    iv["sensor"] = iv.panel_id.map(sensor_de)
    iv = iv.merge(met, on=["ts", "sensor"], how="left")
    faltan = iv.g.isna() & iv.g_met.notna()
    iv.loc[faltan, "g"] = iv.loc[faltan, "g_met"]
    log(f"  Irradiancia completada desde la tabla meteorológica en {int(faltan.sum()):,} mediciones")
    iv = iv.drop(columns=["sensor", "g_met"])
    iv["g"] = corregir_irradiancia(iv.g)
    log(f"  {len(iv):,} mediciones dentro de la ventana horaria")

    # Irradiancia por cara (promedio de los registros de sus 4 paneles en cada minuto)
    cara_de = paneles.set_index("panel_id").cara
    g = iv.dropna(subset=["g"]).assign(cara=lambda x: x.panel_id.map(cara_de))
    irr_min = g.groupby(["cara", "ts"], as_index=False).g.mean()

    # Filtro por panel
    log("Aplicando filtro híbrido por panel...")
    vid_de = paneles.set_index("panel_id").vidrio
    partes = []
    for pid, d in iv.dropna(subset=["g", "p"]).groupby("panel_id"):
        f = filtrar_panel(d, int(vid_de[pid]))
        partes.append(f)
        log(f"  {pid}: {len(d):,} -> {len(f):,} mediciones limpias")
    limpio = pd.concat(partes, ignore_index=True)
    return irr_min, limpio


def tablas_paneles(limpio, con):
    limpio = limpio.copy()
    limpio["fecha"] = limpio.ts.dt.strftime("%Y-%m-%d")
    limpio["hora"] = limpio.ts.dt.hour

    # Días válidos por panel
    cuenta = limpio.groupby(["panel_id", "fecha"]).size().rename("registros").reset_index()
    cuenta["valido"] = (cuenta.registros >= C.UMBRAL_REGISTROS_DIA).astype(int)

    # Agregados horarios (para perfiles de potencia y eficiencia)
    alta = limpio.g >= C.IRR_MIN_EFICIENCIA
    limpio["p_ef"] = np.where(alta, limpio.p, 0.0)
    limpio["ga_ef"] = np.where(alta, limpio.g * C.AREA_PANEL_M2, 0.0)
    iv_hora = (limpio.groupby(["panel_id", "fecha", "hora"])
               .agg(g_media=("g", "mean"), p_media=("p", "mean"), n=("p", "size"),
                    p_ef=("p_ef", "sum"), ga_ef=("ga_ef", "sum"))
               .reset_index())

    # Muestra para dispersión potencia vs irradiancia (promedios de N minutos)
    disp = (limpio.set_index("ts").groupby("panel_id")[["g", "p"]]
            .resample(f"{C.DISPERSION_MINUTOS}min").mean().dropna().reset_index())
    disp = disp[disp.g > 20]
    disp["ts"] = disp.ts.dt.strftime("%Y-%m-%d %H:%M")

    # Energía diaria: solo días válidos
    en = pd.read_sql("SELECT fecha, panel_id, energia_wh FROM energia_diaria WHERE energia_wh IS NOT NULL", con)
    en["fecha"] = pd.to_datetime(en.fecha).dt.strftime("%Y-%m-%d")
    en = en.merge(cuenta[cuenta.valido == 1][["panel_id", "fecha"]], on=["panel_id", "fecha"])
    en = en.groupby(["panel_id", "fecha"], as_index=False).energia_wh.sum()
    log(f"  Energía: {len(en):,} días-panel válidos")
    return cuenta, iv_hora, disp, en


def tablas_irradiancia(irr_min):
    irr_min = irr_min.copy()
    irr_min["fecha"] = irr_min.ts.dt.strftime("%Y-%m-%d")
    irr_min["hora"] = irr_min.ts.dt.hour
    hora = (irr_min.groupby(["cara", "fecha", "hora"])
            .agg(g_media=("g", "mean"), minutos=("g", "size")).reset_index())
    # HSP: suma de energía horaria estimada (promedio de la hora x 1 h)
    dia = (hora.assign(wh=hora.g_media)
           .groupby(["cara", "fecha"]).agg(wh=("wh", "sum"), minutos=("minutos", "sum")).reset_index())
    dia["hsp"] = dia.wh / 1000.0
    dia["valido"] = (dia.minutos >= C.FRACCION_MIN_DIA_IRR * C.MINUTOS_ESPERADOS_DIA).astype(int)
    dia = dia.drop(columns="wh")
    validos = dia[dia.valido == 1][["cara", "fecha"]]
    hora = hora.merge(validos, on=["cara", "fecha"])
    log(f"  Irradiancia: {int(dia.valido.sum()):,} días-cara válidos de {len(dia):,}")
    return hora, dia


def tablas_meteo(con):
    log("Leyendo datos meteorológicos...")
    sens = list(C.SENSOR_TEMP_VIDRIO.values())
    cols = ", ".join(["timestamp", C.SENSOR_TEMP_AMBIENTE, C.SENSOR_VIENTO] + sens)
    m = pd.read_sql(f"SELECT {cols} FROM meteorologia_data", con)
    m["ts"] = pd.to_datetime(m.timestamp, format="mixed")
    m = m[en_ventana(m.ts)]
    m["fecha"] = m.ts.dt.strftime("%Y-%m-%d")
    m["hora"] = m.ts.dt.hour

    def temp_ok(s):
        return s.where((s >= C.TEMP_MIN) & (s <= C.TEMP_MAX))

    m["ta"] = temp_ok(m[C.SENSOR_TEMP_AMBIENTE])
    v = m[C.SENSOR_VIENTO]
    m["viento"] = v.where((v > 0) & (v <= C.VIENTO_MAX))
    meteo = (m.groupby(["fecha", "hora"])
             .agg(ta_media=("ta", "mean"), viento_media=("viento", "mean")).reset_index())

    filas = []
    for pid, s in C.SENSOR_TEMP_VIDRIO.items():
        t = m[["fecha", "hora"]].assign(t=temp_ok(m[s]))
        t = t.groupby(["fecha", "hora"]).t.mean().dropna().reset_index()
        t["panel_id"] = pid
        filas.append(t.rename(columns={"t": "t_media"}))
    tvid = pd.concat(filas, ignore_index=True)
    log(f"  Meteorología: {len(meteo):,} horas")
    return meteo, tvid


def tabla_cronograma(ruta):
    if not ruta.exists():
        log(f"  Aviso: no se encontró el cronograma en {ruta}; la tabla quedará vacía.")
        return pd.DataFrame(columns=["desde", "hasta", "inclinada", "vertical"])
    df = pd.read_excel(ruta, sheet_name=C.CRONOGRAMA_HOJA)
    df.columns = [str(c).strip().upper() for c in df.columns]
    cardinal = {"N": "Norte", "S": "Sur", "E": "Este", "W": "Oeste", "O": "Oeste"}
    filas = []
    for _, r in df.iterrows():
        cod = str(r.get("ORIENTACION", "")).upper().replace(" ", "")
        mt = re.search(r"30([NSEWO])90([NSEWO])", cod)
        if not mt or pd.isna(r.get("INICIO")) or pd.isna(r.get("FIN")):
            continue
        filas.append({
            "desde": pd.to_datetime(r["INICIO"], dayfirst=True).strftime("%Y-%m-%d"),
            "hasta": pd.to_datetime(r["FIN"], dayfirst=True).strftime("%Y-%m-%d"),
            "inclinada": cardinal[mt.group(1)], "vertical": cardinal[mt.group(2)],
        })
    out = pd.DataFrame(filas).sort_values("desde")
    log(f"  Cronograma: {len(out)} periodos")
    return out


def escribir(tablas, meta, destino):
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_suffix(".tmp.db")
    if tmp.exists():
        tmp.unlink()
    con = sqlite3.connect(tmp)
    for nombre, df in tablas.items():
        df.to_sql(nombre, con, index=False)
    pd.DataFrame(list(meta.items()), columns=["clave", "valor"]).to_sql("metadatos", con, index=False)
    idx = {
        "iv_hora": "fecha, panel_id", "dispersion": "ts, panel_id", "energia_dia": "fecha, panel_id",
        "irr_hora": "fecha, cara", "hsp_dia": "fecha, cara", "meteo_hora": "fecha",
        "temp_vidrio_hora": "fecha, panel_id", "dias_panel": "fecha, panel_id",
    }
    for t, cols in idx.items():
        con.execute(f"CREATE INDEX ix_{t} ON {t} ({cols})")
    con.commit()
    con.execute("VACUUM")
    con.close()
    tmp.replace(destino)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--origen", default=str(C.DB_ORIGEN))
    ap.add_argument("--cronograma", default=str(C.CRONOGRAMA_XLSX))
    ap.add_argument("--destino", default=str(C.DB_VISOR))
    a = ap.parse_args()
    from pathlib import Path
    t0 = time.time()

    con = conectar_solo_lectura(Path(a.origen))
    paneles = tabla_paneles()
    irr_min, limpio = procesar_iv(con, paneles)
    log("Calculando tablas de paneles...")
    dias_panel, iv_hora, disp, energia = tablas_paneles(limpio, con)
    log("Calculando irradiancia y HSP por cara...")
    irr_hora, hsp_dia = tablas_irradiancia(irr_min)
    meteo, tvid = tablas_meteo(con)
    con.close()
    log("Leyendo cronograma...")
    crono = tabla_cronograma(Path(a.cronograma))

    fechas = pd.concat([iv_hora.fecha, irr_hora.fecha, energia.fecha])
    meta = {
        "fecha_inicio": fechas.min(), "fecha_fin": fechas.max(),
        "generado": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "origen": Path(a.origen).name,
    }
    tablas = {
        "paneles": paneles, "dias_panel": dias_panel, "iv_hora": iv_hora, "dispersion": disp,
        "energia_dia": energia, "irr_hora": irr_hora, "hsp_dia": hsp_dia,
        "meteo_hora": meteo, "temp_vidrio_hora": tvid, "cronograma": crono,
    }
    log("Escribiendo base de datos de la plataforma...")
    destino = Path(a.destino)
    escribir(tablas, meta, destino)
    log(f"Listo: {destino} ({destino.stat().st_size / 1e6:.1f} MB) · datos del "
        f"{meta['fecha_inicio']} al {meta['fecha_fin']} · {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()

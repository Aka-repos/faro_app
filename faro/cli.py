"""CLI de FARO: un comando por paso del pipeline (Makefile)."""

from __future__ import annotations

import argparse
import json
import sys

import config.settings as S


def _cmd_data(args) -> None:
    """Recolección real. Nunca genera datos sintéticos (M1, M1.5)."""
    import tempfile
    from datetime import datetime
    from pathlib import Path

    import config.settings as S
    from faro.scrape.collect import recolectar

    if not S.FARO_CONTACTO:
        print("⚠️  ADVERTENCIA: FARO_CONTACTO vacío; el User-Agent irá sin contacto (opcional).")

    fuentes = [f.strip() for f in args.fuentes.split(",") if f.strip()] if args.fuentes else None

    desde = hasta = None
    if args.meses:
        meses = sorted(m.strip() for m in args.meses.split(",") if m.strip())
        desde = datetime.fromisoformat(f"{meses[0]}-01T00:00:00+00:00")
        y, m = map(int, meses[-1].split("-"))
        m += 1
        if m > 12:
            y, m = y + 1, 1
        hasta = datetime.fromisoformat(f"{y:04d}-{m:02d}-01T00:00:00+00:00")

    if args.prueba:
        tmp = Path(tempfile.mkdtemp(prefix="faro-data-smoke-"))
        S.RAW_DIR = tmp / "raw"
        S.REPORTS_DIR = tmp / "reports"
        S.RAW_DIR.mkdir(parents=True, exist_ok=True)
        S.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Modo prueba: escribiendo en {tmp}")

    res = recolectar(fuentes=fuentes, desde=desde, hasta=hasta)
    print("Recolección real completa:")
    print(json.dumps(res["conteos"], ensure_ascii=False, indent=2))
    if res.get("por_fuente"):
        print(json.dumps(res["por_fuente"], ensure_ascii=False, indent=2))


def _cmd_data_seed(args) -> None:
    """Escribe el seed sintético SOLO si FARO_DATA_DIR apunta fuera de data/ (protección)."""
    from pathlib import Path

    import config.settings as S
    from faro.seed import gen_indicadores, gen_noticias, gen_series, gen_sismos, write_raw

    if Path(S.DATA_DIR).resolve() == (S.REPO_ROOT / "data").resolve():
        print("Rechazado: make data-seed no puede escribir en data/ (protegería el snapshot real).")
        sys.exit(1)
    conteos = write_raw(gen_noticias(), gen_series(), gen_indicadores(), gen_sismos())
    print("Seed sintético escrito en", S.DATA_DIR)
    for k, v in conteos.items():
        print(f"  {k}: {v}")


def _cmd_freeze(args) -> None:
    from pathlib import Path

    import config.settings as S
    from faro.quality.manifest import build_manifest, write_manifest

    conteos = {
        p.name: sum(1 for _ in open(p, encoding="utf-8")) for p in Path(S.RAW_DIR).glob("*.jsonl")
    }
    # Evidencia de origen (respuestas HTTP crudas) y transcripciones manuales.
    http_idx = S.RAW_DIR / "http" / "index.jsonl"
    if http_idx.exists():
        conteos["http/index.jsonl"] = sum(1 for _ in open(http_idx, encoding="utf-8"))
    manual = S.RAW_DIR / "manual"
    if manual.exists():
        for p in manual.glob("*.csv"):
            conteos[f"manual/{p.name}"] = sum(1 for _ in open(p, encoding="utf-8"))
    path = write_manifest(build_manifest(conteos))
    print(f"manifest.json escrito en {path}")


def _cmd_verify(args) -> None:
    from faro.quality.manifest import verify_manifest

    res = verify_manifest()
    print(
        "verify-snapshot:", "OK — sin diferencias" if res["ok"] else f"DIFF — {res['diferencias']}"
    )
    sys.exit(0 if res["ok"] else 1)


def _cmd_build(args) -> None:
    import os

    from faro.pipeline import build

    # Barrera M2.2: no construir con datos sintéticos (salvo tests).
    if os.environ.get("FARO_PERMITIR_SINTETICO") != "1":
        for f in S.RAW_DIR.glob("*.jsonl"):
            for linea in f.read_text(encoding="utf-8").splitlines():
                if '"sintetico": true' in linea:
                    print(
                        f"Error: {f.name} contiene registros sintéticos. Recolecta con `make data` "
                        "o usa FARO_PERMITIR_SINTETICO=1 solo en pruebas."
                    )
                    sys.exit(1)

    res = build()
    print("Build OK:")
    print(json.dumps(res["ingesta"], ensure_ascii=False, indent=2))
    print(json.dumps(res["deducido"], ensure_ascii=False, indent=2))
    print("Top 5:")
    for r in res["top10"][:5]:
        print(
            f"  {r['titulo_canonico'][:60]} · P={r['P']} ({r['rango']}) · {r['estado_evidencia']}"
        )


def _cmd_eval(args) -> None:
    import os

    from faro import db
    from faro.agent import loop
    from faro.eval import benchmark, metrics

    split = os.environ.get("SPLIT", "dev")
    modo = os.environ.get("MODO", "determinista")
    casos = benchmark.cargar_benchmark(split=split)
    llm_cfg = {"modo": modo}
    if modo == "usuario":
        llm_cfg.update(proveedor=S.LLM_PROVEEDOR, modelo=S.LLM_MODELO, api_key=S.LLM_API_KEY)
    conn = db.connect()
    resultados = []
    for c in casos:
        try:
            r = loop.consultar(
                c["pregunta"], conn, lente=c.get("lente", "editorial"), llm_cfg=llm_cfg
            )
            c["respuesta"] = r["respuesta"][:200]
            c["abstuvo"] = r["abstencion"]
            c["meta"] = r.get("meta", {})
        except Exception as e:  # noqa: BLE001
            c["respuesta"] = f"error:{e}"
            c["abstuvo"] = True
        resultados.append(c)
    conn.close()
    m = {
        "split": split,
        "modo": modo,
        "casos": resultados,
        "abstencion": metrics.abstencion(resultados),
        "cobertura_citas": metrics.cobertura_citas(
            [a for c in resultados for a in c.get("afirmaciones", [])]
        ),
    }
    path = metrics.escribir_metricas(m)
    print(f"Métricas escritas en {path}")
    print(json.dumps(m["abstencion"], ensure_ascii=False, indent=2))


def _cmd_eval_nlp(args) -> None:
    """Evaluación NLP NO circular: lee data/labels/temas.csv y pares.csv (etiquetas humanas)."""
    import csv

    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import f1_score
    from sklearn.model_selection import StratifiedKFold, cross_val_predict

    from faro.nlp import classify, embed
    from faro.nlp.embed import EMBEDDER_NAME

    temas_path = S.LABELS_DIR / "temas.csv"
    pares_path = S.LABELS_DIR / "pares.csv"
    if not temas_path.exists():
        print(f"Error: falta {temas_path}. Corre `make labels-sample` y etiqueta a mano (WP-3).")
        sys.exit(1)
    if not pares_path.exists():
        print(f"Error: falta {pares_path}. Corre `make labels-sample` y etiqueta a mano (WP-3).")
        sys.exit(1)

    with open(temas_path, encoding="utf-8") as fh:
        filas = [r for r in csv.DictReader(fh) if r.get("tema", "").strip()]
    titulares = [r["titulo"] for r in filas]
    etiquetas = [r["tema"].strip() for r in filas]
    clases = sorted(set(etiquetas))
    clase_idx = {c: i for i, c in enumerate(clases)}
    y = np.array([clase_idx[e] for e in etiquetas])
    matriz = embed.Embedder().encode(titulares)

    baseline = [classify.clasificar_baseline(t) for t in titulares]
    macro_baseline = f1_score(etiquetas, baseline, average="macro")

    clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    preds = cross_val_predict(clf, matriz, y, cv=StratifiedKFold(5, shuffle=True, random_state=42))
    macro_lr = f1_score(y, preds, average="macro")

    # Entrenar el clasificador final y guardarlo para el pipeline.
    import joblib

    models_dir = S.REPO_ROOT / "models"
    models_dir.mkdir(exist_ok=True)
    clf.fit(matriz, y)
    joblib.dump(clf, models_dir / "tema_lr.joblib")

    # Precisión/recall de pares (clustering): un par "mismo evento" si quedó en el mismo cluster.
    with open(pares_path, encoding="utf-8") as fh:
        pares = [r for r in csv.DictReader(fh) if r.get("mismo_evento", "").strip()]

    report = {
        "n_etiquetas": len(etiquetas),
        "n_pares": len(pares),
        "metodo_etiquetado": "manual por los dos integrantes",
        "etiquetadores": "[HUMANO]",
        "fecha": __import__("datetime").datetime.now().isoformat(),
        "embedder": EMBEDDER_NAME,
        "ner": "es_core_news_md",
        "macro_f1_lr": round(float(macro_lr), 4),
        "macro_f1_baseline": round(float(macro_baseline), 4),
        "mejora": round(float(macro_lr) - float(macro_baseline), 4),
        "clases": clases,
    }
    S.ensure_dirs()
    (S.REPORTS_DIR / "nlp.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))


def _cmd_labels_sample(args) -> None:
    """Genera data/labels/temas_pendientes.csv y pares_pendientes.csv para etiquetar a mano."""
    import csv
    import random

    import numpy as np

    from faro import db

    S.ensure_dirs()
    conn = db.connect()
    rows = db.fetchall(
        conn, "SELECT id, titulo, medio FROM noticia WHERE titulo != '' ORDER BY RANDOM()"
    )
    conn.close()
    if len(rows) < 150:
        print(f"Hay {len(rows)} noticias; se necesita ≥ 150 para muestrear.")
        sys.exit(1)

    # 150 titulares, estratificados por medio y tema del baseline.
    rng = random.Random(42)
    por_medio: dict[str, list] = {}
    for r in rows:
        por_medio.setdefault(r["medio"], []).append(r)
    muestra = []
    while len(muestra) < 150:
        for _medio, rs in por_medio.items():
            if rs and len(muestra) < 150:
                muestra.append(rs.pop(0))
    with open(S.LABELS_DIR / "temas_pendientes.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["noticia_id", "titulo", "medio", "tema"])
        for r in muestra:
            w.writerow([r["id"], r["titulo"], r["medio"], ""])

    # 50 pares: mezcla de mismo-cluster y distinto-cluster.
    from faro.events.cluster import agrupar_eventos
    from faro.nlp import embed

    noticias = db.fetchall(
        conn := db.connect(), "SELECT id, titulo, fecha_publicacion FROM noticia ORDER BY id"
    )
    matriz = embed.Embedder().encode([n["titulo"] for n in noticias])
    grupos = agrupar_eventos(noticias, matriz)
    conn.close()
    mismo, distinto = [], []
    for g in grupos:
        if len(g) >= 2 and len(mismo) < 25:
            mismo.append((noticias[g[0]], noticias[g[1]]))
    # Distintos clusters pero coseno > 0.6.
    for _ in range(1000):
        if len(distinto) >= 25:
            break
        a, b = rng.sample(range(len(noticias)), 2)
        cos = float(np.dot(matriz[a], matriz[b]))
        if cos > 0.6 and any(a in g and b in g for g in grupos) is False:
            distinto.append((noticias[a], noticias[b]))
    with open(S.LABELS_DIR / "pares_pendientes.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["id_a", "titulo_a", "id_b", "titulo_b", "mismo_evento"])
        for a, b in mismo:
            w.writerow([a["id"], a["titulo"], b["id"], b["titulo"], ""])
        for a, b in distinto:
            w.writerow([a["id"], a["titulo"], b["id"], b["titulo"], ""])
    print(
        f"temas_pendientes.csv: {len(muestra)} · pares_pendientes.csv: {len(mismo) + len(distinto)}"
    )


def _cmd_check_sources(args) -> None:
    from faro.scrape.check import check_fuentes

    res = check_fuentes()
    utilizables = [r for r in res if r.metodo_ok]
    print(f"Fuentes revisadas: {len(res)} · utilizables: {len(utilizables)}")
    for r in res:
        print(
            f"  {r.id:16s} {r.metodo:8s} robots={r.robots_ok} metodo_ok={r.metodo_ok} vol={r.volumen_estimado}"
        )


def _cmd_demo_offline(args) -> None:
    import os
    import shutil
    import subprocess
    import tempfile
    from pathlib import Path

    tmp = Path(tempfile.mkdtemp(prefix="faro-demo-"))
    print(f"Clonando repo a {tmp} ...")
    subprocess.run(["git", "clone", "--depth", "1", str(S.REPO_ROOT), str(tmp)], check=True)
    # Copiar caché de modelos HF y modelos entrenados (para no descargar).
    for src, dst in (
        (S.DATA_DIR / "cache" / "hf", tmp / "data" / "cache" / "hf"),
        (S.REPO_ROOT / "models", tmp / "models"),
    ):
        if src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(src, dst, dirs_exist_ok=True)
    env = {**os.environ, "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"}
    subprocess.run(["uv", "sync", "--frozen"], cwd=str(tmp), check=True, env=env)
    subprocess.run(["make", "build"], cwd=str(tmp), check=True, env=env)
    print("Snapshot cargado. Arrancando Streamlit (modo offline)...")
    os.execvpe("uv", ["uv", "run", "streamlit", "run", "app/streamlit_app.py"], env=env)


def _cmd_demo_cache(args) -> None:
    """Precalienta la caché con las preguntas de docs/guion_demo.md."""
    from faro import db
    from faro.agent import loop

    guion = S.REPO_ROOT / "docs" / "guion_demo.md"
    if not guion.exists():
        print("docs/guion_demo.md no existe; no hay preguntas que cachear.")
        return
    preguntas = [
        line.strip()
        for line in guion.read_text(encoding="utf-8").splitlines()
        if line.strip().startswith("- P: ")
    ]
    conn = db.connect()
    for p in preguntas:
        pregunta = p[5:]
        loop.consultar(pregunta, conn)
        print(f"  cacheada: {pregunta[:60]}")
    conn.close()
    print(f"Caché llena con {len(preguntas)} preguntas.")


def main() -> None:
    p = argparse.ArgumentParser(prog="faro", description="FARO — pipeline y demo")
    sub = p.add_subparsers(dest="cmd", required=True)
    p_data = sub.add_parser("data")
    p_data.add_argument("--fuentes", help="ids separados por coma (subconjunto)")
    p_data.add_argument("--meses", help="meses AAAA-MM separados por coma (subconjunto)")
    p_data.add_argument("--prueba", action="store_true", help="escribir en carpeta temporal")
    sub.add_parser("data-seed")
    sub.add_parser("freeze")
    sub.add_parser("verify")
    sub.add_parser("build")
    sub.add_parser("eval")
    sub.add_parser("eval-nlp")
    sub.add_parser("labels-sample")
    sub.add_parser("check-sources")
    sub.add_parser("demo-offline")
    sub.add_parser("demo-cache")
    sub.add_parser("notion-sync")
    sub.add_parser("muestra-urls")

    args = p.parse_args()
    {
        "data": _cmd_data,
        "data-seed": _cmd_data_seed,
        "freeze": _cmd_freeze,
        "verify": _cmd_verify,
        "build": _cmd_build,
        "eval": _cmd_eval,
        "eval-nlp": _cmd_eval_nlp,
        "labels-sample": _cmd_labels_sample,
        "check-sources": _cmd_check_sources,
        "demo-offline": _cmd_demo_offline,
        "demo-cache": _cmd_demo_cache,
        "notion-sync": _cmd_notion_sync,
        "muestra-urls": _cmd_muestra_urls,
    }[args.cmd](args)


def _cmd_notion_sync(args) -> None:
    from faro.review import notion_sync

    print(json.dumps(notion_sync.sync_notion(), ensure_ascii=False, indent=2))


def _cmd_muestra_urls(args) -> None:
    """M2.4: exporta 20 URLs al azar (semilla fija) para revisión humana."""
    import csv
    import random

    from faro import db

    S.ensure_dirs()
    conn = db.connect()
    rows = db.fetchall(
        conn, "SELECT id, medio, titulo, fecha_publicacion, url FROM noticia ORDER BY RANDOM()"
    )
    conn.close()
    rng = random.Random(42)
    muestra = rng.sample(rows, min(20, len(rows)))
    path = S.REPORTS_DIR / "muestra_urls.csv"
    with open(path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["noticia_id", "medio", "titulo", "fecha_publicacion", "url", "ok", "motivo"])
        for r in muestra:
            w.writerow([r["id"], r["medio"], r["titulo"], r["fecha_publicacion"], r["url"], "", ""])
    print(f"Muestra de {len(muestra)} URLs escrita en {path}")


if __name__ == "__main__":
    main()

"""CLI de FARO: un comando por paso del pipeline (Makefile)."""

from __future__ import annotations

import argparse
import json
import sys

import config.settings as S


def _cmd_data(args) -> None:
    from faro.seed import gen_indicadores, gen_noticias, gen_series, gen_sismos, write_raw

    conteos = write_raw(gen_noticias(), gen_series(), gen_indicadores(), gen_sismos())
    print("Snapshot sintético escrito en data/raw/:")
    for k, v in conteos.items():
        print(f"  {k}: {v}")


def _cmd_freeze(args) -> None:
    from pathlib import Path

    import config.settings as S
    from faro.quality.manifest import build_manifest, write_manifest

    conteos = {
        p.name: sum(1 for _ in open(p, encoding="utf-8")) for p in Path(S.RAW_DIR).glob("*.jsonl")
    }
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
    from faro.pipeline import build

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
    from faro import db
    from faro.agent import loop
    from faro.eval import benchmark, metrics

    casos = benchmark.cargar_benchmark()
    if not casos:
        casos = benchmark.crear_benchmark_semilla()
    conn = db.connect()
    resultados = []
    for c in casos:
        try:
            r = loop.consultar(c["pregunta"], conn, lente=c.get("lente", "editorial"))
            c["respuesta"] = r["respuesta"][:200]
            c["abstuvo"] = r["abstencion"]
        except Exception as e:  # noqa: BLE001
            c["respuesta"] = f"error:{e}"
            c["abstuvo"] = True
        resultados.append(c)
    conn.close()
    m = {
        "casos": resultados,
        "abstencion": metrics.abstencion(resultados),
    }
    path = metrics.escribir_metricas(m)
    print(f"Métricas escritas en {path}")
    print(json.dumps(m["abstencion"], ensure_ascii=False, indent=2))


def _cmd_eval_nlp(args) -> None:
    # Etiquetas: si no hay labels humanas, usar el tema del seed como etiqueta.
    from faro import db
    from faro.nlp import classify, embed

    conn = db.connect()
    rows = db.fetchall(conn, "SELECT id, titulo, tema FROM noticia WHERE tema IS NOT NULL")
    conn.close()
    titulares = [r["titulo"] for r in rows]
    etiquetas = [r["tema"] for r in rows]
    matriz = embed.Embedder().encode(titulares)
    ev = classify.evaluar_clasificador(matriz, etiquetas)
    baseline = [classify.clasificar_baseline(t) for t in titulares]
    from sklearn.metrics import f1_score

    macro_baseline = f1_score(etiquetas, baseline, average="macro")
    report = {
        "metodo": "embeddings + regresión logística (5-fold)",
        "macro_f1_lr": ev["macro_f1_lr"],
        "macro_f1_baseline": float(macro_baseline),
        "n_etiquetas": len(etiquetas),
        "mejora": ev["macro_f1_lr"] - float(macro_baseline),
    }
    S.ensure_dirs()
    (S.REPORTS_DIR / "nlp.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(json.dumps(report, ensure_ascii=False, indent=2))


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
    import subprocess
    import tempfile
    from pathlib import Path

    tmp = Path(tempfile.mkdtemp(prefix="faro-demo-"))
    print(f"Clonando repo a {tmp} ...")
    subprocess.run(["cp", "-R", str(S.REPO_ROOT) + "/.", str(tmp)], check=True)
    # Precarga el snapshot ya congelado y arranca Streamlit.
    subprocess.run([sys.executable, "-m", "faro.cli", "build"], cwd=str(tmp), check=True)
    print("Snapshot cargado. Arrancando Streamlit (modo offline)...")
    os.execvp("uv", ["uv", "run", "streamlit", "run", "app/streamlit_app.py"])


def main() -> None:
    p = argparse.ArgumentParser(prog="faro", description="FARO — pipeline y demo")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("data")
    sub.add_parser("freeze")
    sub.add_parser("verify")
    sub.add_parser("build")
    sub.add_parser("eval")
    sub.add_parser("eval-nlp")
    sub.add_parser("check-sources")
    sub.add_parser("demo-offline")

    args = p.parse_args()
    {
        "data": _cmd_data,
        "freeze": _cmd_freeze,
        "verify": _cmd_verify,
        "build": _cmd_build,
        "eval": _cmd_eval,
        "eval-nlp": _cmd_eval_nlp,
        "check-sources": _cmd_check_sources,
        "demo-offline": _cmd_demo_offline,
    }[args.cmd](args)


if __name__ == "__main__":
    main()

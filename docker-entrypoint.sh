#!/bin/sh
# FARO — entrypoint del contenedor.
# 1) Usa el snapshot REAL versionado (data/raw/*.jsonl) y construye la base.
#    Nunca genera datos sintéticos (WP-8).
# 2) Arranca Streamlit en el puerto 8501.
set -e

if [ -z "$(ls -A data/raw/*.jsonl 2>/dev/null)" ]; then
  echo "ERROR: no hay snapshot real en data/raw/. Corre 'make data' y 'make freeze' antes de empaquetar." >&2
  exit 1
fi

echo "==> Construyendo base desde el snapshot real (offline)..."
python -m faro.cli build

echo "==> Arrancando FARO en http://0.0.0.0:8501"
exec streamlit run app/streamlit_app.py \
  --server.port=8501 \
  --server.address=0.0.0.0 \
  --server.headless=true

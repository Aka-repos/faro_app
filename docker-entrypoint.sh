#!/bin/sh
# FARO — entrypoint del contenedor.
# 1) Genera/valida el snapshot local (seed sintético si no hay raw/) y construye la base.
# 2) Arranca Streamlit en el puerto 8501.
set -e

echo "==> Construyendo snapshot y base (offline)..."
python -m faro.cli build

echo "==> Arrancando FARO en http://0.0.0.0:8501"
exec streamlit run app/streamlit_app.py \
  --server.port=8501 \
  --server.address=0.0.0.0 \
  --server.headless=true

# FARO — imagen Docker (demo reproducible)
# La imagen contiene el código + dependencias; el snapshot se genera en el primer arranque
# (seed sintético) o se monta uno real con un volumen en data/.

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false \
    STREAMLIT_SERVER_HEADLESS=true

WORKDIR /app

# 1) Dependencias del proyecto (pyproject.toml -> pip).
#    Se copia solo lo que `pip install .` necesita (faro, schemas, config) para
#    que cambios en la UI (app/) no invaliden la capa de dependencias.
COPY pyproject.toml README.md ./
COPY faro ./faro
COPY schemas ./schemas
COPY config ./config

RUN pip install --no-cache-dir .

# 2) Código de la UI y prompts.
COPY app ./app
COPY prompts ./prompts

# 3) Entrypoint: construye el snapshot (offline) y arranca la UI.
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

EXPOSE 8501

ENTRYPOINT ["./docker-entrypoint.sh"]

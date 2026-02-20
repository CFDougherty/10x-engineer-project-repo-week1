# syntax=docker/dockerfile:1.5

ARG PYTHON_IMAGE=python:3.12.5-slim

FROM ${PYTHON_IMAGE} AS dependencies
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app

COPY backend/requirements.txt ./requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install --prefix=/install -r requirements.txt

FROM ${PYTHON_IMAGE}

ARG APP_PORT=8000
LABEL org.opencontainers.image.title="PromptLab API backend" \
      org.opencontainers.image.description="FastAPI service that stores and versions prompt templates" \
      org.opencontainers.image.authors="PromptLab contributors"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=${APP_PORT}

WORKDIR /app

RUN addgroup --system appuser && adduser --system --ingroup appuser appuser

COPY --from=dependencies /install/ /usr/local/

COPY --chown=appuser:appuser backend/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod 0755 /usr/local/bin/docker-entrypoint.sh

COPY --chown=appuser:appuser backend/app ./app
COPY --chown=appuser:appuser backend/main.py ./

USER appuser

EXPOSE ${APP_PORT}
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s CMD \
  python -c "import os,sys,urllib.request; p=os.getenv('PORT','8000'); \
u=f'http://127.0.0.1:{p}/health'; \
req=urllib.request.Request(u, method='GET'); \
try: r=urllib.request.urlopen(req,timeout=5); sys.exit(0 if getattr(r,'status',200)==200 else 1) \
except Exception: sys.exit(1)"
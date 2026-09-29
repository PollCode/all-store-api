# syntax=docker/dockerfile:1.7

# =============================================================
# Stage 1: builder — resuelve dependencias con uv
# =============================================================
FROM python:3.13-slim AS builder

# Variables de entorno para uv y Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

# uv desde la imagen oficial (evita instalar pip)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copiamos primero solo los metadatos para aprovechar la caché
COPY pyproject.toml uv.lock ./

# Instalamos dependencias de producción (sin dev) en un venv aislado
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev --no-install-project

# Copiamos el resto del código
COPY . .

# =============================================================
# Stage 2: runtime — imagen final limpia
# =============================================================
FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH" \
    APP_ENV=production

# Dependencias del sistema mínimas (curl para healthcheck, libpq para psycopg)
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Usuario no root
RUN groupadd --system --gid 1000 app \
    && useradd --system --uid 1000 --gid app --home /app --shell /sbin/nologin app

WORKDIR /app

# Copiamos el venv y el código desde el builder
COPY --from=builder --chown=app:app /app /app

# Entrypoint que aplica migraciones y arranca la app
COPY --chown=app:app docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

USER app

EXPOSE 8000

# Healthcheck usando /health (o /docs si no tienes /health)
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -fsS http://localhost:8000/api/v1/health || exit 1

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
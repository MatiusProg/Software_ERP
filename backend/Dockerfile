# syntax=docker/dockerfile:1
#
# Imagen del backend (API Django + notas QR).
#
# El contexto de build es la RAÍZ del repo, no backend/: así Railway la construye
# sin configurar un "Root Directory" y el compose usa la misma. El .dockerignore
# de la raíz deja pasar solo backend/.
#
#   docker build -f backend/Dockerfile -t erp-api .
#
# Dos etapas: la primera instala las dependencias en un venv; la segunda copia
# solo ese venv y el código, sin pip cache ni herramientas de build.

FROM python:3.13-slim AS deps

ENV PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

COPY backend/requirements.txt /tmp/requirements.txt
# La caché de pip sobrevive entre builds (no entra en la imagen): cambiar una
# línea de requirements no vuelve a descargar todo.
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r /tmp/requirements.txt


FROM python:3.13-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/venv/bin:$PATH \
    PORT=8000

# Usuario sin privilegios: si alguien rompe la app, no es root en el contenedor.
RUN useradd --create-home --uid 1000 app
WORKDIR /app

COPY --from=deps /opt/venv /opt/venv
COPY --chown=app:app backend/ .

# Los estáticos del admin se recolectan al construir, no al arrancar: el
# despliegue arranca más rápido y un fallo aquí rompe el build, no producción.
RUN DJANGO_SECRET_KEY=solo-para-collectstatic DJANGO_DEBUG=False \
    python manage.py collectstatic --noinput

USER app
EXPOSE 8000

# Las migraciones NO van aquí: en Railway corren en el preDeployCommand
# (railway.json) y en desarrollo las corre el compose.
CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${PORT} --workers 3 --timeout 60 --access-logfile -"]

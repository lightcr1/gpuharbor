FROM python:3.15-slim@sha256:94d3426f1def7db4a106a232ac121bfd975393e5dfd40a619b955fae45fe7913

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml requirements.lock ./
COPY gpuharbor ./gpuharbor
RUN pip install --no-cache-dir --requirement requirements.lock \
 && pip install --no-cache-dir --no-deps .
COPY registry ./registry
RUN useradd --system --uid 10001 gpuharbor && mkdir -p /data && chown gpuharbor:gpuharbor /data
USER 10001
EXPOSE 8080
CMD ["uvicorn", "gpuharbor.main:app", "--host", "0.0.0.0", "--port", "8080"]

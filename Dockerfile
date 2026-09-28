FROM python:3.12-slim@sha256:f77ac9e44ae96ef2c90b8053ea08c31f8be030f824196b0ae4db6d462c84e51f

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

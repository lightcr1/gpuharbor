FROM python:3.14-slim@sha256:51dafde81dbdb6ebde285137a295cf18a47ca95234fe388a343719cb97305b3d

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

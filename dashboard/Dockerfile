# FunnelLens dashboard (the v1.1 release). Build from the repo root:
#   docker build -f dashboard/Dockerfile -t funnellens-dashboard:local .
# Stage 1 runs the Python track pipeline on the committed export, so the image ships with answers.json;
# set ANSWERS_PATH at run time to show another track's answers instead (docker compose --profile pipelines).
FROM python:3.12-slim AS answers
ARG EXPORT=2026-08
ENV PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN --mount=type=bind,source=tracks/python/requirements.txt,target=/tmp/requirements.txt \
    pip install -r /tmp/requirements.txt
RUN --mount=type=bind,source=.,target=/src \
    cd /src/tracks/python && python -m funnellens run --data /src/data/raw/${EXPORT} --out /answers

FROM scratch AS src
COPY contract/answers.schema.json /app/contract/answers.schema.json
COPY --from=answers /answers/answers.json /app/answers/answers.json
COPY dashboard/app.py dashboard/entrypoint.sh /app/dashboard/
COPY dashboard/.streamlit /app/dashboard/.streamlit
COPY dashboard/funnellens_dashboard /app/dashboard/funnellens_dashboard

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 \
    HOME=/tmp ANSWERS_PATH=/app/answers/answers.json STATIC_DIR=/app/dashboard/static AI_PROVIDER=offline
RUN --mount=type=bind,source=dashboard/requirements.txt,target=/tmp/requirements.txt \
    pip install -r /tmp/requirements.txt \
 && useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin funnellens \
 && mkdir -p /app/dashboard/static && chown 10001:10001 /app/dashboard/static
COPY --from=src /app /app
WORKDIR /app/dashboard
USER 10001
EXPOSE 8501
HEALTHCHECK --interval=5s --timeout=3s --start-period=10s --retries=12 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=2)"]
ENTRYPOINT ["./entrypoint.sh"]

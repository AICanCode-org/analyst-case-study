# FunnelLens pipeline, Python track. Build from the repo root:
#   docker build -f tracks/python/Dockerfile -t funnellens-python:local .
#   docker run --rm -v "$PWD/data:/app/data:ro" -v "$PWD/out:/out" funnellens-python:local run --data /app/data/raw/2026-06 --out /out
# Few layers on purpose: one for dependencies, one for the code (cheap rebuilds, small images).
FROM scratch AS src
COPY contract /app/contract
COPY tracks/python/funnellens /app/tracks/python/funnellens

FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MPLCONFIGDIR=/tmp/matplotlib
RUN --mount=type=bind,source=tracks/python/requirements.txt,target=/tmp/requirements.txt \
    pip install -r /tmp/requirements.txt \
 && useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin funnellens \
 && mkdir -p /out && chown 10001:10001 /out
COPY --from=src /app /app
WORKDIR /app/tracks/python
USER 10001
ENTRYPOINT ["python", "-m", "funnellens"]
CMD ["run", "--data", "/app/data/raw/2026-06", "--out", "/out"]

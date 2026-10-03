# FunnelLens pipeline, R track. Build from the repo root:
#   docker build -f tracks/r/Dockerfile -t funnellens-r:local .
# Debian's packaged R (r-base-core + r-cran-*) in one layer: no compiler, no CRAN download at build time.
FROM scratch AS src
COPY contract /app/contract
COPY tracks/r/DESCRIPTION tracks/r/NAMESPACE tracks/r/LICENSE tracks/r/run.R /app/tracks/r/
COPY tracks/r/R /app/tracks/r/R

FROM python:3.12-slim
ENV HOME=/tmp LANG=C.UTF-8
RUN apt-get -o Acquire::Retries=5 update \
 && apt-get install -y --no-install-recommends r-base-core r-cran-dplyr r-cran-jsonlite r-cran-readr r-cran-rlang \
      r-cran-stringr r-cran-tibble r-cran-tidyr r-cran-yaml r-cran-pkgload \
 && rm -rf /var/lib/apt/lists/* \
 && useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin funnellens \
 && mkdir -p /out && chown 10001:10001 /out
COPY --from=src /app /app
WORKDIR /app/tracks/r
USER 10001
ENTRYPOINT ["Rscript", "run.R"]
CMD ["run", "--data", "/app/data/raw/2026-08", "--out", "/out"]

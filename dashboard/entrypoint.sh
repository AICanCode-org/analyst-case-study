#!/bin/sh
# Validate the answers and write static/ (narrative: AI narrator or template), then serve the dashboard
# on $PORT (default 8501; hosting platforms such as Render set PORT).
set -eu
python -m funnellens_dashboard prepare --answers "${ANSWERS_PATH}" --out "${STATIC_DIR}"
exec python -m streamlit run app.py --server.port "${PORT:-8501}" --server.address 0.0.0.0

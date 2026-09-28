#!/bin/sh
# Container entrypoint: migrate the database, then serve the app on $PORT.
set -eu

if [ -n "${DATABASE_URL:-}" ]; then
  alembic upgrade head
else
  # Hexlet's automated check runs the image without a database and only needs
  # the home page to load. Pages work; anything that needs data fails.
  echo "DATABASE_URL is not set: skipping migrations, data requests will fail." >&2
fi

exec fastapi run app/main.py --host 0.0.0.0 --port "${PORT:-8080}" --proxy-headers

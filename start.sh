#!/usr/bin/env bash
set -e

echo "Running migrations..."
python migrations/migration.py

echo "Starting application..."
exec gunicorn app:app

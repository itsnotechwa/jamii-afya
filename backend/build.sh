#!/usr/bin/env bash
set -o errexit

# ── 1. Decode Aiven CA certificate from env variable ──────────────────────────
# This cert is required for SSL connection to Aiven MySQL.
# Set AIVEN_CA_BASE64 in Render environment variables.
echo "$AIVEN_CA_BASE64" | base64 --decode > /etc/ssl/aiven-ca.pem
echo "✅ Aiven CA certificate written to /etc/ssl/aiven-ca.pem"

# ── 2. Install dependencies ────────────────────────────────────────────────────
pip install -r requirements.txt
echo "✅ Dependencies installed"

# ── 3. Collect static files ────────────────────────────────────────────────────
python manage.py collectstatic --no-input
echo "✅ Static files collected"

# ── 4. Run database migrations ─────────────────────────────────────────────────
echo "$AIVEN_CA_BASE64" | base64 --decode > /etc/ssl/aiven-ca.pem
python manage.py migrate
echo "✅ Migrations applied"
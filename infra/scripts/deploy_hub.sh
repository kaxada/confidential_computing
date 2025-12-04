#!/usr/bin/env bash
set -euo pipefail

TAR_PATH="${1:-/tmp/confidential_bundle.tgz}"
APP_DIR="/opt/confidential"
DEPLOY_USER="${DEPLOY_USER:-ec2-user}"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"
VENV_DIR="$APP_DIR/venv"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-postgres}"
DB_NAME="${DB_NAME:-confidential_rag}"

echo "[deploy_hub] Using bundle: $TAR_PATH"
echo "[deploy_hub] Installing system dependencies (Amazon Linux 2023)"

# ----------------------------
# Install Python tools ONLY
# (Do NOT install node — AL2023 AMI already has Node 20 from NodeSource)
# ----------------------------
sudo dnf install -y python3 python3-pip python3-virtualenv

# ----------------------------
# Install PostgreSQL 15 (AL2023)
# ----------------------------
echo "[deploy_hub] Installing PostgreSQL 15"

sudo dnf install -y postgresql15 postgresql15-server

if ! sudo test -f "/var/lib/pgsql/data/PG_VERSION"; then
    echo "[deploy_hub] Initializing PostgreSQL database"
    sudo postgresql-setup --initdb
fi

sudo systemctl enable --now postgresql || sudo systemctl start postgresql

# ----------------------------
# Configure PostgreSQL
# ----------------------------
echo "[deploy_hub] Ensuring Postgres is running and database exists"

sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '${POSTGRES_PASSWORD}';" || true

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}';" | grep -q 1 \
  || sudo -u postgres createdb "${DB_NAME}"

# ----------------------------
# Deploy bundle
# ----------------------------
sudo mkdir -p "$APP_DIR"
sudo chown -R "$DEPLOY_USER":"$DEPLOY_USER" "$APP_DIR"

sudo tar -xzf "$TAR_PATH" -C "$APP_DIR" --strip-components=0

# ----------------------------
# Python virtual environment
# ----------------------------
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$BACKEND_DIR/app/requirements.txt"

# ----------------------------
# Generate backend .env as ec2-user
# ----------------------------
BACKEND_ENV="$BACKEND_DIR/.env"
if [ ! -f "$BACKEND_ENV" ]; then
sudo -u "$DEPLOY_USER" bash -c "cat > '$BACKEND_ENV' <<EOF
DATABASE_URL=postgresql+psycopg://postgres:${POSTGRES_PASSWORD}@localhost:5432/${DB_NAME}
SITE_BASE_URL=http://localhost:8080
SITE_ID=site_local
DEFAULT_PRIVACY_LEVEL=moderate
JWT_SECRET=${JWT_SECRET:-dev-secret-change-me}
JWT_ALGORITHM=HS256
JWT_EXP_MINUTES=60
EOF"
fi

# ----------------------------
# Systemd service setup
# ----------------------------
sudo cp "$APP_DIR/infra/systemd/backend.service" /etc/systemd/system/backend.service
sudo cp "$APP_DIR/infra/systemd/frontend.service" /etc/systemd/system/frontend.service
sudo systemctl daemon-reload
sudo systemctl restart backend.service frontend.service
sudo systemctl enable backend.service frontend.service

echo "[deploy_hub] Done"

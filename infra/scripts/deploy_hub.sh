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
echo "[deploy_hub] Installing system dependencies (Amazon Linux)"

# ----------------------------
# Install core packages
# ----------------------------
sudo yum install -y python3 python3-pip python3-virtualenv nodejs npm

# ----------------------------
# Install PostgreSQL (Amazon Linux 2)
# ----------------------------
echo "[deploy_hub] Installing PostgreSQL 15"

# Uncomment if on AL2:
sudo amazon-linux-extras enable postgresql15 || true

sudo yum install -y postgresql15 postgresql15-server

# Initialize DB only if not initialized already
if [ ! -d "/var/lib/pgsql/15/data/base" ]; then
    echo "[deploy_hub] Initializing PostgreSQL database"
    sudo /usr/bin/postgresql-setup --initdb
fi

sudo systemctl enable --now postgresql || sudo systemctl start postgresql

# ----------------------------
# Configure PostgreSQL
# ----------------------------
echo "[deploy_hub] Ensuring Postgres is running and database exists"

sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='postgres';" | grep -q 1 \
  || sudo -u postgres createuser postgres

sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '${POSTGRES_PASSWORD}';" || true

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}';" | grep -q 1 \
  || sudo -u postgres createdb "${DB_NAME}"

# ----------------------------
# Deploy application bundle
# ----------------------------
sudo mkdir -p "$APP_DIR"
sudo chown -R "$DEPLOY_USER":"$DEPLOY_USER" "$APP_DIR"
sudo tar -xzf "$TAR_PATH" -C "$APP_DIR" --strip-components=0

# ----------------------------
# Python environment + backend deps
# ----------------------------
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$BACKEND_DIR/app/requirements.txt"

# ----------------------------
# Backend .env creation if needed
# ----------------------------
BACKEND_ENV="$BACKEND_DIR/.env"
if [ ! -f "$BACKEND_ENV" ]; then
cat <<EOF > "$BACKEND_ENV"
DATABASE_URL=postgresql+psycopg://postgres:${POSTGRES_PASSWORD}@localhost:5432/${DB_NAME}
SITE_BASE_URL=http://localhost:8080
SITE_ID=site_local
DEFAULT_PRIVACY_LEVEL=moderate
JWT_SECRET=${JWT_SECRET:-dev-secret-change-me}
JWT_ALGORITHM=HS256
JWT_EXP_MINUTES=60
EOF
fi

# ----------------------------
# Systemd services
# ----------------------------
sudo cp "$APP_DIR/infra/systemd/backend.service" /etc/systemd/system/backend.service
sudo cp "$APP_DIR/infra/systemd/frontend.service" /etc/systemd/system/frontend.service
sudo systemctl daemon-reload
sudo systemctl restart backend.service frontend.service
sudo systemctl enable backend.service frontend.service

echo "[deploy_hub] Done"

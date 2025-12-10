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
# Install Python tools, Nginx, Node.js, Rsync
# ----------------------------
sudo dnf install -y python3 python3-pip python3-virtualenv nginx nodejs rsync

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

cd /

sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '${POSTGRES_PASSWORD}';" || true

sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}';" | grep -q 1 \
  || sudo -u postgres createdb "${DB_NAME}"

# ----------------------------
# Deploy bundle (Sync)
# ----------------------------
sudo mkdir -p "$APP_DIR"

# Extract to temporary directory first
TEMP_DIR=$(mktemp -d)
echo "[deploy_hub] Extracting to $TEMP_DIR"
tar -xzf "$TAR_PATH" -C "$TEMP_DIR"

echo "[deploy_hub] Syncing to $APP_DIR (removing stale files)"
# Sync and delete files not in source, but preserve generated/heavy folders
sudo rsync -a --delete \
  --exclude 'venv' \
  --exclude 'backend/venv' \
  --exclude 'backend/.env' \
  --exclude 'backend/__pycache__' \
  --exclude 'frontend/node_modules' \
  --exclude 'frontend/.env.production' \
  --exclude 'frontend/dist' \
  "$TEMP_DIR/" "$APP_DIR/"

rm -rf "$TEMP_DIR"
sudo chown -R "$DEPLOY_USER":"$DEPLOY_USER" "$APP_DIR"

# ----------------------------
# Python virtual environment
# ----------------------------
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$BACKEND_DIR/requirements.txt"

# ----------------------------
# Generate backend .env as ec2-user
# ----------------------------
BACKEND_ENV="$BACKEND_DIR/.env"

# Construct SITE_REGISTRY JSON if URLs are provided
if [ -n "${SITE_1_URL:-}" ] && [ -n "${SITE_2_URL:-}" ] && [ -n "${SITE_3_URL:-}" ]; then
    SITE_REGISTRY_JSON="{\"site_1\": {\"url\": \"${SITE_1_URL}\"}, \"site_2\": {\"url\": \"${SITE_2_URL}\"}, \"site_3\": {\"url\": \"${SITE_3_URL}\"}}"
else
    # Fallback to defaults
    SITE_REGISTRY_JSON="{\"site_1\": {\"url\": \"http://localhost:8080\"}, \"site_2\": {\"url\": \"http://localhost:8081\"}, \"site_3\": {\"url\": \"http://localhost:8082\"}}"
fi

if [ ! -f "$BACKEND_ENV" ] || [ -n "${SITE_1_URL:-}" ]; then
# Overwrite or create if we have new URLs, otherwise respect existing if no new URLs provided (logic simplified to always write for deployment consistency)
sudo -u "$DEPLOY_USER" bash -c "cat > '$BACKEND_ENV' <<EOF
DATABASE_URL=postgresql+psycopg://postgres:${POSTGRES_PASSWORD}@localhost:5432/${DB_NAME}
SITE_BASE_URL=http://localhost:8000
SITE_ID=hub
DEFAULT_PRIVACY_LEVEL=moderate
JWT_SECRET=${JWT_SECRET:-dev-secret-change-me}
JWT_ALGORITHM=HS256
JWT_EXP_MINUTES=60
SITE_REGISTRY='${SITE_REGISTRY_JSON}'
OPENAI_API_KEY=${OPENAI_API_KEY:-}
EOF"
fi

# ----------------------------
# Frontend Build
# ----------------------------
echo "[deploy_hub] Building Frontend"
cd "$FRONTEND_DIR"
# Configure for Nginx proxy (relative paths)
echo "VITE_API_BASE=" > .env.production

# Run npm install/build as the deployment user to avoid permission issues
# (We assume this script runs as a user who can sudo, or we switch)
if [ "$USER" == "root" ]; then
    # If running as root, run npm as DEPLOY_USER
    sudo -u "$DEPLOY_USER" bash -c "cd $FRONTEND_DIR && npm install && npm run build"
else
    npm install
    npm run build
fi

# ----------------------------
# Configure Nginx
# ----------------------------
echo "[deploy_hub] Configuring Nginx"
sudo cp "$APP_DIR/infra/nginx/confidential.conf" /etc/nginx/conf.d/confidential.conf

# Rename default config to avoid conflict if it exists
if [ -f /etc/nginx/conf.d/default.conf ]; then
    sudo mv /etc/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf.disabled
fi

# Ensure Nginx can read the files
sudo chmod -R 755 "$APP_DIR"
# Ensure Nginx is allowed to connect to network (SELinux)
if command -v getsebool &> /dev/null; then
    sudo setsebool -P httpd_can_network_connect 1 || true
fi

sudo systemctl enable --now nginx
sudo systemctl reload nginx

# ----------------------------
# Systemd service setup
# ----------------------------
sudo cp "$APP_DIR/infra/systemd/backend.service" /etc/systemd/system/backend.service
# Remove frontend service if it exists (replaced by Nginx)
sudo systemctl stop frontend.service || true
sudo systemctl disable frontend.service || true
sudo rm -f /etc/systemd/system/frontend.service

sudo systemctl daemon-reload
sudo systemctl restart backend.service
sudo systemctl enable backend.service

# Cleanup
echo "[deploy_hub] Cleaning up deployment artifacts..."
rm -f "$TAR_PATH"
rm -rf /tmp/infra

echo "[deploy_hub] Done"

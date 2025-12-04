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

install_packages() {
  if command -v apt-get >/dev/null 2>&1; then
    echo "[deploy_hub] Detected apt-based system"
    sudo apt-get update -y
    sudo apt-get install -y python3-venv python3-pip nodejs npm postgresql postgresql-contrib
  elif command -v yum >/dev/null 2>&1 || command -v dnf >/dev/null 2>&1; then
    echo "[deploy_hub] Detected yum/dnf-based system (Amazon Linux/RHEL family)"
    PM="yum"
    command -v dnf >/dev/null 2>&1 && PM="dnf"
    sudo ${PM} install -y python3 python3-pip python3-virtualenv nodejs npm postgresql postgresql-server
    if [ ! -d "/var/lib/pgsql/data/base" ] && { command -v postgresql-setup >/dev/null 2>&1 || [ -x /usr/libexec/postgresql-setup ]; }; then
      sudo postgresql-setup --initdb >/dev/null 2>&1 || sudo /usr/libexec/postgresql-setup --initdb >/dev/null 2>&1 || true
    fi
  else
    echo "[deploy_hub] Unsupported package manager. Install python3, nodejs, and postgresql manually." >&2
    exit 1
  fi
}

ensure_postgres_running() {
  local pg_service
  pg_service=$(systemctl list-unit-files | awk '/postgresql.*\.service/{print $1}' | head -n1)
  [ -z "$pg_service" ] && pg_service="postgresql.service"
  echo "[deploy_hub] Using Postgres service: $pg_service"
  sudo systemctl enable --now "$pg_service" || sudo systemctl start "$pg_service" || true
}

echo "[deploy_hub] Installing system dependencies"
install_packages

echo "[deploy_hub] Ensuring Postgres is running and database exists"
ensure_postgres_running
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='postgres';" | grep -q 1 || sudo -u postgres createuser postgres
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '${POSTGRES_PASSWORD}';" || true
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='${DB_NAME}';" | grep -q 1 || sudo -u postgres createdb "${DB_NAME}"

sudo mkdir -p "$APP_DIR"
sudo chown -R "$DEPLOY_USER":"$DEPLOY_USER" "$APP_DIR"
sudo tar -xzf "$TAR_PATH" -C "$APP_DIR" --strip-components=0

python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$BACKEND_DIR/app/requirements.txt"

# Ensure backend env has defaults if missing
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

sudo cp "$APP_DIR/infra/systemd/backend.service" /etc/systemd/system/backend.service
sudo cp "$APP_DIR/infra/systemd/frontend.service" /etc/systemd/system/frontend.service
sudo systemctl daemon-reload
sudo systemctl restart backend.service frontend.service
sudo systemctl enable backend.service frontend.service

echo "[deploy_hub] Done"

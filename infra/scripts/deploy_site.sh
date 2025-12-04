#!/usr/bin/env bash
set -euo pipefail

TAR_PATH="${1:-/tmp/confidential_site_bundle.tgz}"
APP_DIR="/opt/confidential"
DEPLOY_USER="${DEPLOY_USER:-ec2-user}"
SITE_DIR="$APP_DIR/site-node"
VENV_DIR="$APP_DIR/venv-site"

echo "[deploy_site] Using bundle: $TAR_PATH"

install_packages() {
  if command -v apt-get >/dev/null 2>&1; then
    echo "[deploy_site] Detected apt-based system"
    sudo apt-get update -y
    sudo apt-get install -y python3-venv python3-pip
  elif command -v yum >/dev/null 2>&1 || command -v dnf >/dev/null 2>&1; then
    echo "[deploy_site] Detected yum/dnf-based system (Amazon Linux/RHEL family)"
    PM="yum"
    command -v dnf >/dev/null 2>&1 && PM="dnf"
    sudo ${PM} install -y python3 python3-pip python3-virtualenv
  else
    echo "[deploy_site] Unsupported package manager. Install python3 manually." >&2
    exit 1
  fi
}

echo "[deploy_site] Installing system dependencies"
install_packages

sudo mkdir -p "$APP_DIR"
sudo chown -R "$DEPLOY_USER":"$DEPLOY_USER" "$APP_DIR"
sudo tar -xzf "$TAR_PATH" -C "$APP_DIR" --strip-components=0

python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$SITE_DIR/requirements.txt"

# Ensure site env has defaults if missing
SITE_ENV="$SITE_DIR/.env"
if [ ! -f "$SITE_ENV" ]; then
OPENAI_API_KEY_VAL="${OPENAI_API_KEY:-}"
cat <<EOF > "$SITE_ENV"
LLM_PROVIDER=openai
OPENAI_API_KEY=${OPENAI_API_KEY_VAL}
VECTOR_DB_MODE=local
CHROMA_DB_PATH=./data/chromadb_site1_db
SITE_ID=site_local
ENCLAVE_MODE=false
ENABLE_POLICY_VERIFICATION=false
EOF
fi

sudo cp "$APP_DIR/infra/systemd/site.service" /etc/systemd/system/site.service
sudo systemctl daemon-reload
sudo systemctl restart site.service
sudo systemctl enable site.service

echo "[deploy_site] Done"

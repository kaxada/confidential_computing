#!/usr/bin/env bash
set -euo pipefail

TAR_PATH="${1:-/tmp/confidential_bundle.tgz}"
APP_DIR="/opt/confidential"
DEPLOY_USER="${DEPLOY_USER:-ec2-user}"
BACKEND_DIR="$APP_DIR/backend"
FRONTEND_DIR="$APP_DIR/frontend"
VENV_DIR="$APP_DIR/venv"

echo "[deploy_hub] Using bundle: $TAR_PATH"

sudo mkdir -p "$APP_DIR"
sudo chown -R "$DEPLOY_USER":"$DEPLOY_USER" "$APP_DIR"
sudo tar -xzf "$TAR_PATH" -C "$APP_DIR" --strip-components=0

python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$BACKEND_DIR/app/requirements.txt"

sudo cp "$APP_DIR/infra/systemd/backend.service" /etc/systemd/system/backend.service
sudo cp "$APP_DIR/infra/systemd/frontend.service" /etc/systemd/system/frontend.service
sudo systemctl daemon-reload
sudo systemctl restart backend.service frontend.service
sudo systemctl enable backend.service frontend.service

echo "[deploy_hub] Done"
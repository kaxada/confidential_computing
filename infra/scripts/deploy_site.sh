#!/usr/bin/env bash
set -euo pipefail

TAR_PATH="${1:-/tmp/confidential_site_bundle.tgz}"
APP_DIR="/opt/confidential"
DEPLOY_USER="${DEPLOY_USER:-ec2-user}"
SITE_DIR="$APP_DIR/site-node"
VENV_DIR="$APP_DIR/venv-site"

echo "[deploy_site] Using bundle: $TAR_PATH"

sudo mkdir -p "$APP_DIR"
sudo chown -R "$DEPLOY_USER":"$DEPLOY_USER" "$APP_DIR"
sudo tar -xzf "$TAR_PATH" -C "$APP_DIR" --strip-components=0

python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$SITE_DIR/requirements.txt"

sudo cp "$APP_DIR/infra/systemd/site.service" /etc/systemd/system/site.service
sudo systemctl daemon-reload
sudo systemctl restart site.service
sudo systemctl enable site.service

echo "[deploy_site] Done"

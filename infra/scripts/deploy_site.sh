#!/usr/bin/env bash
set -euo pipefail

TAR_PATH="${1:-/tmp/confidential_site_bundle.tgz}"
SITE_DIR_NAME="${2:-site-node-one}"
SITE_PORT="${3:-8080}"

APP_DIR="/opt/confidential"
DEPLOY_USER="${DEPLOY_USER:-ec2-user}"
SITE_DIR="$APP_DIR/$SITE_DIR_NAME"
VENV_DIR="$APP_DIR/venv-$SITE_DIR_NAME"

echo "[deploy_site] Using bundle: $TAR_PATH"
echo "[deploy_site] Target Site: $SITE_DIR_NAME on Port: $SITE_PORT"

install_packages() {
  if command -v apt-get >/dev/null 2>&1; then
    echo "[deploy_site] Detected apt-based system"
    sudo apt-get update -y
    sudo apt-get install -y python3-venv python3-pip rsync
  elif command -v yum >/dev/null 2>&1 || command -v dnf >/dev/null 2>&1; then
    echo "[deploy_site] Detected yum/dnf-based system (Amazon Linux/RHEL family)"
    PM="yum"
    command -v dnf >/dev/null 2>&1 && PM="dnf"
    sudo ${PM} install -y python3 python3-pip python3-virtualenv rsync
  else
    echo "[deploy_site] Unsupported package manager. Install python3 manually." >&2
    exit 1
  fi
}

echo "[deploy_site] Installing system dependencies"
install_packages

sudo mkdir -p "$APP_DIR"

# Clean deploy using rsync
TEMP_DIR=$(mktemp -d)
echo "[deploy_site] Extracting to $TEMP_DIR"
tar -xzf "$TAR_PATH" -C "$TEMP_DIR"

echo "[deploy_site] Syncing to $APP_DIR"
sudo rsync -a --delete \
  --exclude "venv-$SITE_DIR_NAME" \
  --exclude "$SITE_DIR_NAME/venv" \
  --exclude "$SITE_DIR_NAME/.env" \
  --exclude "$SITE_DIR_NAME/data" \
  --exclude "$SITE_DIR_NAME/__pycache__" \
  "$TEMP_DIR/$SITE_DIR_NAME" "$APP_DIR/"

rm -rf "$TEMP_DIR"
sudo chown -R "$DEPLOY_USER":"$DEPLOY_USER" "$APP_DIR"

python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip

# Install CPU-only torch
echo "[deploy_site] Installing CPU-only PyTorch..."
pip install torch --index-url https://download.pytorch.org/whl/cpu

pip install -r "$SITE_DIR/requirements.txt"

# ----------------------------
# Build ChromaDB (default: only if missing)
# ----------------------------
BUILD_SCRIPT="$SITE_DIR/data/build_chromadb.py"
DB_DIR="$SITE_DIR/data/database"
FORCE_REBUILD_DB="${FORCE_REBUILD_DB:-false}"

if [ -f "$BUILD_SCRIPT" ]; then
    if [ "$FORCE_REBUILD_DB" = "true" ]; then
        echo "[deploy_site] FORCE_REBUILD_DB=true. Rebuilding ChromaDB at $DB_DIR..."
        BUILD_DB="true"
    else
        if [ -f "$DB_DIR/chroma.sqlite3" ]; then
            echo "[deploy_site] ChromaDB already exists and FORCE_REBUILD_DB=false. Skipping build."
            BUILD_DB="false"
        else
            echo "[deploy_site] ChromaDB not found at $DB_DIR. Building..."
            BUILD_DB="true"
        fi
    fi

    if [ "$BUILD_DB" = "true" ]; then
        (
            cd "$SITE_DIR"
            "$VENV_DIR/bin/python" data/build_chromadb.py
        )
    fi
else
    echo "[deploy_site] WARNING: Build script not found at $BUILD_SCRIPT. Skipping DB build."
fi

# Ensure site env has defaults if missing
SITE_ENV="$SITE_DIR/.env"
if [ ! -f "$SITE_ENV" ]; then
OPENAI_API_KEY_VAL="${OPENAI_API_KEY:-}"
cat <<EOF > "$SITE_ENV"
LLM_PROVIDER=openai
OPENAI_API_KEY=${OPENAI_API_KEY_VAL}
VECTOR_DB_MODE=local
CHROMA_DB_PATH=./data/database
SITE_ID=${SITE_DIR_NAME}
ENCLAVE_MODE=false
ENABLE_POLICY_VERIFICATION=false
EOF
else
    if [ -n "${OPENAI_API_KEY:-}" ]; then
        echo "[deploy_site] Updating OPENAI_API_KEY in .env"
        if grep -q "OPENAI_API_KEY=" "$SITE_ENV"; then
            sed -i "s|^OPENAI_API_KEY=.*|OPENAI_API_KEY=$OPENAI_API_KEY|g" "$SITE_ENV"
        else
            echo "OPENAI_API_KEY=$OPENAI_API_KEY" >> "$SITE_ENV"
        fi
    fi
fi

# Dynamically create systemd service
SERVICE_NAME="${SITE_DIR_NAME}.service"
echo "[deploy_site] Configuring systemd service: $SERVICE_NAME"

sudo bash -c "cat > /etc/systemd/system/${SERVICE_NAME} <<EOF
[Unit]
Description=Confidential Site Node ($SITE_DIR_NAME)
After=network.target

[Service]
Type=simple
User=$DEPLOY_USER
WorkingDirectory=$SITE_DIR
EnvironmentFile=-$SITE_ENV
ExecStart=/bin/bash -lc 'source $VENV_DIR/bin/activate && uvicorn server:app --host 0.0.0.0 --port $SITE_PORT'
Restart=always

[Install]
WantedBy=multi-user.target
EOF"

sudo systemctl daemon-reload
sudo systemctl restart "$SERVICE_NAME"
sudo systemctl enable "$SERVICE_NAME"

echo "[deploy_site] Cleaning up deployment artifacts..."
rm -f "$TAR_PATH"
rm -rf /tmp/infra

echo "[deploy_site] Done deploying $SITE_DIR_NAME"

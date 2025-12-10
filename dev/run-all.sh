#!/usr/bin/env bash
set -euo pipefail

# Trap Ctrl+C (SIGINT) and SIGTERM to kill all background processes
# kill -- -$$ sends the signal to the entire process group
trap "trap - SIGTERM && kill -- -$$" SIGINT SIGTERM EXIT

echo "-----------------------------------------------------"
echo "   Starting Confidential Computing Dev Environment   "
echo "-----------------------------------------------------"

# Function to check and install Python dependencies
check_python_deps() {
  local dir="$1"
  local venv_name="$2"
  local venv_path="$dir/$venv_name"

  echo "  -> Checking Python dependencies in $dir..."
  if [ ! -d "$venv_path" ]; then
    echo "    -> Creating venv in $venv_path..."
    python3 -m venv "$venv_path"
  fi
  source "$venv_path/bin/activate"
  pip install --upgrade pip >/dev/null 2>&1
  
  # Install/update packages from requirements.txt
  if [ -f "$dir/requirements.txt" ]; then
    pip install -r "$dir/requirements.txt"
  fi
  
  # Regenerate requirements.txt to capture new packages added manually
  pip freeze > "$dir/requirements.txt"
  deactivate
  echo "  -> Python dependencies checked for $dir."
}

# Function to check and install Node.js dependencies
check_node_deps() {
  local dir="$1"
  echo "  -> Checking Node.js dependencies in $dir..."
  ( # Run in subshell to avoid changing caller's directory
    cd "$dir"
    npm install
    # npm install automatically updates package-lock.json if package.json changes
  )
  echo "  -> Node.js dependencies checked for $dir."
}


# 1. Backend (Hub) - Port 8000
echo ""
echo "[Backend] Preparing..."
check_python_deps "backend" "venv"
echo "[Backend] Starting on http://localhost:8000..."
(
  cd backend
  source venv/bin/activate # Re-activate for this subshell
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
) &


# 2. Frontend - Port 5173
echo ""
echo "[Frontend] Preparing..."
check_node_deps "frontend"
echo "[Frontend] Starting on http://localhost:5173..."
(
  cd frontend
  # Ensure VITE_API_BASE points to backend for local dev
  export VITE_API_BASE=http://localhost:8000
  npm run dev -- --host 0.0.0.0 --port 5173
) &


# 3. Site Node One - Port 8080
echo ""
echo "[Site 1] Preparing..."
check_python_deps "site-node-one" "venv"
echo "[Site 1] Starting on http://localhost:8080..."
(
  cd site-node-one
  source venv/bin/activate
  uvicorn server:app --reload --host 0.0.0.0 --port 8080 --env-file .env
) &


# 4. Site Node Two - Port 8081
echo ""
echo "[Site 2] Preparing..."
check_python_deps "site-node-two" "venv"
echo "[Site 2] Starting on http://localhost:8081..."
(
  cd site-node-two
  source venv/bin/activate
  uvicorn server:app --reload --host 0.0.0.0 --port 8081 --env-file .env
) &


# 5. Site Node Three - Port 8082
echo ""
echo "[Site 3] Preparing..."
check_python_deps "site-node-three" "venv"
echo "[Site 3] Starting on http://localhost:8082..."
(
  cd site-node-three
  source venv/bin/activate
  uvicorn server:app --reload --host 0.0.0.0 --port 8082 --env-file .env
) &

echo ""
echo "All services started. Press Ctrl+C to stop them."
wait

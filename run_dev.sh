#!/usr/bin/env bash
set -euo pipefail

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Cleanup function to kill background jobs and update requirements
cleanup() {


    log_info "Stopping all services..."
    # Kill all background jobs started by this script
    # We use jobs -p to get PIDs of background processes (which are now the direct services due to 'exec')
    jobs -p | xargs -r kill
    wait
    log_info "Services stopped. Exiting."
}

# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM EXIT

echo -e "${BLUE}-----------------------------------------------------${NC}"
echo -e "${BLUE}   Starting Confidential Computing Dev Environment   ${NC}"
echo -e "${BLUE}-----------------------------------------------------${NC}"

# Ensure logs directory exists
mkdir -p logs

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_err() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check and install Python dependencies
check_python_deps() {
  local dir="$1"
  local venv_name="$2"
  local venv_path="$dir/$venv_name"

  echo -n "  -> Checking Python dependencies in $dir... "
  
  if [ ! -d "$venv_path" ]; then
    echo -n "(creating venv) "
    python3 -m venv "$venv_path"
  fi
  
  source "$venv_path/bin/activate"
  pip install -q --upgrade pip
  
  # Force CPU-only torch installation
  pip install -q torch --index-url https://download.pytorch.org/whl/cpu

  # Install/update packages from requirements.txt
  if [ -f "$dir/requirements.txt" ]; then
    pip install -q -r "$dir/requirements.txt"
  fi
  
  
  deactivate
  echo -e "${GREEN}Done.${NC}"
}

# Function to check and install Node.js dependencies
check_node_deps() {
  local dir="$1"
  echo -n "  -> Checking Node.js dependencies in $dir... "
  if [ ! -d "$dir/node_modules" ]; then
      echo -n "(installing) "
      (cd "$dir" && npm install --silent >/dev/null 2>&1)
  else
      # Quick check
      (cd "$dir" && npm install --silent >/dev/null 2>&1)
  fi
  echo -e "${GREEN}Done.${NC}"
}

# 1. Backend (Hub) - Port 8000
echo ""
log_info "Preparing Backend..."
check_python_deps "backend" "venv"

if [ ! -f "backend/.env" ]; then
    log_warn "backend/.env not found! Backend may fail to connect to DB."
else
    if grep -q "sqlite" backend/.env && [ ! -f "dev.db" ]; then
        log_warn "Configured for SQLite but dev.db not found in root."
    fi
fi

log_info "Starting Backend on http://localhost:8000..."
echo "      Logs: logs/backend.log"
(
  cd backend
  source venv/bin/activate
  # Use exec to replace the subshell with the process, ensuring it's a direct child of the script
  exec uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > ../logs/backend.log 2>&1
) &


# 2. Frontend - Port 5173
echo ""
log_info "Preparing Frontend..."
check_node_deps "frontend"
log_info "Starting Frontend on http://localhost:5173..."
echo "      Logs: logs/frontend.log"
(
  cd frontend
  export VITE_API_BASE=http://localhost:8000
  exec npm run dev -- --host 0.0.0.0 --port 5173 > ../logs/frontend.log 2>&1
) &


# 3. Site Node One - Port 8080
echo ""
log_info "Preparing Site 1..."
check_python_deps "site-node-one" "venv"
log_info "Starting Site 1 on http://localhost:8080..."
echo "      Logs: logs/site_1.log"
(
  cd site-node-one
  source venv/bin/activate
  exec uvicorn server:app --reload --host 0.0.0.0 --port 8080 --env-file .env > ../logs/site_1.log 2>&1
) &


# 4. Site Node Two - Port 8081
echo ""
log_info "Preparing Site 2..."
check_python_deps "site-node-two" "venv"
log_info "Starting Site 2 on http://localhost:8081..."
echo "      Logs: logs/site_2.log"
(
  cd site-node-two
  source venv/bin/activate
  exec uvicorn server:app --reload --host 0.0.0.0 --port 8081 --env-file .env > ../logs/site_2.log 2>&1
) &


# 5. Site Node Three - Port 8082
echo ""
log_info "Preparing Site 3..."
check_python_deps "site-node-three" "venv"
log_info "Starting Site 3 on http://localhost:8082..."
echo "      Logs: logs/site_3.log"
(
  cd site-node-three
  source venv/bin/activate
  exec uvicorn server:app --reload --host 0.0.0.0 --port 8082 --env-file .env > ../logs/site_3.log 2>&1
) &

echo ""
echo -e "${BLUE}-----------------------------------------------------${NC}"
echo -e "${GREEN}   All services started!   ${NC}"
echo -e "${BLUE}-----------------------------------------------------${NC}"
echo "You can view logs using: tail -f logs/*.log"
echo "Press Ctrl+C to stop all services."
wait
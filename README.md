# confidential_computing

Working toward a confidential-computing-backed RAG chatbot. See `docs/step1-mvp-slice.md` for the vertical-slice spec.

## Backend
- Env: copy `backend/.env.example` to `.env` and set `DATABASE_URL`, JWT settings, `SITE_BASE_URL`.
- Run dev server: `source venv/bin/activate && cd backend && uvicorn app.main:app --reload --port 8000`
- Site RAG service (from `site-node/`): `cd site-node && python site_service.py` (listens on 9000 by default)
- Tests: `pip install -r backend/requirements-dev.txt && cd backend && pytest`

## Frontend (React + Vite)
- Install deps: `cd frontend && npm install`
- Run dev server: `npm run dev` (defaults to http://localhost:5173, targeting `VITE_API_BASE` env or `http://127.0.0.1:8000`)
- Build: `npm run build`

## Dev: run all services
- `./dev/run-all.sh` (requires `venv` set up and `npm` present)

## CI/CD (GitHub Actions)
- `.github/workflows/deploy-hub.yml`: deploys backend + built frontend to hub host when backend/frontend/infra change.
- `.github/workflows/deploy-site.yml`: deploys site-node to site host when site-node/infra change.
- Remote deploy scripts/systemd: see `infra/scripts/` and `infra/systemd/`. Configure secrets:
  - Hub: `HUB_HOST`, `USER`, `SSH_KEY`
  - Site: `SITE_HOST`, `USER`, `SSH_KEY`
  - Deploy scripts expect app root at `/opt/confidential` on the target hosts.

# confidential_computing

Working toward a confidential-computing-backed RAG chatbot. See `docs/step1-mvp-slice.md` for the vertical-slice spec.

## Backend
- Run dev server: `source venv/bin/activate && cd backend && uvicorn app.main:app --reload --port 8000`
- DB: configure `DATABASE_URL` via env (default `postgresql+psycopg://postgres:postgres@localhost:5432/confidential_rag`).
- Stub site (optional): `source venv/bin/activate && python site-node/stub_site.py` (listens on 9000)

## Tests
- Install dev deps: `pip install -r backend/requirements-dev.txt`
- Run backend tests: `cd backend && pytest`

## Frontend (simple HTML)
- Serve locally: `cd frontend && python -m http.server 3000`
- Open: `http://localhost:3000` (talks to backend at `http://127.0.0.1:8000`)

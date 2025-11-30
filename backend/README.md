# Backend notes

## Env
- Copy `.env.example` to `.env` and set:
  - `DATABASE_URL`
  - `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXP_MINUTES`
  - `SITE_BASE_URL`

## Run
- `source ../venv/bin/activate`
- `uvicorn app.main:app --reload --port 8000`

## Tests
- `pip install -r requirements-dev.txt`
- `pytest`

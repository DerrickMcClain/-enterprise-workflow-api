# Enterprise Task & Workflow Management API

Multi-tenant project management and workflow **REST API** (FastAPI, PostgreSQL, SQLAlchemy 2, Redis, Celery, Alembic, Docker). Each **workspace** is a tenant: members, projects, tasks, comments, attachments, audit logs, and productivity reports are scoped to that workspace with **admin / manager / member** roles.

## Features

- **Auth:** register, login, JWT access + refresh (rotation in DB), logout with access-token **JTI denylist** in Redis, email verification and password reset tokens in Redis, bcrypt passwords.
- **Multi-tenancy:** workspaces, membership, role checks on every mutating path.
- **Domain:** projects (status rules), tasks (priority, due dates, assignees, soft delete), comments, file attachments (size/type validation, **local disk** or **optional S3** when `S3_BUCKET` is set).
- **Background jobs:** Celery (email delivery when SMTP is set, overdue reminders, refresh-token cleanup).
- **Caching:** Redis for productivity report and token/revocation patterns.
- **Ops:** health/ready, request IDs, OpenAPI at `/docs`, Alembic migrations, Docker Compose, **GitHub Actions (pytest on every push/PR; optional SSH deploy to a VPS)**, pytest.

## CI/CD and production deploy

- **CI:** `.github/workflows/ci-cd.yml` — installs dependencies and runs `pytest` on every push/PR to `main`, `master`, or `develop`.
- **Deploy (optional):** set repository variable `ENABLE_SSH_DEPLOY` to `true` and add secrets `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`, `DEPLOY_PATH`. Pushes to **`main`** or **`master`** will SSH into your server, `git pull`, and `docker compose -f docker-compose.prod.yml up -d --build` after tests pass. Full steps: **[DEPLOY.md](DEPLOY.md)**.

Production compose file: **`docker-compose.prod.yml`** (DB/Redis only on localhost by default, `ENVIRONMENT=production`, S3 env vars). Put HTTPS (e.g. Caddy) in front of `127.0.0.1:8000`.

## Run locally (Docker)

```bash
cp .env.example .env
# set SECRET_KEY to a long random value
docker compose up --build
```

- API: `http://localhost:8000` — OpenAPI: `http://localhost:8000/docs`
- Migrations run on API container start; add a worker: `docker compose up worker` (or scale as needed).

## Run locally (without Docker)

- PostgreSQL 16+ and Redis 6+ on localhost (see `.env.example`).
- `alembic upgrade head`
- `uvicorn app.main:app --reload`
- `celery -A app.workers.celery_app:celery_app worker -l info` (and optionally `beat` for schedules).

## Seed data

With `DATABASE_URL` set and schema migrated:

```bash
python -m scripts.seed_data
```

Default user: `seed@example.com` / `password12` (change in production).

## Main API shape

All routes are under the configured `API_PREFIX` (default `/api`).

| Area | Examples |
|------|----------|
| Auth | `POST /api/auth/register`, `POST /api/auth/login`, `POST /api/auth/refresh`, `POST /api/auth/logout`, `POST /api/auth/verify-email`, password reset |
| Users | `GET /api/users/me`, `PATCH /api/users/me` |
| Workspaces | `GET/POST /api/workspaces`, `GET /api/workspaces/{id}`, `POST /api/workspaces/{id}/members` |
| Projects | `GET /api/projects?workspace_id=`, `POST /api/projects?workspace_id=`, `GET|PATCH|DELETE /api/projects/{id}` |
| Tasks | `GET /api/tasks?project_id=`, `POST /api/tasks?project_id=`, `GET|PATCH|DELETE /api/tasks/{id}`, `POST /api/tasks/{id}/comments`, `POST /api/tasks/{id}/attachments` (multipart) |
| Reports | `GET /api/reports/productivity?workspace_id=`, `GET /api/audit-logs?workspace_id=` |
| System | `GET /api/health`, `GET /api/ready` |

## Tests

```bash
pip install -r requirements.txt
pytest tests/
```

## Push to GitHub (first time)

Step-by-step: **[docs/GITHUB_SETUP.md](docs/GITHUB_SETUP.md)** (create empty repo, `git push`, then enable Actions + optional deploy).

## License

Use freely for a portfolio; production use requires your own hardening, monitoring, and secrets management.

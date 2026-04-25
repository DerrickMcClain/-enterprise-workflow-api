# Deployment (VPS + Docker + GitHub Actions)

This project runs as **Docker Compose** (Postgres, Redis, API, Celery worker, Celery beat). For a public URL you need a **server** (e.g. DigitalOcean Droplet, Hetzner, AWS EC2) and usually **TLS** in front (Caddy or nginx) pointing at `127.0.0.1:8000`.

## 1. One-time: prepare the server

- Ubuntu 22.04+ (or similar) with a non-root user that can run Docker, or `sudo`.
- Open firewall: **22** (SSH), **80/443** (if you use Caddy in front; API listens on `127.0.0.1:8000` in `docker-compose.prod.yml` by default so it is not exposed to the public internet without a reverse proxy).
- [Install Docker Engine and Compose plugin](https://docs.docker.com/engine/install/ubuntu/).

## 2. One-time: clone the repo and create `.env` on the server

```bash
sudo mkdir -p /opt/enterprise-workflow-api
sudo chown "$USER:$USER" /opt/enterprise-workflow-api
cd /opt/enterprise-workflow-api
git clone https://github.com/YOUR_ORG/YOUR_REPO.git .
# Or use a deploy key for private repos
```

Copy your production secrets (never commit them):

- `cp .env.example .env` and fill at least: `SECRET_KEY` (32+ random chars), `POSTGRES_PASSWORD`, and match `DATABASE_URL` to the same user/password in `POSTGRES_USER` / `POSTGRES_DB` if you change defaults.
- In `docker-compose.prod.yml`, the default DB user is `workflow`; your `DATABASE_URL` should be  
  `postgresql+psycopg2://workflow:YOUR_DB_PASSWORD@db:5432/workflow`.

Optional **S3** (attachments in the cloud):

- `S3_BUCKET=your-bucket`
- `AWS_REGION=us-east-1`
- On **EC2**, use an **IAM instance role** and leave `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` empty in `.env`.
- For **S3-compatible** (MinIO, DO Spaces), set `S3_ENDPOINT_URL`.

Start once:

```bash
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

Put **HTTPS** in front, for example [Caddy](https://caddyserver.com/docs/quick-starts/reverse-proxy) on the same host, proxying `https://api.yourdomain.com` → `127.0.0.1:8000`. Point DNS **A/AAAA** record to the server’s public IP.

## 3. GitHub Actions: test + automatic deploy

Tests run on every push/PR. **Deploy** only runs on pushes to **`main`** (or your primary branch) when a repository variable is turned on.

### Repository variable (required to enable deploy)

- GitHub → **Settings → Secrets and variables → Actions → Variables**
- New variable: **`ENABLE_SSH_DEPLOY`** = `true`

If this is **not** set to `true`, the deploy job is skipped; tests still run.

### Repository secrets (for deploy)

| Name | Value |
|------|--------|
| `DEPLOY_HOST` | Public IP or hostname of your VPS (SSH) |
| `DEPLOY_USER` | SSH user (e.g. `ubuntu`, `debian`, `root`) |
| `DEPLOY_SSH_KEY` | **Private** key (full PEM), same key whose public part is in `~/.ssh/authorized_keys` on the server |
| `DEPLOY_PATH` | Absolute path to the git repo on the server, e.g. `/opt/enterprise-workflow-api` |

The deploy step runs (after tests pass):

```text
cd $DEPLOY_PATH
git pull origin main
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

**Requirements on the server**

- The clone must track **`main`** and allow `git pull` (add a [deploy key](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys#deploy-keys) for private repositories).
- `.env` must already exist and stay on the server (not in git).

**Optional:** change `git pull origin main` in `.github/workflows/ci-cd.yml` if your default branch is different.

## 4. What you can list on a resume

- *“CI with pytest on every PR; main-branch deploys over SSH to a Docker Compose stack on a VPS, with S3 for attachment storage.”*

## 5. Health checks

After deploy:

- `https://your-api-domain.com/api/health`
- `https://your-api-domain.com/api/ready` (DB + Redis)
- `https://your-api-domain.com/docs`

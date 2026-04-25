# First-time GitHub + CI (and optional deploy)

## 1. Create a new empty repository on GitHub

1. Log in to [https://github.com/new](https://github.com/new).
2. **Repository name:** e.g. `enterprise-workflow-api` (or any name you like).
3. Choose **Public** (or Private).
4. **Do not** add a README, .gitignore, or license (this project already has files).
5. Click **Create repository**.

Copy the **HTTPS** URL GitHub shows, e.g. `https://github.com/YOUR_USERNAME/enterprise-workflow-api.git`

## 2. Push this folder from your PC (PowerShell)

Run from the project folder (adjust the path if yours is different):

```powershell
cd C:\Users\derri\Desktop\enterprise-workflow-api
git init
git branch -M main
git add .
git commit -m "Initial commit: Enterprise Workflow API"
git remote add origin https://github.com/YOUR_USERNAME/enterprise-workflow-api.git
git push -u origin main
```

If GitHub asks for a password, use a **Personal Access Token** (PAT) with `repo` scope, not your account password:  
[https://github.com/settings/tokens](https://github.com/settings/tokens)

## 3. Confirm CI (pytest) runs

After the first push, open:

**`https://github.com/YOUR_USERNAME/enterprise-workflow-api/actions`**

You should see the **“CI and deploy”** workflow with a **test** job (green = pytest passed).  
**Deploy** will **not** run yet (that is correct until you turn it on in step 4).

## 4. When your VPS is ready: enable deploy

In the repo: **Settings → Secrets and variables → Actions**

### Variables (not secret)

- **Name:** `ENABLE_SSH_DEPLOY`  
- **Value:** `true`  

(If this variable is missing or not `true`, only **tests** run; **deploy** is skipped.)

### Secrets (Repository secrets)

| Name | What to put |
|------|-------------|
| `DEPLOY_HOST` | Your server IP or hostname (SSH) |
| `DEPLOY_USER` | SSH login name (e.g. `ubuntu`, `debian`) |
| `DEPLOY_SSH_KEY` | **Full** private key (PEM), including `-----BEGIN…` lines |
| `DEPLOY_PATH` | Full path to the git clone on the server, e.g. `/opt/enterprise-workflow-api` |

Set up the server as described in **`DEPLOY.md`** (Docker, clone, `.env` on the server, deploy key for private repo if needed).

Then push to `main` again; the workflow should run **test** then **deploy**.

## 5. If you do not have a VPS yet

- Leave **`ENABLE_SSH_DEPLOY`** unset (or not `true`).  
- You still get **CI on every push** (pytest).  
- Add the variable and secrets when the server is ready.

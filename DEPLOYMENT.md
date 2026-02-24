# Deployment Guide – Paintify

Deploy the frontend and backend to GitHub and optional cloud services.

---

## 1. Push to GitHub

```bash
git add .
git commit -m "Add deployment config"
git remote add origin https://github.com/YOUR_USERNAME/paintify.git
git push -u origin main
```

---

## 2. Frontend – GitHub Pages

The frontend deploys to GitHub Pages on every push to `main`.

### Setup

1. In your repo: **Settings → Pages**
2. Under **Source**, choose **GitHub Actions**
3. Push to `main` or run the workflow manually

### Environment variable

Set the backend API URL for production:

1. **Settings → Secrets and variables → Actions**
2. Add **Variables** → `VITE_INVOICE_API_URL` = `https://your-backend-url.com` (no trailing slash)

After deployment, the app will be at:

`https://YOUR_USERNAME.github.io/paintify/`

---

## 3. Backend – Railway (optional)

The backend workflow validates on every push. To deploy to Railway:

### Setup

1. Create an account at [railway.app](https://railway.app)
2. **New Project** → **Deploy from GitHub repo** → select `paintify`
3. Set **Root Directory** to `invoice_backend`
4. Add environment variables in Railway:
   - `USE_SQLITE=1` (or configure MySQL)
   - `DJANGO_SECRET_KEY` (generate a secure key)
   - `DEBUG=0`
   - `ALLOWED_HOSTS=your-app.railway.app,localhost`
5. Copy your **Railway API token** from [railway.app/account](https://railway.app/account)
6. In GitHub: **Settings → Secrets → Actions** → add `RAILWAY_TOKEN`

### CORS

In Railway, add your frontend URL to CORS:

- `CORS_ORIGINS=https://YOUR_USERNAME.github.io`

---

## 4. Connect frontend and backend

1. Deploy the backend on Railway and copy its URL (e.g. `https://paintify-backend.up.railway.app`)
2. In GitHub repo **Settings → Secrets and variables → Actions**, set:
   - `VITE_INVOICE_API_URL` = `https://paintify-backend.up.railway.app`
3. Re-run the frontend workflow or push a new commit so the frontend rebuilds with the correct API URL

---

## 5. Alternative: Render

For Render instead of Railway:

1. Create a **Web Service** and connect your GitHub repo
2. **Root Directory**: `invoice_backend`
3. **Build Command**: `pip install -r requirements-sqlite.txt`
4. **Start Command**: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
5. Add the same environment variables as above

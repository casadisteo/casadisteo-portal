# casadisteo-portal
casadisteo webpage

## Publish a Hello World page (GitHub Pages + custom domain)

This repo includes a static homepage at `docs/index.html` that you can publish to `casadisteo.com` using GitHub Pages.

### 1) Commit + push

```bash
git add docs README.md
git commit -m "Add Hello World homepage for GitHub Pages"
git push
```

### 2) Enable GitHub Pages

In your GitHub repo:

- Go to **Settings** → **Pages**
- **Build and deployment**
  - **Source**: “Deploy from a branch”
  - **Branch**: `main`
  - **Folder**: `/docs`
- Save

GitHub will show the Pages URL once it’s published.

### 3) Point your domain DNS at GitHub Pages

In your DNS provider for `casadisteo.com`:

- **A records (apex)**: add these 4 records
  - `@` → `185.199.108.153`
  - `@` → `185.199.109.153`
  - `@` → `185.199.110.153`
  - `@` → `185.199.111.153`
- **CNAME (www)**:
  - `www` → `<your-github-username>.github.io`

Notes:
- The `docs/CNAME` file in this repo sets the custom domain to `casadisteo.com`.
- DNS can take a bit to propagate; HTTPS may take a little longer to appear in GitHub Pages.

## Private supplies portal (Render + Google Sheets)

This repo also contains a private Streamlit portal (`app.py`) you can deploy on Render and point to `portal.casadisteo.com`.

### Google Sheet setup

Create a Google Sheet with a tab named `inventory` and headers like:

- `item`
- `current_qty`
- `reorder_at`
- `unit` (optional)
- `notes` (optional)

### Secrets (login + Google Sheets)

Copy `.streamlit/secrets.toml.example` and fill it in. On Render, add it as a **Secret File** at path:

Create a Secret File named:

`secrets.toml`

Render will mount it at `/etc/secrets/secrets.toml`, and the service startup will copy it into `.streamlit/secrets.toml` automatically.

### Deploy to Render

- Create a new **Web Service**
- Connect this GitHub repo
- Render will detect `render.yaml`
- Deploy

### Point `portal.casadisteo.com` to Render

In Namecheap Advanced DNS:

- Add a **CNAME** record:
  - **Host**: `portal`
  - **Value**: the hostname Render gives you for the service (e.g. `your-service.onrender.com`)

Then add the custom domain in Render for the service and enable HTTPS.

# Deploy the UW Degree Mapper

Recommended setup: GitHub for source control and Vercel for public hosting.

The browser first loads `data/catalog-live.json` when present, then falls back to `data/catalog-fallback.json`. `server.py` is only needed for local development and refreshing the catalog.

## Local testing

```powershell
py server.py
```

Open `http://localhost:5173`.

## Refresh the catalog before publishing

```powershell
py server.py --sync-only
```

This creates or updates `data/catalog-live.json`. Commit that file if you want the public website to use the refreshed catalog.

## Publish changes

```powershell
git add .
git commit -m "Describe the change"
git push
```

A Vercel project connected to the GitHub repository will deploy the pushed commit automatically.

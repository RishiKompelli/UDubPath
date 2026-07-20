# UW Degree Mapper

No npm or pip installation is required.

## Run locally in VS Code

Open this folder in VS Code, open PowerShell, and run:

```powershell
py server.py
```

Then open:

```text
http://localhost:5173
```

Stop the server with `Ctrl + C`.

## Refresh the official UW catalog

```powershell
py server.py --sync-only
```

This writes `data/catalog-live.json`. The website uses that file when present and otherwise uses `data/catalog-fallback.json`.

## Deploy with Vercel

1. Upload this complete folder to a GitHub repository.
2. In Vercel, import the repository.
3. Choose **Other** as the framework preset.
4. Leave Build Command, Install Command, and Output Directory blank.
5. Deploy.

The website is static on Vercel. `server.py` is only for local development and catalog refreshes.

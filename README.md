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

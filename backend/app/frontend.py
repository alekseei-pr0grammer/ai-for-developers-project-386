"""Serving the built frontend (the Vite `dist/` directory) from the API process,
so one container runs the whole app."""

from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse

# Vite puts a content hash in asset file names, so they can be cached forever.
IMMUTABLE = "public, max-age=31536000, immutable"
# Everything else, index.html above all, is revalidated so new deploys show up at once.
REVALIDATE = "no-cache"


def add_frontend(app: FastAPI, dist: Path) -> None:
    """Serve files from `dist`, and the app page for every other path outside /api,
    so client-side routes such as /{handle} load the app."""
    root = dist.resolve()
    index = root / "index.html"

    @app.api_route("/{path:path}", methods=["GET", "HEAD"], include_in_schema=False)
    def frontend(path: str) -> FileResponse:
        if path == "api" or path.startswith("api/"):
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        file = (root / path).resolve()
        if file.is_relative_to(root) and file.is_file():
            cache = IMMUTABLE if file.is_relative_to(root / "assets") else REVALIDATE
            return FileResponse(file, headers={"Cache-Control": cache})
        if path.startswith("assets/"):
            raise HTTPException(status.HTTP_404_NOT_FOUND)
        return FileResponse(index, headers={"Cache-Control": REVALIDATE})

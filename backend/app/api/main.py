"""Minimal application entrypoint.

TICKET-002 needs the backend container to serve something so that
``docker compose up -d`` can reach all-healthy and ``GET /healthz`` can return
200. TICKET-037 replaces this with the real FastAPI skeleton: settings, seeded
roles and the error model.
"""

from fastapi import FastAPI

app = FastAPI(title="Revenue Leakage Investigator", version="0.1.0")


@app.get("/healthz")
def healthz() -> dict[str, str]:
    """Liveness probe. The Docker healthcheck calls this."""
    return {"status": "ok"}

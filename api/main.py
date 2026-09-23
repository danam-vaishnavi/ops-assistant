"""
FastAPI service for the ops assistant.
Run locally with: uvicorn api.main:app --reload
"""
import time
from collections import defaultdict
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
from retrieval.generate import answer
from agent.triage import triage

app = FastAPI(title="Ops Ticket Assistant API")

# --- Simple in-memory rate limiter: N requests per IP per hour ---
RATE_LIMIT = 20
WINDOW_SECONDS = 3600
_request_log: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(client_ip: str):
    now = time.time()
    recent = [t for t in _request_log[client_ip] if now - t < WINDOW_SECONDS]
    _request_log[client_ip] = recent
    if len(recent) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Try again later.")
    _request_log[client_ip].append(now)


class TicketRequest(BaseModel):
    text: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/answer")
def get_answer(req: TicketRequest, request: Request):
    check_rate_limit(request.client.host)
    try:
        return answer(req.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/triage")
def get_triage(req: TicketRequest, request: Request):
    check_rate_limit(request.client.host)
    try:
        return {"result": triage(req.text)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

"""RRBridge-compatible ingestion and outbound-polling command API."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from . import store

@asynccontextmanager
async def lifespan(app):
    store.init()
    yield

app = FastAPI(title="RomRaiderServer PoC", lifespan=lifespan)

def auth(expected, authorization):
    if not expected or authorization != "Bearer " + expected:
        raise HTTPException(401, "unauthorized")

def ingest_auth(authorization: str | None = Header(None)):
    auth(os.getenv("INGEST_TOKEN"), authorization)

def agent_auth(authorization: str | None = Header(None)):
    auth(os.getenv("AGENT_TOKEN"), authorization)

@app.get("/health")
def health():
    return {"ok": True, "service": "RomRaiderServer-PoC"}

@app.post("/ingest", dependencies=[Depends(ingest_auth)])
async def ingest(request: Request):
    body = await request.body()
    if len(body) > 524288:
        raise HTTPException(413, "request too large")
    try:
        return store.ingest(body.decode("utf-8"))
    except (ValueError, UnicodeError, OverflowError) as exc:
        raise HTTPException(400, str(exc))

@app.get("/agent/commands/next", dependencies=[Depends(agent_auth)])
def next_command():
    return {"command": store.claim()}

class Completion(BaseModel):
    result: dict

@app.post("/agent/commands/{command_id}/complete", dependencies=[Depends(agent_auth)])
def finish(command_id: int, payload: Completion):
    if not store.complete(command_id, payload.result):
        raise HTTPException(409, "command missing or not leased")
    return {"ok": True}

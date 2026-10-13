"""Isolated product-v1 FastAPI application. Existing PoC endpoints are untouched."""
from contextlib import asynccontextmanager
from datetime import datetime
from math import isfinite
from typing import Annotated, Literal
from uuid import UUID
import hashlib
import os
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from psycopg.errors import IntegrityError

from . import store


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


def check_aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Timestamp must include timezone")
    return value


class ProfileParameter(StrictModel):
    parameter_id: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=256)
    unit: str = Field(max_length=32)


class ProfileRevision(StrictModel):
    protocol_version: Literal[1]
    device_id: UUID
    vehicle_id: UUID
    profile_revision_id: UUID
    logger_definition_fingerprint: str = Field(min_length=1, max_length=256)
    parameters: list[ProfileParameter] = Field(min_length=1, max_length=200)


class MeasurementValue(StrictModel):
    parameter_id: str = Field(min_length=1, max_length=120)
    value: float

    @field_validator("value", mode="before")
    @classmethod
    def valid_number(cls, value):
        if type(value) not in (int, float) or not isfinite(value):
            raise ValueError("value must be a finite JSON number")
        return value


class RecordCommon(StrictModel):
    record_id: UUID
    captured_at: datetime
    source_kind: Literal["ecu", "synthetic", "agent"]
    segment_id: UUID | None = None

    @field_validator("captured_at")
    @classmethod
    def aware(cls, value):
        return check_aware(value)


class Observation(RecordCommon):
    kind: Literal["observation"]
    segment_id: UUID
    source_kind: Literal["ecu", "synthetic"]
    sequence: int = Field(ge=0)
    profile_revision_id: UUID
    values: list[MeasurementValue] = Field(min_length=1, max_length=200)


class Event(RecordCommon):
    kind: Literal["event"]
    event_type: str = Field(min_length=1, max_length=120)
    data: dict


class Gap(RecordCommon):
    kind: Literal["gap"]
    event_type: str = Field(min_length=1, max_length=120)
    data: dict


class Batch(StrictModel):
    protocol_version: Literal[1]
    batch_id: UUID
    device_id: UUID
    vehicle_id: UUID
    run_id: UUID
    records: list[Annotated[Observation | Event | Gap, Field(discriminator="kind")]] = Field(
        min_length=1, max_length=128
    )


class Acquisition(StrictModel):
    last_observed_at: datetime | None
    recent_hz: float | None
    drop_count: int = Field(ge=0)


class Spool(StrictModel):
    unacked_records: int = Field(ge=0)
    pending_bytes: int = Field(ge=0)


class DeviceStatus(StrictModel):
    protocol_version: Literal[1]
    device_id: UUID
    vehicle_id: UUID
    reported_at: datetime
    agent_version: str
    logger_state: Literal["not_started", "starting", "logging", "stopped", "error", "unknown"]
    acquisition: Acquisition
    spool: Spool
    run_id: UUID | None = None
    segment_id: UUID | None = None
    profile_revision_id: UUID | None = None

    @field_validator("reported_at")
    @classmethod
    def aware(cls, value):
        return check_aware(value)


@asynccontextmanager
async def lifespan(app: FastAPI):
    store.init_schema()
    yield


app = FastAPI(title="RomLogger Product Agent API v1", lifespan=lifespan)


def fail(status: int, code: str, message: str, details=None):
    return HTTPException(status, detail={"error": {"code": code, "message": message,
                                                    "retryable": status >= 500,
                                                    "details": details or {}}})


def require_device(authorization: str | None = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise fail(401, "UNAUTHORIZED", "Device authentication required")
    secret = authorization[7:]
    if not secret or len(secret) > 512:
        raise fail(401, "UNAUTHORIZED", "Invalid device token")
    fingerprint = hashlib.sha256(secret.encode("utf-8")).hexdigest()
    with store.connect() as db:
        row = db.execute("""SELECT device_id,vehicle_id,token_sha256 FROM v1_devices
                 WHERE token_sha256=%s AND revoked_at IS NULL""", (fingerprint,)).fetchone()
    if not row or not secrets.compare_digest(row["token_sha256"], fingerprint):
        raise fail(401, "UNAUTHORIZED", "Invalid device credentials")
    return row


@app.exception_handler(store.DomainError)
async def domain_error_handler(request: Request, exc: store.DomainError):
    return JSONResponse(status_code=exc.status, content={
        "error": {"code": exc.code, "message": exc.message, "retryable": False,
                  "details": exc.details}})


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    # A concurrent duplicate/constraint failure is never an ACK.
    return JSONResponse(status_code=409, content={
        "error": {"code": "DATABASE_CONSTRAINT_CONFLICT", "message": "Conflicting record",
                  "retryable": False}})


@app.get("/health")
def health():
    return {"ok": True, "service": "RomLogger-product-v1"}


@app.put("/api/agent/v1/profile-revisions/{profile_revision_id}")
def put_profile(profile_revision_id: UUID, request: ProfileRevision, response: Response,
                device=Depends(require_device)):
    if profile_revision_id != request.profile_revision_id:
        raise fail(422, "PROFILE_ID_MISMATCH", "URL and body profile IDs differ")
    result = store.register_profile(device,request.model_dump(mode="json"))
    response.status_code = 201 if result["status"] == "registered" else 200
    return result


@app.post("/api/agent/v1/telemetry/batches")
def post_batch(request: Batch, device=Depends(require_device)):
    return store.ingest_batch(device,request.model_dump(mode="json",exclude_none=True))


@app.post("/api/agent/v1/status")
def post_status(request: DeviceStatus, device=Depends(require_device)):
    return store.update_status(device,request.model_dump(mode="json",exclude_none=True))


@app.get("/api/agent/v1/telemetry/recent")
def recent(limit: int = Query(100, ge=1, le=500), device=Depends(require_device)):
    """Temporary authenticated readback for the Server-first phase, NOT public MCP."""
    return store.recent_records(device,limit)

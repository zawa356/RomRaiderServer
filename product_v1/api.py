"""Isolated product-v1 FastAPI application. Existing PoC endpoints are untouched."""
from contextlib import asynccontextmanager
from datetime import datetime
from math import isfinite
from typing import Annotated, Literal
from uuid import UUID, uuid4
import hashlib
import os
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, ConfigDict, Field, field_validator
from psycopg.errors import IntegrityError

from . import store, commands


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


class CapabilityParameter(StrictModel):
    parameter_id: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=256)
    unit: str = Field(max_length=64)
    availability: Literal["defined", "possibly_supported", "verified_readable",
                          "unsupported", "unknown"]
    evidence: str | None = Field(default=None, max_length=512)


class CapabilitySnapshot(StrictModel):
    protocol_version: Literal[1]
    device_id: UUID
    vehicle_id: UUID
    logger_version: str = Field(min_length=1, max_length=120)
    definition_fingerprint: str = Field(min_length=1, max_length=256)
    ecu_identity: str | None = Field(default=None, max_length=256)
    observed_at: datetime
    parameters: list[CapabilityParameter] = Field(max_length=1000)

    @field_validator("observed_at")
    @classmethod
    def aware(cls, value):
        return check_aware(value)


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


class CommandClaimRequest(StrictModel):
    protocol_version: Literal[1]
    device_id: UUID
    vehicle_id: UUID
    current_plan_revision_id: UUID | None = None
    client_state_revision: str = Field(min_length=1,max_length=128)


class CommandReportRequest(StrictModel):
    protocol_version: Literal[1]
    device_id: UUID
    vehicle_id: UUID
    command_id: UUID
    report_id: UUID
    state: Literal["received","rejected","applying","applied_unverified",
                   "verified","failed","expired","cancelled","unknown"]
    observed_profile_revision_id: UUID | None = None
    result_reason: str | None = Field(default=None,max_length=1024)
    reported_at: datetime

    @field_validator("reported_at")
    @classmethod
    def aware(cls, value):
        return check_aware(value)


class ReconcileRequest(StrictModel):
    protocol_version: Literal[1]
    device_id: UUID
    vehicle_id: UUID
    reported_at: datetime
    client_state_revision: str = Field(min_length=1,max_length=128)
    current_run_id: UUID | None = None
    observed_profile_revision_id: UUID | None = None
    last_command_id: UUID | None = None
    local_execution_records: list[dict] = Field(default_factory=list,max_length=64)

    @field_validator("reported_at")
    @classmethod
    def aware(cls, value):
        return check_aware(value)


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
    store.require_schema()
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


def error_response(request: Request, status: int, code: str, message: str,
                   retryable: bool = False, details=None):
    return JSONResponse(status_code=status, content={
        "request_id": getattr(request.state, "request_id", str(uuid4())),
        "error": {"code": code, "message": message, "retryable": retryable,
                  "details": details or {}}})


@app.middleware("http")
async def request_guard(request: Request, call_next):
    request.state.request_id = str(uuid4())
    if request.url.path == "/api/agent/v1/telemetry/batches":
        max_bytes = 512 * 1024
        # A bounded body check is required even when Content-Length is omitted.
        size = request.headers.get("content-length")
        if size is not None:
            try:
                if int(size) > max_bytes:
                    return error_response(request, 413, "PAYLOAD_TOO_LARGE",
                                          "Maximum batch body size exceeded")
            except ValueError:
                return error_response(request, 400, "BAD_CONTENT_LENGTH",
                                      "Invalid Content-Length header")
        if len(await request.body()) > max_bytes:
            return error_response(request, 413, "PAYLOAD_TOO_LARGE",
                                  "Maximum batch body size exceeded")
    return await call_next(request)


@app.exception_handler(store.DomainError)
async def domain_error_handler(request: Request, exc: store.DomainError):
    return error_response(request, exc.status, exc.code, exc.message,
                          details=exc.details)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    # A concurrent duplicate/constraint failure is never an ACK.
    return error_response(request, 409, "DATABASE_CONSTRAINT_CONFLICT",
                          "Conflicting record")


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException):
    detail = exc.detail
    if isinstance(detail, dict) and isinstance(detail.get("error"), dict):
        e = detail["error"]
        return error_response(request, exc.status_code, e["code"], e["message"],
                              retryable=e.get("retryable", False),
                              details=e.get("details"))
    return error_response(request, exc.status_code, "HTTP_ERROR",
                          "The operation was rejected")


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    # Do not echo raw user-supplied input, Authorization or stack traces.
    issues = [{"loc": [str(p) for p in e.get("loc", ())],
               "type": e.get("type", "invalid")} for e in exc.errors()]
    return error_response(request, 422, "INVALID_REQUEST",
                          "Request does not match the v1 schema",
                          details={"issues": issues})


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


@app.put("/api/agent/v1/capability-snapshots/{snapshot_id}")
def put_capability(snapshot_id: UUID, request: CapabilitySnapshot, response: Response,
                   device=Depends(require_device)):
    result = store.register_capability(device,str(snapshot_id),
                                       request.model_dump(mode="json",exclude_none=True))
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

@app.post("/api/agent/v1/reconcile")
def agent_reconcile(request: ReconcileRequest, device=Depends(require_device)):
    return commands.reconcile(device,request.model_dump(mode="json",exclude_none=True))


@app.post("/api/agent/v1/commands/claim")
def agent_claim(request: CommandClaimRequest, device=Depends(require_device)):
    return commands.claim(device,request.model_dump(mode="json",exclude_none=True))


@app.post("/api/agent/v1/commands/{command_id}/report")
def agent_report(command_id: UUID, request: CommandReportRequest,
                 device=Depends(require_device)):
    return commands.report(device,command_id,request.model_dump(mode="json",exclude_none=True))


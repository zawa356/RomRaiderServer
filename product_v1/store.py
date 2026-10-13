"""Product v1 database operations. Never imports or alters the legacy PoC store."""
import hashlib
import json
import os
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


class DomainError(Exception):
    def __init__(self, status: int, code: str, message: str, details: dict | None = None):
        self.status, self.code, self.message = status, code, message
        self.details = details or {}
        super().__init__(message)


def connect():
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)


def require_schema():
    """Read-only startup check. Migrations are a separate, explicit operation."""
    with connect() as db:
        try:
            row = db.execute(
                "SELECT version_num FROM v1_alembic_version"
            ).fetchone()
        except psycopg.errors.UndefinedTable as exc:
            raise RuntimeError(
                "Product v1 schema is not migrated; run python -m product_v1.migrate upgrade"
            ) from exc
    if row is None or row["version_num"] != "0001_initial":
        raise RuntimeError(
            "Incompatible product-v1 schema version; migrate before starting the API"
        )


def normalized(obj) -> bytes:
    """Canonical logical value encoding; never includes transport batch_id."""
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":")).encode("utf-8")


def digest(obj) -> str:
    return hashlib.sha256(normalized(obj)).hexdigest()


def register_profile(device: dict, payload: dict):
    vehicle, ident = device["vehicle_id"], payload["profile_revision_id"]
    if str(device["device_id"]) != payload["device_id"] or str(vehicle) != payload["vehicle_id"]:
        raise DomainError(403, "DEVICE_SCOPE", "Device or vehicle mismatch")
    params = payload["parameters"]
    names = [p["parameter_id"] for p in params]
    if len(names) != len(set(names)):
        raise DomainError(422, "DUPLICATE_PARAMETER", "Repeated parameter ID")
    signature = digest(payload)
    with connect() as db:
        db.execute("SELECT vehicle_id FROM v1_vehicles WHERE vehicle_id=%s FOR UPDATE", (vehicle,))
        inserted = db.execute("""INSERT INTO v1_profile_revisions
            (profile_revision_id,device_id,vehicle_id,payload,content_hash)
            VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING
            RETURNING profile_revision_id""",
            (ident,device["device_id"],vehicle,Jsonb(payload),signature)).fetchone()
        row = db.execute("""SELECT device_id,vehicle_id,content_hash
              FROM v1_profile_revisions WHERE profile_revision_id=%s""",(ident,)).fetchone()
        if (row["content_hash"] != signature or row["device_id"] != device["device_id"]
                or row["vehicle_id"] != vehicle):
            raise DomainError(409, "PROFILE_REVISION_CONFLICT", "Profile ID has different content")
    return {"status": "registered" if inserted else "already_registered", "profile_revision_id": ident}


def _ensure_run(db, device, run_id):
    db.execute("""INSERT INTO v1_runs(run_id,device_id,vehicle_id) VALUES (%s,%s,%s)
        ON CONFLICT DO NOTHING""", (run_id,device["device_id"],device["vehicle_id"]))
    row = db.execute("SELECT device_id,vehicle_id FROM v1_runs WHERE run_id=%s", (run_id,)).fetchone()
    if row["device_id"] != device["device_id"] or row["vehicle_id"] != device["vehicle_id"]:
        raise DomainError(409, "RUN_CONFLICT", "Run belongs to another device or vehicle")


def _ensure_segment(db, run_id, segment_id, profile_id):
    if segment_id is None:
        return
    db.execute("""INSERT INTO v1_segments(segment_id,run_id,profile_revision_id)
        VALUES (%s,%s,%s) ON CONFLICT DO NOTHING""", (segment_id,run_id,profile_id))
    row = db.execute("SELECT run_id,profile_revision_id FROM v1_segments WHERE segment_id=%s FOR UPDATE",
                     (segment_id,)).fetchone()
    if row["run_id"] != UUID(run_id):
        raise DomainError(409, "SEGMENT_CONFLICT", "Segment belongs to a different run")
    if profile_id is not None:
        if row["profile_revision_id"] is None:
            db.execute("UPDATE v1_segments SET profile_revision_id=%s WHERE segment_id=%s",
                       (profile_id,segment_id))
        elif row["profile_revision_id"] != UUID(profile_id):
            raise DomainError(409, "SEGMENT_PROFILE_CONFLICT", "Segment profile changed without a new segment")


def ingest_batch(device: dict, payload: dict):
    if payload["device_id"] != str(device["device_id"]) or payload["vehicle_id"] != str(device["vehicle_id"]):
        raise DomainError(403, "DEVICE_SCOPE", "Device or vehicle mismatch")
    recs = payload["records"]
    ids = [rec["record_id"] for rec in recs]
    if len(ids) != len(set(ids)):
        raise DomainError(422, "DUPLICATE_RECORD_IN_BATCH", "Repeated record ID in a single batch")
    new_count = duplicate_count = 0
    with connect() as db:
        vehicle_id = device["vehicle_id"]
        # Serializes both ingest commits and cursor watermark creation, per vehicle.
        v = db.execute("SELECT vehicle_id FROM v1_vehicles WHERE vehicle_id=%s FOR UPDATE",
                       (vehicle_id,)).fetchone()
        if not v:
            raise DomainError(403, "DEVICE_SCOPE", "Vehicle not registered")
        _ensure_run(db, device, payload["run_id"])
        db.execute("""INSERT INTO v1_ingest_clock(vehicle_id,last_seq) VALUES (%s,0)
            ON CONFLICT DO NOTHING""", (vehicle_id,))
        for rec in recs:
            rec_hash = digest({"device_id": payload["device_id"], "vehicle_id": payload["vehicle_id"],
                               "run_id": payload["run_id"], "record": rec})
            old = db.execute("SELECT content_hash FROM v1_records WHERE record_id=%s",
                             (rec["record_id"],)).fetchone()
            if old:
                if old["content_hash"] != rec_hash:
                    raise DomainError(409, "RECORD_ID_CONFLICT",
                                      "Record ID is already used for different data",
                                      {"record_id": rec["record_id"]})
                duplicate_count += 1
                continue
            if rec["kind"] == "observation":
                p = db.execute("""SELECT device_id,vehicle_id,payload
                     FROM v1_profile_revisions WHERE profile_revision_id=%s""",
                    (rec["profile_revision_id"],)).fetchone()
                if not p:
                    raise DomainError(422, "UNKNOWN_PROFILE_REVISION", "Register profile definition first",
                                      {"record_id": rec["record_id"]})
                if p["device_id"] != device["device_id"] or p["vehicle_id"] != vehicle_id:
                    raise DomainError(409, "PROFILE_SCOPE", "Profile belongs to another device or vehicle")
                supported = {p["parameter_id"] for p in p["payload"]["parameters"]}
                fields = [v["parameter_id"] for v in rec["values"]]
                if len(fields) != len(set(fields)) or not set(fields).issubset(supported):
                    raise DomainError(422, "PARAMETER_MISMATCH", "Invalid or duplicate parameter",
                                      {"record_id": rec["record_id"]})
                collision = db.execute("""SELECT record_id FROM v1_records
                     WHERE run_id=%s AND kind='observation' AND sequence=%s""",
                      (payload["run_id"],rec["sequence"])).fetchone()
                if collision:
                    raise DomainError(409, "SEQUENCE_CONFLICT", "Sequence already used by another record",
                                      {"record_id": rec["record_id"]})
                _ensure_segment(db,payload["run_id"],rec["segment_id"],rec["profile_revision_id"])
            else:
                _ensure_segment(db,payload["run_id"],rec.get("segment_id"),None)
            seq = db.execute("""UPDATE v1_ingest_clock SET last_seq=last_seq+1
                   WHERE vehicle_id=%s RETURNING last_seq""",(vehicle_id,)).fetchone()["last_seq"]
            db.execute("""INSERT INTO v1_records(record_id,device_id,vehicle_id,run_id,
                 segment_id,kind,sequence,captured_at,source_kind,profile_revision_id,
                 content_hash,payload,ingest_seq)
                 VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (rec["record_id"],device["device_id"],vehicle_id,payload["run_id"],
                 rec.get("segment_id"),rec["kind"],rec.get("sequence"),
                 rec["captured_at"],rec["source_kind"],rec.get("profile_revision_id"),
                 rec_hash,Jsonb(rec),seq))
            if rec["kind"] == "observation":
                for value in rec["values"]:
                    db.execute("""INSERT INTO v1_values(record_id,parameter_id,value)
                          VALUES(%s,%s,%s)""",(rec["record_id"],value["parameter_id"],value["value"]))
            new_count += 1
        # db context commits only if all checks, inserts and indexes succeeded.
    return {"status":"committed","batch_id":payload["batch_id"],
            "record_count":len(recs),"inserted_count":new_count,"duplicate_count":duplicate_count}


def update_status(device, payload):
    if payload["device_id"] != str(device["device_id"]) or payload["vehicle_id"] != str(device["vehicle_id"]):
        raise DomainError(403,"DEVICE_SCOPE","Device or vehicle mismatch")
    with connect() as db:
        db.execute("""INSERT INTO v1_device_status(device_id,vehicle_id,reported_at,state)
            VALUES(%s,%s,%s,%s) ON CONFLICT (device_id) DO UPDATE SET
            reported_at=EXCLUDED.reported_at,received_at=now(),state=EXCLUDED.state
            WHERE v1_device_status.reported_at<=EXCLUDED.reported_at""",
            (device["device_id"],device["vehicle_id"],payload["reported_at"],Jsonb(payload)))
        ts = db.execute("SELECT now() AS received").fetchone()["received"]
    return {"status":"recorded","server_received_at":ts.isoformat()}


def recent_records(device, limit: int = 100):
    with connect() as db:
        rows=db.execute("""SELECT record_id,run_id,sequence,captured_at,source_kind,
                 payload,ingest_seq FROM v1_records WHERE vehicle_id=%s AND kind='observation'
                 ORDER BY ingest_seq DESC LIMIT %s""",(device["vehicle_id"],limit)).fetchall()
    return {"rows":[{"record_id":str(r["record_id"]), "run_id":str(r["run_id"]),
                      "sequence":r["sequence"],"captured_at":r["captured_at"].isoformat(),
                      "source_kind":r["source_kind"],"values":r["payload"]["values"],
                      "ingest_seq":r["ingest_seq"]} for r in rows],"returned":len(rows)}

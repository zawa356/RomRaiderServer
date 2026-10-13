"""Database primitives; PoC only. No vehicle commands are executed here."""
import os
from datetime import datetime, timezone
import psycopg
from psycopg.rows import dict_row

def connect():
    return psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)

from threading import Lock
_INIT_LOCK = Lock()
_SCHEMA_READY = False

def init():
    global _SCHEMA_READY
    with _INIT_LOCK:
        if _SCHEMA_READY:
            return
        with connect() as db:
            # All PoC containers (api/mcp/voice-demo) initialize simultaneously.
            # CREATE TABLE IF NOT EXISTS alone does not serialize PostgreSQL
            # system-catalog writes across processes. Hold a transaction-scoped
            # advisory lock for the *entire* set of DDL operations.
            db.execute("SELECT pg_advisory_xact_lock(731193027141464)")
            db.execute("""CREATE TABLE IF NOT EXISTS samples (
                session text NOT NULL, seq bigint NOT NULL, segment integer NOT NULL,
                timestamp_ms bigint NOT NULL, values_json jsonb NOT NULL,
                received_at timestamptz NOT NULL DEFAULT now(),
                PRIMARY KEY (session, seq))""")
            db.execute("""CREATE TABLE IF NOT EXISTS parameters (
                session text NOT NULL, segment integer NOT NULL, param_id text NOT NULL,
                name text NOT NULL, units text NOT NULL,
                PRIMARY KEY (session, segment, param_id))""")
            db.execute("""CREATE TABLE IF NOT EXISTS events (
                id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                session text NOT NULL, segment integer NOT NULL,
                timestamp_ms bigint NOT NULL, message text NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS commands (
                id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                command text NOT NULL, profile text, status text NOT NULL DEFAULT 'pending',
                created_at timestamptz NOT NULL DEFAULT now(),
                leased_until timestamptz, result jsonb,
                completed_at timestamptz)""")

            db.execute("ALTER TABLE commands ADD COLUMN IF NOT EXISTS target_mode text NOT NULL DEFAULT 'mock'")
            db.execute("""CREATE TABLE IF NOT EXISTS voice_requests (
                id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                command text NOT NULL, profile text NOT NULL,
                state text NOT NULL DEFAULT 'proposed',
                created_at timestamptz NOT NULL DEFAULT now(),
                expires_at timestamptz NOT NULL DEFAULT (now() + interval '2 minutes'),
                command_id bigint)""")

        _SCHEMA_READY = True

def ingest(body):
    inserted = duplicates = 0
    with connect() as db:
        for raw in body.splitlines():
            if not raw.strip():
                continue
            parts = raw.split("\t")
            kind = parts[0]
            if kind == "M" and len(parts) == 6:
                _, session, segment, pid, name, units = parts
                db.execute("""INSERT INTO parameters VALUES (%s,%s,%s,%s,%s)
                    ON CONFLICT DO NOTHING""", (session,int(segment),pid,name,units))
            elif kind == "S" and len(parts) == 6:
                _, session, segment, seq, ts, vals = parts
                values = {}
                for pair in vals.split(","):
                    key, sep, val = pair.partition("=")
                    if not sep or not key:
                        raise ValueError("bad sample value")
                    values[key] = float(val)
                import json
                row = db.execute("""INSERT INTO samples
                    (session,seq,segment,timestamp_ms,values_json)
                    VALUES (%s,%s,%s,%s,%s::jsonb) ON CONFLICT DO NOTHING
                    RETURNING seq""", (session,int(seq),int(segment),int(ts),json.dumps(values))).fetchone()
                inserted += bool(row)
                duplicates += not bool(row)
            elif kind == "E" and len(parts) == 5:
                _, session, segment, ts, message = parts
                db.execute("INSERT INTO events(session,segment,timestamp_ms,message) VALUES (%s,%s,%s,%s)",
                           (session,int(segment),int(ts),message))
            else:
                raise ValueError("invalid TSV record")
    return {"ok": True, "samples": inserted, "duplicates": duplicates}

def latest():
    with connect() as db:
        row = db.execute("""SELECT session,seq,segment,timestamp_ms,values_json
                            FROM samples ORDER BY received_at DESC, seq DESC LIMIT 1""").fetchone()
    return dict(row) if row else {"status":"no_samples"}

ALLOWED = {"logging_start", "logging_stop", "filelog_start", "filelog_stop", "switch_profile"}
PROFILES = {"basic.xml", "fuel.xml"}
import re

def submit(command, profile=None):
    if command not in ALLOWED:
        raise ValueError("command not allowed")
    if command == "switch_profile":
        if profile not in PROFILES:
            raise ValueError("profile is not in server-side allowlist")
    elif profile:
        raise ValueError("profile not accepted for this command")
    with connect() as db:
        row = db.execute("INSERT INTO commands(command,profile,target_mode) VALUES (%s,%s,'mock') RETURNING id",
                         (command,profile)).fetchone()
    return {"id":row["id"],"status":"pending","command":command,"profile":profile}

def claim(mode="mock"):
    if mode not in ("mock", "real"):
        raise ValueError("invalid command target mode")
    with connect() as db:
        db.execute("""UPDATE commands SET status='expired'
                      WHERE status IN ('pending','leased')
                        AND created_at <= now() - interval '2 minutes'""")
        row=db.execute("""UPDATE commands SET status='leased',
            leased_until=now()+interval '30 seconds'
            WHERE id=(SELECT id FROM commands
                WHERE target_mode=%s AND created_at > now() - interval '2 minutes'
                  AND (status='pending' OR (status='leased' AND leased_until<now()))
                ORDER BY id FOR UPDATE SKIP LOCKED LIMIT 1)
            RETURNING id,command,profile,target_mode""", (mode,)).fetchone()
    return dict(row) if row else None

def complete(command_id, result):
    import json
    with connect() as db:
        row=db.execute("""UPDATE commands SET status='completed',result=%s::jsonb,
            completed_at=now(),leased_until=NULL WHERE id=%s AND status='leased'
            RETURNING id""",(json.dumps(result),command_id)).fetchone()
    return bool(row)

def command_status(command_id):
    with connect() as db:
        row=db.execute("SELECT id,command,profile,target_mode,status,result FROM commands WHERE id=%s",(command_id,)).fetchone()
    return dict(row) if row else None

def propose_voice(profile):
    """Unauthenticated demo: store a short-lived proposal, NEVER an executable command."""
    if profile not in PROFILES:
        raise ValueError("only basic.xml or fuel.xml are allowed")
    with connect() as db:
        # Global database-backed quota for this deliberately no-auth demo route.
        quota = db.execute("""SELECT count(*) AS n FROM voice_requests
                              WHERE created_at > now() - interval '1 hour'""").fetchone()["n"]
        if quota >= 5:
            return {"accepted": False, "error": "demo proposal quota reached; try later"}
        row = db.execute("""INSERT INTO voice_requests(command,profile)
                            VALUES ('switch_profile',%s)
                            RETURNING id,expires_at""", (profile,)).fetchone()
    return {"accepted": True, "request_id": row["id"], "state": "proposed",
            "profile": profile, "executed": False,
            "message": "A proposal only. Local operator approval and X270 checks are required."}

def voice_request_status(request_id):
    with connect() as db:
        row=db.execute("""SELECT v.id,v.state,v.profile,v.command_id,v.expires_at,
                                 c.status AS command_status,c.result AS command_result
                          FROM voice_requests v
                          LEFT JOIN commands c ON c.id=v.command_id
                          WHERE v.id=%s""", (request_id,)).fetchone()
    if not row:
        return {"found": False}
    from datetime import datetime, timezone
    state = row["state"]
    if state == "proposed" and datetime.now(timezone.utc) >= row["expires_at"]:
        state = "expired"
    result = row["command_result"] or {}
    return {"found": True, "request_id":row["id"],"state":state,
            "profile":row["profile"], "command_status":row["command_status"],
            "result_ok":result.get("ok") if row["command_status"]=="completed" else None,
            "real_rrbridge":result.get("real_rrbridge",False)
              if row["command_status"]=="completed" else False}


def latest_selftest():
    """Return the latest *proven* RRBridge synthetic selftest sample.

    Fail closed: a TEST_* key alone is insufficient. Require exactly the
    expected three IDs, known metadata from Stream.selftest(), and a matching
    'selftest start' event in the same session and segment. No real ECU fields
    or general telemetry can leave through the unauthenticated voice-demo.
    """
    with connect() as db:
        row = db.execute("""
            SELECT s.session, s.segment, s.seq, s.timestamp_ms, s.values_json
            FROM samples AS s
            WHERE s.values_json ?& ARRAY['TEST_RPM','TEST_TPS','TEST_MRP']::text[]
              AND (s.values_json - 'TEST_RPM' - 'TEST_TPS' - 'TEST_MRP') = '{}'::jsonb
              AND EXISTS (
                SELECT 1 FROM parameters AS p
                WHERE p.session=s.session AND p.segment=s.segment
                  AND p.param_id='TEST_RPM'
                  AND p.name='Selftest Engine Speed' AND p.units='rpm')
              AND EXISTS (
                SELECT 1 FROM parameters AS p
                WHERE p.session=s.session AND p.segment=s.segment
                  AND p.param_id='TEST_TPS'
                  AND p.name='Selftest Throttle' AND p.units='%')
              AND EXISTS (
                SELECT 1 FROM parameters AS p
                WHERE p.session=s.session AND p.segment=s.segment
                  AND p.param_id='TEST_MRP'
                  AND p.name='Selftest Manifold Rel Pressure' AND p.units='kPa')
              AND EXISTS (
                SELECT 1 FROM events AS e
                WHERE e.session=s.session AND e.segment=s.segment
                  AND e.message ~ '^selftest start count=[0-9]+ hz=[0-9]+$')
            ORDER BY s.received_at DESC, s.seq DESC LIMIT 1
        """).fetchone()
    if not row:
        return {
            "available": False,
            "synthetic": True,
            "live": False,
            "message": "No verified RRBridge synthetic selftest sample found.",
        }
    values = row["values_json"]
    return {
        "available": True,
        "synthetic": True,
        "live": False,
        "session": row["session"],
        "segment": row["segment"],
        "seq": row["seq"],
        "timestamp_ms": row["timestamp_ms"],
        "engine_rpm": float(values["TEST_RPM"]),
        "throttle_percent": float(values["TEST_TPS"]),
        "manifold_relative_pressure_kpa": float(values["TEST_MRP"]),
        "message": "RRBridge selftest synthetic data; not a live ECU reading.",
    }

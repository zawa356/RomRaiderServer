"""Phase 1.2-A: real PostgreSQL fault, concurrency and lost-ACK contract tests.

These are synthetic fixtures; they do NOT validate an ECU, Java Agent or spool.
The tests must never connect to non-disposable PostgreSQL environments.
"""
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4
import hashlib

import psycopg
import pytest
from fastapi.testclient import TestClient

from product_v1 import api, store

ROOT = "/api/agent/v1"


@pytest.fixture
def subject():
    store.require_schema()
    vehicle_id, device_id, profile_id = uuid4(), uuid4(), uuid4()
    token = "ci_ingest_fault_" + uuid4().hex
    with store.connect() as db:
        db.execute("INSERT INTO v1_vehicles(vehicle_id,display_name) VALUES (%s,%s)",
                   (vehicle_id, "synthetic fault test vehicle"))
        db.execute("INSERT INTO v1_devices(device_id,vehicle_id,token_sha256) VALUES (%s,%s,%s)",
                   (device_id,vehicle_id,hashlib.sha256(token.encode()).hexdigest()))
    profile = {
        "protocol_version": 1, "device_id": str(device_id),
        "vehicle_id": str(vehicle_id), "profile_revision_id": str(profile_id),
        "logger_definition_fingerprint": "synthetic-fault-definition",
        "parameters": [{"parameter_id": "P8", "name": "Engine RPM", "unit": "rpm"}]
    }
    with TestClient(api.app, raise_server_exceptions=False) as client:
        response=client.put(f"{ROOT}/profile-revisions/{profile_id}",
                            json=profile,headers={"Authorization":"Bearer "+token})
        assert response.status_code==201,response.text
        yield {"client":client,"vehicle":str(vehicle_id),"device":str(device_id),
               "profile":str(profile_id),"headers":{"Authorization":"Bearer "+token}}


def one(subject, run, seq, segment, record_id=None, rpm=2500):
    return {
        "record_id": str(record_id or uuid4()),
        "kind": "observation",
        "segment_id": str(segment),
        "sequence": seq,
        "captured_at": "2026-10-13T01:00:01Z",
        "source_kind": "synthetic",
        "profile_revision_id": subject["profile"],
        "values": [{"parameter_id": "P8", "value": rpm}],
    }


def batch(subject, run, records, batch_id=None):
    return {
        "protocol_version": 1,
        "batch_id": str(batch_id or uuid4()),
        "device_id": subject["device"], "vehicle_id": subject["vehicle"],
        "run_id": str(run), "records": records,
    }


def post(subject, payload):
    return subject["client"].post(f"{ROOT}/telemetry/batches",json=payload,
                                  headers=subject["headers"])


def rows(subject, run):
    with store.connect() as db:
        found=db.execute("""
            SELECT record_id,sequence,payload,ingest_seq
            FROM v1_records WHERE run_id=%s AND kind='observation'
            ORDER BY sequence
        """,(run,)).fetchall()
        clock=db.execute("SELECT last_seq FROM v1_ingest_clock WHERE vehicle_id=%s",
                         (subject["vehicle"],)).fetchone()
    return found, clock["last_seq"] if clock else None


def test_lost_ack_after_real_commit_retries_idempotently(subject, monkeypatch):
    run, segment = uuid4(),uuid4()
    samples=[one(subject,run,i,segment,rpm=2500+i) for i in range(5)]
    request=batch(subject,run,samples)
    original=store.ingest_batch

    def commit_then_lose_http_response(device,payload):
        result=original(device,payload)  # DB transaction has already committed.
        assert result["record_count"]==5
        raise psycopg.OperationalError("synthetic-fault-secret-DSN-hidden")

    monkeypatch.setattr(api.store,"ingest_batch",commit_then_lose_http_response)
    lost=post(subject,request)
    assert lost.status_code==503,lost.text
    assert lost.json()["error"]["code"]=="STORAGE_UNAVAILABLE"
    assert lost.json()["error"]["retryable"] is True
    assert "synthetic-fault-secret-DSN-hidden" not in lost.text
    assert lost.json()["request_id"]
    before, clock_before=rows(subject,run)
    assert len(before)==5
    monkeypatch.setattr(api.store,"ingest_batch",original)

    # The same durable data can be sent with a NEW transport batch_id.
    retry=post(subject,batch(subject,run,samples))
    assert retry.status_code==200,retry.text
    ack=retry.json()
    assert ack["status"]=="committed" and ack["record_count"]==5
    assert ack["inserted_count"]==0 and ack["duplicate_count"]==5
    after,clock_after=rows(subject,run)
    assert [r["record_id"] for r in before]==[r["record_id"] for r in after]
    assert clock_after==clock_before, "Replay must not advance ingest watermark"


def test_actual_postgres_exception_rolls_back_entire_batch(subject):
    run,segment=uuid4(),uuid4()
    a=one(subject,run,0,segment)
    b=one(subject,run,1,segment)
    payload=batch(subject,run,[a,b])
    trigger_name="v1_ci_fault_trigger"
    function_name="v1_ci_fault_function"
    # This trigger deliberately makes PostgreSQL reject the SECOND insert
    # after the first observation, values and ingest counter were modified.
    # It proves the real transaction rolls back everything, not just inserts.
    # The UUID is generated in the test and therefore safe to interpolate.
    sql=f"""
        CREATE OR REPLACE FUNCTION {function_name}() RETURNS trigger AS $$
        BEGIN
          IF NEW.record_id = '{b["record_id"]}'::uuid THEN
            RAISE EXCEPTION 'synthetic-ci-db-failure';
          END IF;
          RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """
    with store.connect() as db:
        db.execute(sql)
        db.execute(f"""
          CREATE TRIGGER {trigger_name}
          BEFORE INSERT ON v1_records
          FOR EACH ROW EXECUTE FUNCTION {function_name}()
        """)
    try:
        refused=post(subject,payload)
        assert refused.status_code >= 400,refused.text
        assert not (refused.status_code==200 and refused.json().get("status")=="committed")
        found,clock=rows(subject,run)
        assert found==[], "First record must roll back with second record"
        assert clock is None, "Watermark must roll back with failed ingest"
        with store.connect() as db:
            assert db.execute("SELECT count(*) AS n FROM v1_values WHERE record_id=%s",
                              (a["record_id"],)).fetchone()["n"]==0
            assert db.execute("SELECT count(*) AS n FROM v1_segments WHERE segment_id=%s",
                              (segment,)).fetchone()["n"]==0
    finally:
        with store.connect() as db:
            db.execute(f"DROP TRIGGER IF EXISTS {trigger_name} ON v1_records")
            db.execute(f"DROP FUNCTION IF EXISTS {function_name}()")
    successful=post(subject,payload)
    assert successful.status_code==200,successful.text
    assert successful.json()["inserted_count"]==2
    found,clock=rows(subject,run)
    assert len(found)==2 and clock==2


def test_parallel_identical_batches_converge_to_one_copy(subject):
    run,segment=uuid4(),uuid4()
    entries=[one(subject,run,i,segment) for i in range(8)]
    requests=[batch(subject,run,entries) for _ in range(4)]
    with ThreadPoolExecutor(max_workers=4) as pool:
        responses=list(pool.map(lambda req: post(subject,req),requests))
    assert all(x.status_code==200 for x in responses),[r.text for r in responses]
    result=[r.json() for r in responses]
    assert sum(r["inserted_count"] for r in result)==8
    assert sum(r["duplicate_count"] for r in result)==24
    assert all(r["inserted_count"]+r["duplicate_count"]==8 for r in result)
    stored,clock=rows(subject,run)
    assert len(stored)==8 and clock==8
    assert len({r["record_id"] for r in stored})==8


def test_parallel_conflicting_payload_keeps_exactly_one_original(subject):
    run,segment,ident=uuid4(),uuid4(),uuid4()
    variants=[
        batch(subject,run,[one(subject,run,0,segment,record_id=ident,rpm=3100)]),
        batch(subject,run,[one(subject,run,0,segment,record_id=ident,rpm=4100)]),
    ]
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses=list(pool.map(lambda req: post(subject,req),variants))
    assert sorted(r.status_code for r in responses)==[200,409],[r.text for r in responses]
    data,_=rows(subject,run)
    assert len(data)==1
    assert data[0]["payload"]["values"][0]["value"] in (3100.0,4100.0)
    # Both versions cannot be acknowledged under one immutable ID.
    duplicate=post(subject,batch(subject,run,[data[0]["payload"]]))
    assert duplicate.status_code==200 and duplicate.json()["duplicate_count"]==1


def test_transient_database_outage_yields_no_ack(subject, monkeypatch):
    def disconnected():
        raise psycopg.OperationalError("postgresql://secret-password@private-host")
    monkeypatch.setattr(api.store,"connect",disconnected)
    request=batch(subject,uuid4(),[one(subject,uuid4(),1,uuid4())])
    failure=post(subject,request)
    assert failure.status_code==503,failure.text
    assert failure.json()["error"]["retryable"] is True
    assert "secret-password" not in failure.text
    assert failure.json()["error"]["code"]=="STORAGE_UNAVAILABLE"


def test_stale_status_does_not_overwrite_fresher_state(subject):
    base={
        "protocol_version":1,"device_id":subject["device"],"vehicle_id":subject["vehicle"],
        "agent_version":"synthetic-ci","logger_state":"logging",
        "acquisition":{"last_observed_at":None,"recent_hz":1.0,"drop_count":0},
        "spool":{"unacked_records":0,"pending_bytes":0}
    }
    fresh=dict(base,reported_at="2026-10-13T01:02:00Z")
    stale=dict(base,reported_at="2026-10-13T01:01:00Z",logger_state="error")
    assert subject["client"].post(f"{ROOT}/status",json=fresh,
                                  headers=subject["headers"]).status_code==200
    assert subject["client"].post(f"{ROOT}/status",json=stale,
                                  headers=subject["headers"]).status_code==200
    with store.connect() as db:
        record=db.execute("SELECT state,reported_at FROM v1_device_status WHERE device_id=%s",
                          (subject["device"],)).fetchone()
    assert record["state"]["logger_state"]=="logging"
    assert record["reported_at"].isoformat()=="2026-10-13T01:02:00+00:00"

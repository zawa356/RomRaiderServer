"""PostgreSQL-backed product-v1 contract tests (synthetic fixture only)."""
import hashlib
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from product_v1 import store
from product_v1.api import app


@pytest.fixture(scope="module")
def ctx():
    store.init_schema()
    vehicle_id, device_id = uuid4(), uuid4()
    token = "ci_" + uuid4().hex + uuid4().hex
    with store.connect() as db:
        db.execute("INSERT INTO v1_vehicles(vehicle_id,display_name) VALUES (%s,%s)",
                   (vehicle_id,"synthetic CI vehicle"))
        db.execute("INSERT INTO v1_devices(device_id,vehicle_id,token_sha256) VALUES (%s,%s,%s)",
                   (device_id,vehicle_id,hashlib.sha256(token.encode()).hexdigest()))
    with TestClient(app) as client:
        yield {"client":client,"vehicle_id":str(vehicle_id),"device_id":str(device_id),
               "headers":{"Authorization":"Bearer "+token}}


def profile(ctx, ident=None, unit="rpm"):
    return {"protocol_version":1,"device_id":ctx["device_id"],"vehicle_id":ctx["vehicle_id"],
            "profile_revision_id":str(ident or uuid4()),
            "logger_definition_fingerprint":"ci-synthetic-definition-v1",
            "parameters":[{"parameter_id":"P8","name":"Engine Speed","unit":unit},
                          {"parameter_id":"P13","name":"Throttle","unit":"%"}]}


def observation(profile_id, seq, record_id=None, value=2800.0, segment=None):
    return {"kind":"observation","record_id":str(record_id or uuid4()),
            "segment_id":str(segment or uuid4()),"sequence":seq,
            "captured_at":"2026-10-13T00:00:01.234Z","source_kind":"synthetic",
            "profile_revision_id":str(profile_id),
            "values":[{"parameter_id":"P8","value":value},
                      {"parameter_id":"P13","value":50.0}]}


def batch(ctx, run_id, records):
    return {"protocol_version":1,"batch_id":str(uuid4()),"device_id":ctx["device_id"],
            "vehicle_id":ctx["vehicle_id"],"run_id":str(run_id),"records":records}


def post_batch(ctx, payload):
    return ctx["client"].post("/api/agent/v1/telemetry/batches",json=payload,headers=ctx["headers"])


def register(ctx, p):
    return ctx["client"].put("/api/agent/v1/profile-revisions/"+p["profile_revision_id"],
                             json=p,headers=ctx["headers"])


def test_health_and_device_auth(ctx):
    c=ctx["client"]
    assert c.get("/health").json()["ok"]
    assert c.get("/api/agent/v1/telemetry/recent").status_code == 401
    assert c.get("/api/agent/v1/telemetry/recent",headers={"Authorization":"Bearer invalid"}).status_code==401
    assert c.get("/api/agent/v1/telemetry/recent",headers=ctx["headers"]).status_code==200


def test_profile_duplicate_and_collision(ctx):
    p=profile(ctx)
    assert register(ctx,p).status_code == 201
    replay=register(ctx,p)
    assert replay.status_code == 200 and replay.json()["status"]=="already_registered"
    different=profile(ctx,ident=p["profile_revision_id"],unit="rpm2")
    r=register(ctx,different)
    assert r.status_code == 409, r.text
    assert r.json()["error"]["code"]=="PROFILE_REVISION_CONFLICT"
    wrong=dict(p,device_id=str(uuid4()))
    assert register(ctx,wrong).status_code==403


def test_atomic_commit_ack_replay_and_conflicts(ctx):
    p=profile(ctx); assert register(ctx,p).status_code==201
    run,segment=uuid4(),uuid4()
    a=observation(p["profile_revision_id"],0,segment=segment)
    b=observation(str(uuid4()),1,segment=segment)
    req=batch(ctx,run,[a,b])
    failed=post_batch(ctx,req)
    assert failed.status_code==422,failed.text
    assert failed.json()["error"]["code"]=="UNKNOWN_PROFILE_REVISION"
    assert ctx["client"].get("/api/agent/v1/telemetry/recent",
                             headers=ctx["headers"]).json()["returned"]==0
    req["records"]=[a]
    ok=post_batch(ctx,req)
    assert ok.status_code==200,ok.text
    assert ok.json()["status"]=="committed"
    assert ok.json()["inserted_count"]==1
    assert ok.json()["record_count"]==1
    dup=post_batch(ctx,req)
    assert dup.status_code==200
    assert dup.json()["inserted_count"]==0 and dup.json()["duplicate_count"]==1
    changed=batch(ctx,run,[dict(a,values=[{"parameter_id":"P8","value":999.0}])])
    assert post_batch(ctx,changed).status_code==409
    seq_clash=batch(ctx,run,[observation(p["profile_revision_id"],0,segment=segment)])
    assert post_batch(ctx,seq_clash).status_code==409
    latest=ctx["client"].get("/api/agent/v1/telemetry/recent",
                              headers=ctx["headers"]).json()
    assert latest["returned"]==1 and latest["rows"][0]["values"][0]["value"]==2800.0


def test_profile_and_parameter_validation(ctx):
    p=profile(ctx);assert register(ctx,p).status_code==201
    run=uuid4()
    duplicate_params=observation(p["profile_revision_id"],1)
    duplicate_params["values"].append(dict(duplicate_params["values"][0]))
    assert post_batch(ctx,batch(ctx,run,[duplicate_params])).status_code==422
    invalid=observation(p["profile_revision_id"],1)
    invalid["values"][0]["parameter_id"]="NOT_DEFINED"
    assert post_batch(ctx,batch(ctx,run,[invalid])).status_code==422
    bool_value=observation(p["profile_revision_id"],1)
    bool_value["values"][0]["value"]=True
    assert post_batch(ctx,batch(ctx,run,[bool_value])).status_code==422
    bad_time=observation(p["profile_revision_id"],1)
    bad_time["captured_at"]="2026-10-13T00:00:01"
    assert post_batch(ctx,batch(ctx,run,[bad_time])).status_code==422


def test_event_gap_and_synthetic_source(ctx):
    run=uuid4()
    event={"kind":"event","record_id":str(uuid4()),
           "captured_at":"2026-10-13T00:00:02Z","source_kind":"agent",
           "event_type":"logging_start","data":{"reason":"synthetic-ci"}}
    gap={"kind":"gap","record_id":str(uuid4()),
         "captured_at":"2026-10-13T00:00:03Z","source_kind":"agent",
         "event_type":"writer_backpressure","data":{"dropped":2}}
    result=post_batch(ctx,batch(ctx,run,[event,gap]))
    assert result.status_code==200,result.text
    assert result.json()["inserted_count"]==2
    assert post_batch(ctx,batch(ctx,run,[event,gap])).json()["duplicate_count"]==2


def test_batch_atomic_after_one_record_collision(ctx):
    p=profile(ctx);register(ctx,p)
    run,segment=uuid4(),uuid4()
    initial=observation(p["profile_revision_id"],1,segment=segment)
    assert post_batch(ctx,batch(ctx,run,[initial])).status_code==200
    candidate=observation(p["profile_revision_id"],2,segment=segment)
    conflict=dict(initial,values=[{"parameter_id":"P8","value":1234.0}])
    before=ctx["client"].get("/api/agent/v1/telemetry/recent",headers=ctx["headers"]).json()["returned"]
    bad=post_batch(ctx,batch(ctx,run,[candidate,conflict]))
    assert bad.status_code==409
    after=ctx["client"].get("/api/agent/v1/telemetry/recent",headers=ctx["headers"]).json()["returned"]
    assert after==before, "A valid record from a rejected batch MUST be rolled back"
    assert post_batch(ctx,batch(ctx,run,[candidate])).status_code==200


def test_device_scope_and_status(ctx):
    p=profile(ctx)
    p["vehicle_id"]=str(uuid4())
    assert register(ctx,p).status_code==403
    status={"protocol_version":1,"device_id":ctx["device_id"],"vehicle_id":ctx["vehicle_id"],
            "reported_at":"2026-10-13T00:00:10Z","agent_version":"test-agent",
            "logger_state":"logging",
            "acquisition":{"last_observed_at":"2026-10-13T00:00:09Z","recent_hz":5.0,
                           "drop_count":0},
            "spool":{"unacked_records":0,"pending_bytes":0}}
    got=ctx["client"].post("/api/agent/v1/status",json=status,headers=ctx["headers"])
    assert got.status_code==200,got.text
    assert got.json()["status"]=="recorded"

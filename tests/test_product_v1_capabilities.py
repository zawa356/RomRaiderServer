"""Product v1 capability snapshot contract tests using disposable PostgreSQL."""
import hashlib
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from product_v1 import store
from product_v1.api import app


@pytest.fixture
def ctx():
    store.require_schema()
    vehicle, device = uuid4(), uuid4()
    token="ci_caps_"+uuid4().hex
    with store.connect() as db:
        db.execute("INSERT INTO v1_vehicles(vehicle_id,display_name) VALUES (%s,%s)",
                   (vehicle,"synthetic capability CI vehicle"))
        db.execute("""INSERT INTO v1_devices(device_id,vehicle_id,token_sha256)
            VALUES (%s,%s,%s)""",(device,vehicle,hashlib.sha256(token.encode()).hexdigest()))
    with TestClient(app) as client:
        yield {"vehicle_id":str(vehicle),"device_id":str(device),
               "client":client,"headers":{"Authorization":"Bearer "+token}}


def example(ctx):
    return {
        "protocol_version":1,
        "device_id":ctx["device_id"],
        "vehicle_id":ctx["vehicle_id"],
        "logger_version":"synthetic-test-logger",
        "definition_fingerprint":"synthetic-logger-xml-sha256",
        "ecu_identity":"synthetic-ecu",
        "observed_at":"2026-10-13T00:00:00Z",
        "parameters":[
            {"parameter_id":"P8","name":"Engine speed","unit":"rpm",
             "availability":"verified_readable","evidence":"synthetic fixture only"},
            {"parameter_id":"P9","name":"Vehicle speed","unit":"km/h",
             "availability":"unknown","evidence":"not checked"},
        ],
    }


def put(ctx, ident, body, headers=None):
    return ctx["client"].put("/api/agent/v1/capability-snapshots/"+str(ident),
                             json=body,headers=headers if headers is not None else ctx["headers"])


def test_immutable_capability_snapshot_and_parameter_index(ctx):
    ident=uuid4()
    request=example(ctx)
    first=put(ctx,ident,request)
    assert first.status_code==201,first.text
    assert first.json()["status"]=="registered"
    second=put(ctx,ident,request)
    assert second.status_code==200 and second.json()["status"]=="already_registered"
    with store.connect() as db:
        stored=db.execute("""SELECT payload,definition_fingerprint FROM v1_capability_snapshots
                             WHERE snapshot_id=%s""",(ident,)).fetchone()
        params=db.execute("""SELECT parameter_id,availability,unit FROM v1_capability_parameters
                             WHERE snapshot_id=%s ORDER BY parameter_id""",(ident,)).fetchall()
    assert stored["definition_fingerprint"]==request["definition_fingerprint"]
    assert len(params)==2
    assert params[0]["availability"]=="verified_readable"
    assert params[1]["availability"]=="unknown"
    assert stored["payload"]["ecu_identity"]=="synthetic-ecu"
    changed=example(ctx)
    changed["parameters"][1]["availability"]="verified_readable"
    conflict=put(ctx,ident,changed)
    assert conflict.status_code==409
    assert conflict.json()["error"]["code"]=="CAPABILITY_SNAPSHOT_CONFLICT"
    with store.connect() as db:
        existing=db.execute("""SELECT availability FROM v1_capability_parameters
                               WHERE snapshot_id=%s AND parameter_id='P9'""",(ident,)).fetchone()
    assert existing["availability"]=="unknown", "Existing capability must remain immutable"


def test_capability_auth_and_duplicate_parameter_fail_closed(ctx):
    ident=uuid4()
    request=example(ctx)
    assert put(ctx,ident,request,headers={}).status_code==401
    wrong=example(ctx)
    wrong["vehicle_id"]=str(uuid4())
    assert put(ctx,ident,wrong).status_code==403
    duplicate=example(ctx)
    duplicate["parameters"].append(dict(duplicate["parameters"][0]))
    x=put(ctx,ident,duplicate)
    assert x.status_code==422
    assert x.json()["error"]["code"]=="DUPLICATE_PARAMETER"
    with store.connect() as db:
        assert db.execute("SELECT count(*) AS n FROM v1_capability_snapshots WHERE snapshot_id=%s",
                          (ident,)).fetchone()["n"]==0


def test_capability_validation_rejects_unknown_flags_and_naive_timestamps(ctx):
    bad=example(ctx)
    bad["parameters"][0]["availability"]="this-is-not-an-availability-state"
    assert put(ctx,uuid4(),bad).status_code==422
    bad=example(ctx)
    bad["observed_at"]="2026-10-13T00:00:00"
    assert put(ctx,uuid4(),bad).status_code==422
    empty=example(ctx)
    empty["parameters"]=[]
    assert put(ctx,uuid4(),empty).status_code==201

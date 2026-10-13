"""Phase 1.1-D Server command transport: synthetic-only, no ECU calls."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import hashlib
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from product_v1 import store
from product_v1.api import app

URL = "/api/agent/v1"
UTC = timezone.utc


@pytest.fixture
def env(monkeypatch):
    store.require_schema()
    vehicle, device, task, plan, approval, command = [uuid4() for _ in range(6)]
    token = "synthetic_command_test_" + uuid4().hex
    now = datetime.now(UTC)
    with store.connect() as db:
        db.execute("INSERT INTO v1_vehicles(vehicle_id,display_name) VALUES (%s,%s)",
                   (vehicle, "synthetic command contract"))
        db.execute("""INSERT INTO v1_devices(device_id,vehicle_id,token_sha256)
          VALUES (%s,%s,%s)""",
          (device,vehicle,hashlib.sha256(token.encode()).hexdigest()))
        db.execute("""INSERT INTO v1_tasks(task_id,vehicle_id,state)
          VALUES (%s,%s,'active')""",(task,vehicle))
        db.execute("""INSERT INTO v1_plan_revisions(plan_revision_id,task_id,revision_number)
          VALUES (%s,%s,1)""",(plan,task))
        db.execute("""INSERT INTO v1_approval_scopes
          (approval_scope_id,task_id,vehicle_id,approved_by,allowed_actions,starts_at,expires_at)
          VALUES (%s,%s,%s,%s,%s,%s,%s)""",
          (approval,task,vehicle,"synthetic fixture",["suspend_ai_changes"],
           now-timedelta(minutes=1),now+timedelta(minutes=10)))
        db.execute("""INSERT INTO v1_command_requests
          (command_id,vehicle_id,device_id,task_id,plan_revision_id,approval_scope_id,
           action,issued_at,expires_at)
          VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
          (command,vehicle,device,task,plan,approval,"suspend_ai_changes",
           now-timedelta(seconds=5),now+timedelta(minutes=2)))
    with TestClient(app) as client:
        yield {"client":client,"device":str(device),"vehicle":str(vehicle),
               "task":str(task),"plan":str(plan),"approval":str(approval),
               "command":str(command),"token":token,
               "headers":{"Authorization":"Bearer "+token},
               "monkeypatch":monkeypatch}


def reconcile(env, revision="ci-rev-1", **overrides):
    req={"protocol_version":1,"device_id":env["device"],"vehicle_id":env["vehicle"],
         "reported_at":datetime.now(UTC).isoformat(),
         "client_state_revision":revision}
    req.update(overrides)
    return env["client"].post(URL+"/reconcile",json=req,headers=env["headers"])


def claim(env, **overrides):
    req={"protocol_version":1,"device_id":env["device"],"vehicle_id":env["vehicle"],
         "current_plan_revision_id":env["plan"],"client_state_revision":"ci-rev-1"}
    req.update(overrides)
    return env["client"].post(URL+"/commands/claim",json=req,headers=env["headers"])


def report(env, state, report_id=None, **overrides):
    req={"protocol_version":1,"device_id":env["device"],"vehicle_id":env["vehicle"],
         "command_id":env["command"],"report_id":str(report_id or uuid4()),
         "state":state,"reported_at":datetime.now(UTC).isoformat()}
    req.update(overrides)
    return env["client"].post(URL+"/commands/"+env["command"]+"/report",
                              json=req,headers=env["headers"])


def test_claim_disabled_by_default_and_requires_reconciliation(env):
    assert claim(env).json()=={"status":"none","command":None}
    env["monkeypatch"].setenv("ROMLOGGER_ENABLE_COMMAND_CLAIM","true")
    # No latest client state/reconciliation -> never deliver.
    assert claim(env).json()["status"]=="none"
    assert reconcile(env).json()["status"]=="aligned"
    assert claim(env,client_state_revision="stale").json()["status"]=="none"
    assert claim(env,current_plan_revision_id=str(uuid4())).json()["status"]=="none"
    got=claim(env)
    assert got.status_code==200,got.text
    assert got.json()["status"]=="leased"
    assert got.json()["command"]["command_id"]==env["command"]
    assert got.json()["command"]["action"]=="suspend_ai_changes"
    assert got.json()["command"]["approval_scope_id"]==env["approval"]
    # Same lease must NOT become a new operation ID.
    assert claim(env).json()["command"]["command_id"]==env["command"]
    assert reconcile(env,revision="ci-rev-2").json()["status"]=="action_required"


def test_reports_have_unique_id_monotonic_transitions_and_audit(env):
    env["monkeypatch"].setenv("ROMLOGGER_ENABLE_COMMAND_CLAIM","true")
    assert reconcile(env).status_code==200
    assert claim(env).json()["status"]=="leased"
    assert report(env,"verified").status_code==409  # no false positive without evidence
    first_id=uuid4()
    first=report(env,"received",report_id=first_id)
    assert first.status_code==200,first.text
    assert first.json()["status"]=="recorded"
    retry=report(env,"received",report_id=first_id,
                 reported_at=None)
    # The payload differs when the timestamp changes or is invalid.
    assert retry.status_code==422
    for state in ("applying","applied_unverified","verified"):
        result=report(env,state)
        assert result.status_code==200,result.text
    assert report(env,"applying").status_code==409
    with store.connect() as db:
        row=db.execute("SELECT status FROM v1_command_requests WHERE command_id=%s",
                       (env["command"],)).fetchone()
        count=db.execute("SELECT count(*) AS n FROM v1_command_reports WHERE command_id=%s",
                         (env["command"],)).fetchone()["n"]
    assert row["status"]=="verified"
    assert count==4
    assert claim(env).json()["status"]=="none"


def test_report_id_idempotence_and_collision(env):
    env["monkeypatch"].setenv("ROMLOGGER_ENABLE_COMMAND_CLAIM","true")
    reconcile(env)
    claim(env)
    timestamp=datetime.now(UTC).isoformat()
    rid=uuid4()
    first=report(env,"received",report_id=rid,reported_at=timestamp)
    assert first.status_code==200,first.text
    repeat=report(env,"received",report_id=rid,reported_at=timestamp)
    assert repeat.status_code==200 and repeat.json()["status"]=="already_recorded"
    altered=report(env,"failed",report_id=rid,reported_at=timestamp)
    assert altered.status_code==409 and altered.json()["error"]["code"]=="REPORT_ID_CONFLICT"
    with store.connect() as db:
        assert db.execute("SELECT status FROM v1_command_requests WHERE command_id=%s",
                          (env["command"],)).fetchone()["status"]=="received"


def test_expired_leases_go_to_unknown_not_queued_and_do_not_redeliver(env):
    env["monkeypatch"].setenv("ROMLOGGER_ENABLE_COMMAND_CLAIM","true")
    reconcile(env)
    assert claim(env).json()["status"]=="leased"
    with store.connect() as db:
        db.execute("""UPDATE v1_command_requests SET lease_until=now()-interval '1 second'
          WHERE command_id=%s""",(env["command"],))
    assert claim(env).json()["status"]=="none"
    assert claim(env).json()["status"]=="none"
    with store.connect() as db:
        assert db.execute("SELECT status FROM v1_command_requests WHERE command_id=%s",
                          (env["command"],)).fetchone()["status"]=="unknown"
    assert reconcile(env,revision="ci-new").json()["status"]=="action_required"
    # Late, authoritative device reports may resolve unknown execution.
    assert report(env,"failed").status_code==200


def test_expired_approval_and_outdated_plan_never_claimed(env):
    env["monkeypatch"].setenv("ROMLOGGER_ENABLE_COMMAND_CLAIM","true")
    reconcile(env)
    with store.connect() as db:
        db.execute("""UPDATE v1_approval_scopes SET revoked_at=now()
           WHERE approval_scope_id=%s""",(env["approval"],))
    assert claim(env).json()["status"]=="none"
    with store.connect() as db:
        db.execute("""UPDATE v1_approval_scopes SET revoked_at=NULL
           WHERE approval_scope_id=%s""",(env["approval"],))
        db.execute("""INSERT INTO v1_plan_revisions
          (plan_revision_id,task_id,revision_number)
          VALUES (%s,%s,2)""",(uuid4(),env["task"]))
    assert claim(env).json()["status"]=="none"


def test_wrong_scope_and_unknown_commands_are_not_disclosed(env):
    env["monkeypatch"].setenv("ROMLOGGER_ENABLE_COMMAND_CLAIM","true")
    assert reconcile(env,vehicle_id=str(uuid4())).status_code==403
    assert claim(env,device_id=str(uuid4())).status_code==403
    unknown=report(env,"received",command_id=str(uuid4()))
    assert unknown.status_code==422
    foreign=env["client"].post(URL+"/commands/"+str(uuid4())+"/report",
        json={"protocol_version":1,"device_id":env["device"],"vehicle_id":env["vehicle"],
              "command_id":str(uuid4()),"report_id":str(uuid4()),
              "state":"received","reported_at":datetime.now(UTC).isoformat()},
        headers=env["headers"])
    assert foreign.status_code==422
    assert reconcile(env,last_command_id=str(uuid4())).json()["status"]=="unknown"
    assert env["client"].post(URL+"/commands/claim",json={}).status_code==401


def test_reconciliation_revision_conflicts_are_detected(env):
    first=reconcile(env,revision="rev-stable")
    assert first.status_code==200
    second=reconcile(env,revision="rev-stable",last_command_id=str(uuid4()))
    assert second.status_code==409
    assert second.json()["error"]["code"]=="CLIENT_STATE_REVISION_CONFLICT"


def test_parallel_claims_share_one_command_id(env):
    env["monkeypatch"].setenv("ROMLOGGER_ENABLE_COMMAND_CLAIM","true")
    reconcile(env)
    with ThreadPoolExecutor(max_workers=2) as executor:
        futures=[executor.submit(claim,env) for _ in range(2)]
    responses=[future.result() for future in futures]
    assert all(r.status_code==200 for r in responses)
    assert {r.json()["command"]["command_id"] for r in responses}=={env["command"]}
    with store.connect() as db:
        assert db.execute("""SELECT status FROM v1_command_requests
            WHERE command_id=%s""",(env["command"],)).fetchone()["status"]=="leased"


def test_revoked_lease_never_returned_again(env):
    env["monkeypatch"].setenv("ROMLOGGER_ENABLE_COMMAND_CLAIM","true")
    reconcile(env)
    assert claim(env).json()["status"]=="leased"
    with store.connect() as db:
        db.execute("UPDATE v1_approval_scopes SET revoked_at=now() WHERE approval_scope_id=%s",
                   (env["approval"],))
    assert claim(env).json()["status"]=="none"
    with store.connect() as db:
        assert db.execute("SELECT status FROM v1_command_requests WHERE command_id=%s",
                          (env["command"],)).fetchone()["status"]=="unknown"
    assert reconcile(env,revision="rev-revoked").json()["status"]=="action_required"


def test_unapproved_action_is_not_delivered(env):
    env["monkeypatch"].setenv("ROMLOGGER_ENABLE_COMMAND_CLAIM","true")
    reconcile(env)
    with store.connect() as db:
        db.execute("""UPDATE v1_command_requests
            SET action='apply_measurement_plan' WHERE command_id=%s""",
                   (env["command"],))
        db.execute("""UPDATE v1_approval_scopes
            SET allowed_actions=ARRAY['apply_measurement_plan']::text[]
            WHERE approval_scope_id=%s""",(env["approval"],))
    # Even an approved plan cannot bypass the dedicated on-car safety phase.
    assert claim(env).json()["status"]=="none"

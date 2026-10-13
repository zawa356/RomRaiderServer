"""Product v1 command transport.

Transport only: no public command-creation endpoint and NO ECU side effects.
Delivery remains disabled unless explicitly enabled. Plan application stays blocked
until a separate tested safety and approval implementation exists.
"""
import os
from datetime import datetime, timezone, timedelta
from uuid import UUID

from psycopg.types.json import Jsonb

from . import store


# First implementation intentionally restricts delivery to a non-actuating
# control. This is NOT permission for an Agent to skip its independent checks.
DELIVERABLE_ACTIONS = ("suspend_ai_changes",)
TERMINAL = {"rejected", "verified", "failed", "expired", "cancelled"}
TRANSITIONS = {
    "leased": {"received", "rejected", "failed", "expired", "cancelled", "unknown"},
    "received": {"applying", "rejected", "failed", "expired", "cancelled", "unknown"},
    "applying": {"applied_unverified", "failed", "unknown"},
    "applied_unverified": {"verified", "failed", "unknown"},
    # An actual late Agent report can resolve uncertain execution. Server must
    # never interpret lease expiry as proof the operation did not run.
    "unknown": {"received", "applying", "applied_unverified", "verified",
                "failed", "rejected", "cancelled"},
}


def _check_scope(device, body):
    if (body["device_id"] != str(device["device_id"]) or
            body["vehicle_id"] != str(device["vehicle_id"])):
        raise store.DomainError(403, "DEVICE_SCOPE", "Device or vehicle mismatch")


def _lease_payload(row):
    return {
        "command_id": str(row["command_id"]),
        "action": row["action"],
        "task_id": str(row["task_id"]),
        "plan_revision_id": str(row["plan_revision_id"]),
        "approval_scope_id": str(row["approval_scope_id"]),
        "issued_at": row["issued_at"].isoformat(),
        "expires_at": row["expires_at"].isoformat(),
        "expected_profile_revision_id": (
            str(row["expected_profile_revision_id"])
            if row["expected_profile_revision_id"] is not None else None
        ),
        "lease_until": row["lease_until"].isoformat(),
    }


def _none():
    return {"status": "none", "command": None}


def claim(device, body):
    """Device-initiated pull, with no autonomous replay of timed-out leases."""
    _check_scope(device, body)
    if os.environ.get("ROMLOGGER_ENABLE_COMMAND_CLAIM") != "true":
        return _none()
    with store.connect() as db:
        # A shared per-vehicle row lock serializes multiple claim workers.
        db.execute("SELECT vehicle_id FROM v1_vehicles WHERE vehicle_id=%s FOR UPDATE",
                   (device["vehicle_id"],))
        last = db.execute("""
            SELECT client_state_revision FROM v1_reconciliations
            WHERE device_id=%s ORDER BY reconcile_id DESC LIMIT 1
        """, (device["device_id"],)).fetchone()
        if not last or last["client_state_revision"] != body["client_state_revision"]:
            return _none()
        # Never assume that an expired delivery lease means execution did not occur.
        db.execute("""
            UPDATE v1_command_requests SET status='unknown',updated_at=now()
            WHERE device_id=%s AND status='leased' AND lease_until<=now()
        """, (device["device_id"],))
        outstanding = db.execute("""
            SELECT * FROM v1_command_requests WHERE device_id=%s
              AND status='leased' AND lease_until>now()
            ORDER BY issued_at,command_id LIMIT 1 FOR UPDATE
        """, (device["device_id"],)).fetchone()
        if outstanding:
            # Re-claim returns the same ID, but the Agent must use its local
            # execution journal and MUST NOT interpret this as a new operation.
            return {"status":"leased","command":_lease_payload(outstanding)}
        unresolved = db.execute("""
            SELECT 1 FROM v1_command_requests
            WHERE device_id=%s AND status IN
              ('received','applying','applied_unverified','unknown') LIMIT 1
        """, (device["device_id"],)).fetchone()
        if unresolved:
            return _none()
        # Fail closed if there is no CURRENT, explicitly approved active task.
        row = db.execute("""
            SELECT c.* FROM v1_command_requests c
            JOIN v1_tasks t ON t.task_id=c.task_id
            JOIN v1_plan_revisions p ON p.plan_revision_id=c.plan_revision_id
            JOIN v1_approval_scopes a ON a.approval_scope_id=c.approval_scope_id
            JOIN v1_devices d ON d.device_id=c.device_id
            WHERE c.device_id=%s AND c.vehicle_id=%s AND c.status='queued'
              AND c.issued_at<=now() AND c.expires_at>now()
              AND c.action=ANY(%s)
              AND t.vehicle_id=c.vehicle_id AND t.state='active'
              AND p.task_id=c.task_id AND a.task_id=c.task_id
              AND a.vehicle_id=c.vehicle_id AND a.revoked_at IS NULL
              AND a.starts_at<=now() AND a.expires_at>now()
              AND c.action=ANY(a.allowed_actions)
              AND d.vehicle_id=c.vehicle_id AND d.revoked_at IS NULL
              AND NOT EXISTS (
                SELECT 1 FROM v1_plan_revisions newer
                WHERE newer.task_id=c.task_id
                  AND newer.revision_number>p.revision_number
              )
              AND c.plan_revision_id=%s
            ORDER BY c.issued_at,c.command_id LIMIT 1 FOR UPDATE OF c
        """, (device["device_id"],device["vehicle_id"],
              list(DELIVERABLE_ACTIONS),body.get("current_plan_revision_id"))).fetchone()
        if not row:
            return _none()
        lease = db.execute("""
            UPDATE v1_command_requests SET status='leased',
                lease_until=LEAST(expires_at, now() + interval '30 seconds'),
                updated_at=now()
            WHERE command_id=%s RETURNING *
        """, (row["command_id"],)).fetchone()
        return {"status":"leased","command":_lease_payload(lease)}


def report(device, command_id, body):
    """Append-only report ID; checks monotonic transition before updating state."""
    _check_scope(device, body)
    if str(command_id) != body["command_id"]:
        raise store.DomainError(422, "COMMAND_ID_MISMATCH", "Path and body IDs differ")
    signature = store.digest(body)
    with store.connect() as db:
        db.execute("SELECT vehicle_id FROM v1_vehicles WHERE vehicle_id=%s FOR UPDATE",
                   (device["vehicle_id"],))
        old = db.execute("""
            SELECT command_id,device_id,content_hash
            FROM v1_command_reports WHERE report_id=%s
        """, (body["report_id"],)).fetchone()
        if old:
            if (old["command_id"] != UUID(body["command_id"]) or
                    old["device_id"] != device["device_id"] or
                    old["content_hash"] != signature):
                raise store.DomainError(409, "REPORT_ID_CONFLICT",
                                        "Report ID already used with different content")
            return {"status":"already_recorded"}
        command = db.execute("""
            SELECT * FROM v1_command_requests WHERE command_id=%s
            FOR UPDATE
        """, (command_id,)).fetchone()
        if command is None or command["device_id"] != device["device_id"] or (
                command["vehicle_id"] != device["vehicle_id"]):
            raise store.DomainError(404, "COMMAND_NOT_FOUND", "Command not found for device")
        current = command["status"]
        requested = body["state"]
        if requested != current and requested not in TRANSITIONS.get(current, set()):
            raise store.DomainError(409, "COMMAND_STATE_CONFLICT",
                                    "Illegal command state transition")
        # Repeated semantic states with a NEW report ID are still audit records,
        # but terminal state must never regress.
        db.execute("""
            INSERT INTO v1_command_reports
              (report_id,command_id,device_id,state,reported_at,content_hash,payload)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """,(body["report_id"],command_id,device["device_id"],requested,
             body["reported_at"],signature,Jsonb(body)))
        if requested != current:
            db.execute("""
                UPDATE v1_command_requests SET status=%s,updated_at=now()
                WHERE command_id=%s
            """, (requested,command_id))
    return {"status":"recorded"}


def reconcile(device, body):
    """Audit the Agent's reported state. Never replay or perform any command."""
    _check_scope(device, body)
    signature = store.digest(body)
    with store.connect() as db:
        db.execute("SELECT vehicle_id FROM v1_vehicles WHERE vehicle_id=%s FOR UPDATE",
                   (device["vehicle_id"],))
        prior = db.execute("""
            SELECT content_hash FROM v1_reconciliations
            WHERE device_id=%s AND client_state_revision=%s
        """,(device["device_id"],body["client_state_revision"])).fetchone()
        if prior and prior["content_hash"] != signature:
            raise store.DomainError(409, "CLIENT_STATE_REVISION_CONFLICT",
                                    "Same client revision has different content")
        if not prior:
            db.execute("""
                INSERT INTO v1_reconciliations
                 (device_id,vehicle_id,client_state_revision,reported_at,content_hash,payload)
                VALUES (%s,%s,%s,%s,%s,%s)
            """,(device["device_id"],device["vehicle_id"],body["client_state_revision"],
                 body["reported_at"],signature,Jsonb(body)))
        # The most recent active plan is informational. Reconcile does not
        # authorize a plan change or emit commands.
        plan = db.execute("""
            SELECT p.plan_revision_id FROM v1_tasks t
            JOIN v1_plan_revisions p ON p.task_id=t.task_id
            WHERE t.vehicle_id=%s AND t.state='active'
            ORDER BY p.revision_number DESC LIMIT 1
        """,(device["vehicle_id"],)).fetchone()
        expected = str(plan["plan_revision_id"]) if plan else None
        local_command = body.get("last_command_id")
        if local_command is not None:
            known = db.execute("""
                SELECT status FROM v1_command_requests
                WHERE command_id=%s AND device_id=%s
            """,(local_command,device["device_id"])).fetchone()
            if not known:
                return {"status":"unknown","server_expected_plan_revision_id":expected,
                        "reason":"last_command_not_known"}
        unresolved = db.execute("""
            SELECT 1 FROM v1_command_requests WHERE device_id=%s
            AND status IN ('leased','received','applying','applied_unverified','unknown')
            LIMIT 1
        """,(device["device_id"],)).fetchone()
        if unresolved:
            return {"status":"action_required","server_expected_plan_revision_id":expected,
                    "reason":"execution_not_confirmed_no_automatic_replay"}
        if body.get("local_execution_records"):
            # Local execution details require Supervisor adjudication in a
            # later phase. Never interpret arbitrary client claims as verified.
            return {"status":"action_required","server_expected_plan_revision_id":expected,
                    "reason":"local_execution_review_required"}
        return {"status":"aligned","server_expected_plan_revision_id":expected,
                "reason":"no_outstanding_execution"}

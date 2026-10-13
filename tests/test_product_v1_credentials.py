"""Local-only credential lifecycle integration tests against real PostgreSQL."""
import hashlib
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from product_v1 import credentials, store
from product_v1.api import app


def test_rotate_and_revoke_device_without_affecting_other_devices():
    store.require_schema()
    vehicle, device_a, device_b = uuid4(), uuid4(), uuid4()
    old_token = "ci_initial_" + uuid4().hex
    other_token = "ci_other_" + uuid4().hex
    with store.connect() as db:
        db.execute("INSERT INTO v1_vehicles(vehicle_id,display_name) VALUES (%s,%s)",
                   (vehicle, "credential CI synthetic vehicle"))
        for ident, token in ((device_a,old_token), (device_b,other_token)):
            db.execute("""INSERT INTO v1_devices(device_id,vehicle_id,token_sha256)
                VALUES (%s,%s,%s)""",
                (ident,vehicle,hashlib.sha256(token.encode()).hexdigest()))

    def api_status(client, token):
        return client.get("/api/agent/v1/telemetry/recent",
                          headers={"Authorization": "Bearer " + token}).status_code

    with TestClient(app) as client:
        assert api_status(client, old_token)==200
        assert api_status(client, other_token)==200
        rotated = credentials.rotate_device(device_a)
        new_token = rotated["device_token"]
        assert rotated["device_id"]==str(device_a)
        assert new_token != old_token
        assert api_status(client, old_token)==401
        assert api_status(client, new_token)==200
        assert api_status(client, other_token)==200
        with store.connect() as db:
            stored = db.execute("SELECT token_sha256 FROM v1_devices WHERE device_id=%s",
                                (device_a,)).fetchone()["token_sha256"]
        assert stored==hashlib.sha256(new_token.encode()).hexdigest()
        assert new_token not in stored

        before=credentials.device_status(device_a)
        assert before["state"]=="active"
        revoked=credentials.revoke_device(device_a)
        assert revoked["state"]=="revoked" and revoked["newly_revoked"] is True
        assert api_status(client, new_token)==401
        again=credentials.revoke_device(device_a)
        assert again["newly_revoked"] is False
        assert again["revoked_at"]==revoked["revoked_at"]
        assert api_status(client, other_token)==200
        with pytest.raises(credentials.RevokedDevice):
            credentials.rotate_device(device_a)


def test_unknown_device_fails_without_side_effects():
    unknown=uuid4()
    with pytest.raises(credentials.UnknownDevice):
        credentials.rotate_device(unknown)
    with pytest.raises(credentials.UnknownDevice):
        credentials.revoke_device(unknown)
    with pytest.raises(credentials.UnknownDevice):
        credentials.device_status(unknown)

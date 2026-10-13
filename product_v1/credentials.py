"""Offline/local administrative credential rotation and revocation for product v1.

NOT an API/MCP endpoint. The operator must already have database administration
credentials; plaintext device secrets are never stored on the server.
"""
import argparse
import hashlib
import json
import secrets
from uuid import UUID

from . import store


class UnknownDevice(ValueError):
    pass


class RevokedDevice(ValueError):
    pass


def rotate_device(device_id: UUID) -> dict:
    """Atomically invalidate the previous token and print the replacement once."""
    token = secrets.token_urlsafe(48)
    fingerprint = hashlib.sha256(token.encode("utf-8")).hexdigest()
    with store.connect() as db:
        row = db.execute("""
            UPDATE v1_devices SET token_sha256=%s
            WHERE device_id=%s AND revoked_at IS NULL
            RETURNING device_id,vehicle_id
        """, (fingerprint, device_id)).fetchone()
        if not row:
            known = db.execute(
                "SELECT revoked_at FROM v1_devices WHERE device_id=%s",
                (device_id,)
            ).fetchone()
            if known:
                raise RevokedDevice("Revoked device cannot receive new credentials")
            raise UnknownDevice("Unknown device_id")
    return {
        "device_id": str(row["device_id"]),
        "vehicle_id": str(row["vehicle_id"]),
        "device_token": token,
        "warning": "Old token invalid immediately. Securely store this one-time token.",
    }


def revoke_device(device_id: UUID) -> dict:
    """Revocation is permanent in v1. Repeat calls are idempotent."""
    with store.connect() as db:
        row = db.execute("""
            UPDATE v1_devices SET revoked_at=now()
            WHERE device_id=%s AND revoked_at IS NULL
            RETURNING device_id,vehicle_id,revoked_at
        """, (device_id,)).fetchone()
        changed = bool(row)
        if not row:
            row = db.execute("""
                SELECT device_id,vehicle_id,revoked_at
                FROM v1_devices WHERE device_id=%s
            """, (device_id,)).fetchone()
        if not row:
            raise UnknownDevice("Unknown device_id")
    return {
        "device_id": str(row["device_id"]),
        "vehicle_id": str(row["vehicle_id"]),
        "state": "revoked",
        "newly_revoked": changed,
        "revoked_at": row["revoked_at"].isoformat(),
    }


def device_status(device_id: UUID) -> dict:
    with store.connect() as db:
        row = db.execute("""
            SELECT device_id,vehicle_id,revoked_at FROM v1_devices
            WHERE device_id=%s
        """, (device_id,)).fetchone()
    if not row:
        raise UnknownDevice("Unknown device_id")
    return {
        "device_id": str(row["device_id"]),
        "vehicle_id": str(row["vehicle_id"]),
        "state": "revoked" if row["revoked_at"] else "active",
        "revoked_at": row["revoked_at"].isoformat() if row["revoked_at"] else None,
    }


def main():
    parser = argparse.ArgumentParser(description="RomLogger v1 device credentials (local admin only)")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("rotate", "revoke", "status"):
        p = sub.add_parser(name)
        p.add_argument("--device-id", type=UUID, required=True)
    args = parser.parse_args()
    store.require_schema()
    try:
        result = {
            "rotate": rotate_device,
            "revoke": revoke_device,
            "status": device_status,
        }[args.command](args.device_id)
    except (UnknownDevice, RevokedDevice) as exc:
        parser.exit(2, f"ERROR: {exc}\n")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

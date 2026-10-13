"""Provision a per-device product-v1 token without touching the PoC database."""
import argparse
import hashlib
import json
import secrets
from uuid import uuid4, UUID

from . import store


def main():
    parser = argparse.ArgumentParser(description="Register a RomLogger v1 test vehicle and device")
    parser.add_argument("--vehicle-id", type=UUID, help="Existing vehicle id (otherwise new)")
    parser.add_argument("--display-name", default="RomLogger test vehicle")
    args = parser.parse_args()
    store.require_schema()
    vehicle_id = args.vehicle_id or uuid4()
    device_id = uuid4()
    # Never save the plaintext device secret to PostgreSQL.
    token = secrets.token_urlsafe(40)
    with store.connect() as db:
        db.execute("""INSERT INTO v1_vehicles(vehicle_id,display_name) VALUES (%s,%s)
            ON CONFLICT DO NOTHING""",(vehicle_id,args.display_name))
        db.execute("""INSERT INTO v1_devices(device_id,vehicle_id,token_sha256)
            VALUES (%s,%s,%s)""",(device_id,vehicle_id,hashlib.sha256(token.encode()).hexdigest()))
    print(json.dumps({"vehicle_id":str(vehicle_id),"device_id":str(device_id),
                      "device_token":token,
                      "warning":"Store this token securely; it will not be shown again."}))


if __name__ == "__main__":
    main()

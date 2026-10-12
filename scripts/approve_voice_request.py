"""Approve a short-lived voice demo proposal LOCALLY on the server host.

Never expose this as an unauthenticated API. Queue only after physically confirming
the vehicle is stationary. The X270 Supervisor also requires a local --arm and
checks RRBridge readiness/stationary data before any operation.
"""
import argparse
from app import store

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("request_id", type=int)
    args = parser.parse_args()
    store.init()
    with store.connect() as db:
        row = db.execute(
            """SELECT id,command,profile,state,expires_at,
                      (expires_at > now()) AS fresh
               FROM voice_requests WHERE id=%s FOR UPDATE""",
            (args.request_id,)).fetchone()
        if not row or row["state"] != "proposed" or not row["fresh"]:
            print("Request missing, expired, or already approved.")
            return 2
        if row["command"] != "switch_profile" or row["profile"] not in store.PROFILES:
            print("Rejected: unsupported request.")
            return 2
        print(f"Proposed on voice: switch_profile {row['profile']}")
        print("Only approve while physically at the STATIONARY X270.")
        confirm = input(f"Type APPROVE {row['id']} to queue REAL bench command: ")
        if confirm != f"APPROVE {row['id']}":
            print("Not approved")
            return 2
        # Recheck while holding the DB row lock.
        if not db.execute(
            "SELECT expires_at > now() AS fresh FROM voice_requests WHERE id=%s",
            (row["id"],)).fetchone()["fresh"]:
            print("Expired before approval.")
            return 2
        command = db.execute(
            """INSERT INTO commands(command,profile,target_mode)
               VALUES (%s,%s,'real') RETURNING id""",
            (row["command"],row["profile"])).fetchone()
        db.execute("""UPDATE voice_requests SET state='approved',command_id=%s
                      WHERE id=%s""",(command["id"],row["id"]))
    print(f"Approved voice request {row['id']} -> real command {command['id']}")
    print("This is QUEUED, not yet executed by X270.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

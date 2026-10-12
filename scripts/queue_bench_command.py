"""Queue ONE real-mode PoC command locally on the server (not exposed by HTTP/MCP).

Run only from inside the API container while an operator is physically
present at the X270 and has arranged safe stationary testing. Not for driving.
"""
import argparse
from app import store

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=sorted(store.ALLOWED))
    parser.add_argument("--profile", default="")
    args = parser.parse_args()
    command, profile = args.command, args.profile or None
    if command == "switch_profile" and profile not in store.PROFILES:
        parser.error("profile must be basic.xml or fuel.xml")
    if command != "switch_profile" and profile:
        parser.error("profile is accepted only for switch_profile")
    print("This will enqueue a REAL X270 command; the X270 local Supervisor")
    print("will independently require arming, readiness and stationary safeguards.")
    confirmation = input("If physically stationary, type: STATIONARY\n> ")
    if confirmation != "STATIONARY":
        raise SystemExit("Not queued.")
    store.init()
    with store.connect() as db:
        row = db.execute(
            """INSERT INTO commands(command,profile,target_mode)
               VALUES (%s,%s,'real') RETURNING id""", (command, profile)).fetchone()
    print("Queued real-mode command id:", row["id"])
    print("Submission does not imply execution; check the completion result.")

if __name__ == "__main__":
    main()

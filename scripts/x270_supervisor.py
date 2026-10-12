"""X270 outbound-polling Supervisor PoC for RRBridge v0.5.0.

Python 3.10+, standard library only. Defaults to a DRY RUN.
For real operations the operator must arm locally for 120 seconds.
Only allowed logging/profile commands; no ECU write/ROM/DTC endpoints.
"""
import argparse
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

COMMANDS = {"logging_start", "logging_stop", "filelog_start", "filelog_stop", "switch_profile"}
PROFILES = {"basic.xml", "fuel.xml"}
ARM_SECONDS = 120
SPEED_MAX_KMH = 0.5
SPEED_MAX_AGE_MS = 4000

class Refused(Exception):
    pass

def arm_path():
    return Path(os.environ.get("RR_SUPERVISOR_ARM_FILE",
                               str(Path.home() / ".rr-supervisor-arm.json")))

def receipts_path():
    return Path(os.environ.get("RR_SUPERVISOR_RECEIPTS",
                               str(Path.home() / ".rr-supervisor-receipts.json")))

def write_json_atomic(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, path)

def read_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, ValueError, OSError):
        return {}

def arm():
    target = arm_path()
    write_json_atomic(target, {"expires_epoch": time.time() + ARM_SECONDS})
    print(f"Local control armed for {ARM_SECONDS} seconds: {target}")
    print("Only use while physically present with the vehicle stationary.")

def require_arm():
    expiry = read_json(arm_path()).get("expires_epoch", 0)
    now = time.time()
    if not isinstance(expiry, (int, float)) or not now < expiry <= now + ARM_SECONDS + 1:
        raise Refused("local arming expired or absent; run --arm while stationary")

def http_json(url, *, token=None, method="GET", json_body=None, timeout=10):
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    data = None
    if json_body is not None:
        data = json.dumps(json_body).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, headers=headers, data=data, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)

def validate_endpoints(server_url, rrbridge_url):
    server = urllib.parse.urlsplit(server_url)
    rr = urllib.parse.urlsplit(rrbridge_url)
    if server.scheme != "https" and not (
        server.scheme == "http" and server.hostname in ("127.0.0.1", "localhost")
    ):
        raise Refused("server URL must use HTTPS except for local test")
    if rr.scheme != "http" or rr.hostname != "127.0.0.1" or rr.port != 18765:
        raise Refused("RRBridge endpoint must be http://127.0.0.1:18765")
    if server.username or server.password or rr.username or rr.password:
        raise Refused("URL must not embed credentials")
    return server_url.rstrip("/"), rrbridge_url.rstrip("/")

def recent_stationary_sample(spool_dir, session):
    """Require recent measured speed P9 from the current session's LOCAL spool."""
    if not re.fullmatch(r"[A-Za-z0-9_-]+", str(session or "")):
        raise Refused("invalid RRBridge session")
    path = Path(spool_dir) / ("rr_" + session + ".tsv")
    if not path.is_file():
        raise Refused("no local spool for current session")
    with path.open("rb") as fh:
        fh.seek(0, 2)
        fh.seek(max(0, fh.tell() - 262144))
        lines = fh.read().decode("utf-8", errors="replace").splitlines()
    for line in reversed(lines):
        cols = line.split("\t")
        if len(cols) != 6 or cols[0] != "S" or cols[1] != session:
            continue
        try:
            timestamp = int(cols[4])
            pairs = dict(x.split("=", 1) for x in cols[5].split(",") if "=" in x)
            if "P9" not in pairs:
                raise Refused("latest sample lacks P9; stationary state cannot be confirmed")
            speed = float(pairs["P9"])
        except (ValueError, OverflowError, TypeError):
            raise Refused("latest vehicle speed sample is invalid")
        age = time.time() * 1000 - timestamp
        if age < -1000 or age > SPEED_MAX_AGE_MS:
            raise Refused("vehicle speed sample stale")
        if not 0 <= speed <= SPEED_MAX_KMH:
            raise Refused("vehicle speed not stationary")
        return
    raise Refused("no actual P9 vehicle speed in current session")

def validate_command(command, profile):
    if command not in COMMANDS:
        raise Refused("unsupported command")
    if command == "switch_profile":
        if profile not in PROFILES:
            raise Refused("profile not explicitly approved for X270 PoC")
    elif profile:
        raise Refused("unexpected profile")

def validate_rrbridge_status(rr_url, rr_token, command, profile, spool_dir):
    status = http_json(rr_url + "/status", token=rr_token or None)
    if status.get("ready") is not True:
        raise Refused("RRBridge not ready")
    if command == "switch_profile":
        if (status.get("guard") or {}).get("enabled") is not True:
            raise Refused("profile protection guard is off")
        candidates = http_json(rr_url + "/list_profiles", token=rr_token or None).get("profiles", [])
        if not any(p.get("name") == profile and p.get("allowed") is True for p in candidates):
            raise Refused("profile missing or disallowed on X270")
    if status.get("logging") or status.get("fileLogging"):
        session = (status.get("stream") or {}).get("session")
        recent_stationary_sample(spool_dir, session)
    elif command in ("filelog_start", "filelog_stop"):
        raise Refused("file logging cannot be controlled while logging is stopped")
    return status

def execute_real(rr_url, rr_token, command, profile, spool_dir):
    require_arm()
    validate_command(command, profile)
    validate_rrbridge_status(rr_url, rr_token, command, profile, spool_dir)
    require_arm()
    query = "?profile=" + urllib.parse.quote(profile, safe="") if profile else ""
    if command in ("logging_start", "logging_stop"):
        query = "?wait_ms=3000"
    response = http_json(rr_url + "/" + command + query, token=rr_token or None,
                         method="POST", timeout=15)
    if response.get("ok") is not True:
        raise Refused("RRBridge rejected operation: " + str(response.get("error", "unknown"))[:200])
    return {"ok": True, "real_rrbridge": True, "command": command, "profile": profile or None}

def handle_command(item, *, real, rr_url, rr_token, spool_dir, receipt_file):
    ident = item.get("id")
    if type(ident) is not int or ident <= 0:
        raise Refused("invalid command id")
    receipts = read_json(receipt_file)
    key = str(ident)
    if key in receipts:
        saved = receipts[key]
        if saved.get("state") == "finished":
            return saved["result"]
        return {"ok": False, "error": "previous attempt has unknown outcome; local inspection required"}
    command = item.get("command")
    profile = item.get("profile") or ""
    validate_command(command, profile)
    if real and item.get("target_mode") != "real":
        raise Refused("mock/test commands cannot be executed on real RRBridge")
    # The receipt is written BEFORE any local side effect to avoid replay execution.
    receipts[key] = {"state": "started", "command": command, "profile": profile}
    write_json_atomic(receipt_file, receipts)
    try:
        if real:
            result = execute_real(rr_url, rr_token, command, profile, spool_dir)
        else:
            result = {"ok": True, "simulated": True, "real_rrbridge": False,
                      "command": command, "profile": profile or None}
    except (Refused, urllib.error.URLError, OSError, ValueError) as exc:
        result = {"ok": False, "error": str(exc)[:250], "real_rrbridge": False}
    receipts[key] = {"state": "finished", "result": result}
    write_json_atomic(receipt_file, receipts)
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arm", action="store_true",
                        help="allow local RRBridge control for 120 seconds")
    parser.add_argument("--real", action="store_true",
                        help="enable local RRBridge calls with safety checks")
    parser.add_argument("--once", action="store_true",
                        help="poll at most one command")
    args = parser.parse_args()
    if args.arm:
        arm()
        return 0
    server_url, rr_url = validate_endpoints(
        os.getenv("RR_SERVER_URL", "http://127.0.0.1:18767"),
        os.getenv("RRBRIDGE_URL", "http://127.0.0.1:18765"))
    agent_token = os.environ.get("AGENT_TOKEN")
    if not agent_token:
        raise Refused("AGENT_TOKEN required")
    if args.real:
        require_arm()
    spool_dir = os.getenv(
        "RRBRIDGE_SPOOL_DIR",
        str(Path.home() / "Documents" / "OpenPortWork" / "RRBridge" / "spool"))
    rr_token = os.environ.get("RRBRIDGE_TOKEN", "")
    print("Supervisor:", "LOCAL REAL ACTIONS" if args.real else "DRY RUN", flush=True)
    while True:
        if args.real:
            require_arm()  # Refuse to fetch after local operator approval expires.
        try:
            item = http_json(server_url + "/agent/commands/next",
                             token=agent_token).get("command")
            if item:
                result = handle_command(item, real=args.real, rr_url=rr_url,
                                        rr_token=rr_token, spool_dir=spool_dir,
                                        receipt_file=receipts_path())
                print(json.dumps({"id": item["id"], "result": result},
                                 ensure_ascii=False), flush=True)
                http_json(server_url + "/agent/commands/" + str(item["id"]) + "/complete",
                          token=agent_token, method="POST", json_body={"result": result})
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            print("Transient error:", exc, file=sys.stderr, flush=True)
        if args.once:
            return 0
        time.sleep(2)

if __name__ == "__main__":
    try:
        sys.exit(main())
    except (Refused, KeyError, OSError) as exc:
        print("Refused:", exc, file=sys.stderr)
        sys.exit(2)

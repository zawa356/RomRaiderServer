"""MOCK ONLY: polls the server, does not access RomRaider."""
import json
import os
import time
import urllib.request

base = os.getenv("SERVER_URL", "http://127.0.0.1:8080")
token = os.environ["AGENT_TOKEN"]
headers = {"Authorization": "Bearer " + token}
print("Mock agent (NO vehicle control) polling", base, flush=True)
while True:
    try:
        request = urllib.request.Request(base + "/agent/commands/next", headers=headers)
        with urllib.request.urlopen(request, timeout=10) as response:
            item = json.load(response)["command"]
        if item:
            print("MOCK received:", item, flush=True)
            payload = json.dumps({"result": {"ok": True, "mock": True,
                "message": "Not sent to RomRaider"}}).encode()
            req = urllib.request.Request(
                base + "/agent/commands/" + str(item["id"]) + "/complete",
                data=payload, headers={**headers, "Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=10) as response:
                print("MOCK acknowledged:", response.status, flush=True)
    except Exception as exc:
        print("Polling error:", exc, flush=True)
    time.sleep(2)

# C14 PoC protocol: ChatGPT Live → server → X270 → RRBridge

Status: **PROVISIONAL SERVER-SIDE EXTENSION**, 2026-10-12.
Upstream contract: [RomRaider_agent/docs/10_interfaces.md](https://github.com/zawa356/RomRaider_agent/blob/main/docs/10_interfaces.md), sections C2/C3/C4/C5/C8/C9 and C14.
Do not change the upstream contract or Agent code without coordinating its owner (Claude is actively updating that repo).

## Intent and boundaries

This demonstrates two logical directions without allowing an anonymous voice tool to execute a physical vehicle action:

1. X270 (RRBridge v0.5) → HTTPS `POST /ingest` → PostgreSQL → MCP read.
2. ChatGPT Live → anonymous **proposal** → DB → explicit local **approval** → short-lived real command queue → X270 outbound HTTPS poll → locally armed Supervisor → RRBridge `127.0.0.1:18765` → completion via HTTPS → MCP read.

**The no-auth voice demo can only request a proposal**, never a queueable/executeable command. The user has to explicitly approve on the server and arm the X270. This is a supervised bench-only test, not a hands-free driving solution. OAuth, user-to-device authorization and audited unattended policy are mandatory before that.

### Identity and rights

- `/voice-demo/mcp` is unauthenticated; `ALLOW_VOICE_PROPOSALS=false` by default. Tool `propose_demo_profile_switch` only accepts `basic.xml` or `fuel.xml`, records a `voice_requests` row that expires after 2 minutes, and enforces a global limit of five proposals/hour. `get_demo_request_status` returns proposal/command status without credentials.
- `/mcp` requires `MCP_TOKEN`; existing `submit_test_command` always creates `target_mode=mock`. Never upgrade the public voice MCP to direct command submission.
- `/agent/commands/next?mode=mock|real` requires `AGENT_TOKEN` and performs an outbound-polling claim for the requested mode. Defaults to `mock` for existing mock agent compatibility. New `target_mode` column is migrated automatically at application startup; older entries become `mock`.
- `/agent/commands/{id}/complete` requires `AGENT_TOKEN`, JSON `{"result":{"ok":true|false, ...}}`. Command status is `pending → leased → completed` (or `expired`). The 30-second lease may be retried, so the X270 has a persistent local receipt journal and must never execute an ambiguous replay.
- Both pending commands and voice proposals expire after 2 minutes (from their respective creation times). Command results remain queryable. This PoC assumes a single X270; no per-device credentials or durable exactly-once guarantee yet.
- Only the server admin's **interactive CLI** `scripts/approve_voice_request.py <id>` can convert an unexpired `voice_requests` row to a `target_mode=real` command, after typing `APPROVE <id>`. The DB transaction locks the proposal row to prevent duplicate approval.

## X270 Supervisor (Python reference PoC)

`scripts/x270_supervisor.py` requires Python 3.10+ but uses only stdlib; it is provided in **RomRaiderServer**, not RomRaider_agent. Dry-run is the default, real mode is explicitly `--real`.

Configuration via environment (do not commit credentials):

| Variable | Meaning |
| --- | --- |
| `RR_SERVER_URL` | public HTTPS root of the server, **without** `/agent`; Quick Tunnel is acceptable for temporary testing |
| `AGENT_TOKEN` | server-issued Bearer credential for X270 outward polling and ACK |
| `RRBRIDGE_TOKEN` | optional `rrbridge.properties` `http.token` |
| `RRBRIDGE_URL` | strictly `http://127.0.0.1:18765` (default) |
| `RRBRIDGE_SPOOL_DIR` | local RRBridge `spool` directory; defaults to user Documents/OpenPortWork/RRBridge/spool |
| `RR_SUPERVISOR_ARM_FILE` | optional local manually issued control approval file |
| `RR_SUPERVISOR_RECEIPTS` | optional persistent local replay-protection file |

Operations accepted: `logging_start`, `logging_stop`, `filelog_start`, `filelog_stop`, `switch_profile`. Real-mode switch permits only `basic.xml` and `fuel.xml` and checks RRBridge `list_profiles` for `allowed=true`, plus `guard.enabled=true`. No `load_profile`, `selftest_stream`, arbitrary file path or ECU ROM/DTC/reset operations.

`--arm` writes a local expiry (120 seconds). `--real` refuses without this operator action and stops accepting claims when it expires. If the logger is active, a current-local-session **P9 (Vehicle Speed) sample, 0–0.5 km/h, younger than 4s** is required. Missing/stale speed or a different measurement profile fails closed. When logging is stopped, switching between preapproved profiles is possible only under the short-lived local arming. An operator must confirm the vehicle is physically stationary before arming; this alone is not an automated motion guarantee.

Status and profile data are read from **local** C3 RRBridge HTTP. Control is `POST /<command>?profile=<filename>`, or `?wait_ms=3000` for logging start/stop. The response body's `ok` is checked, not HTTP status alone. Failures are acknowledged to server as `{"result":{"ok":false,...}}`.

## End-to-end test in phases

### A. Pull and redeploy Ubuntu Server (retain local host port 18767)

```bash
git pull --ff-only
docker compose -f compose.yaml -f compose.voice-demo.yaml up -d --build
docker compose -f compose.yaml -f compose.voice-demo.yaml ps
curl -i http://127.0.0.1:18767/mcp    # expected 401 without token
```

If a local edit to compose.yaml conflicts, **do not reset or overwrite it**. Keep existing port 18767.

### B. Mock-only test first

Set `ALLOW_TEST_COMMANDS=true` in `.env`, and recreate `mcp` with Compose. Call authenticated `submit_test_command` via MCP with e.g. `switch_profile` / `basic.xml`, while running `scripts/mock_agent.py` in an API container. `get_command_status(id)` should return `completed` and `mock=true`. No actual X270 use.

### C. Voice proposal (still no real action)

Set `ALLOW_VOICE_PROPOSALS=true` in the local `.env` and recreate `voice-demo` service using the optional Compose overlay. Restarting/refreshing ChatGPT's plugin discovery might be necessary for the two newly added tools.
ChatGPT Live: “RomRaiderServer Voice Demo の propose_demo_profile_switch を使って basic.xml への切替を提案して。実行しないで。リクエスト番号も教えて。”
The server returns an ID and `state=proposed`. **No queue operation or vehicle change has occurred**.

### D. Manual approval and real X270 bench test — stationary only

1. On X270, place this repo's `scripts/x270_supervisor.py` and set `RR_SERVER_URL` to current tunnel's HTTPS root, `AGENT_TOKEN` to the server secret, and optional local `RRBRIDGE_TOKEN`. Ensure RRBridge v0.5 is running and **logger is stopped** initially.
2. On X270 console: `py -3 scripts\\x270_supervisor.py --arm`, then `py -3 scripts\\x270_supervisor.py --real`. Keep vehicle stationary. The arming expires in 120 seconds. Real-mode is never enabled by default.
3. Obtain a voice request ID with step C. Within 120 seconds, on Ubuntu Server: `docker compose exec api python scripts/approve_voice_request.py <REQUEST_ID>`. At the prompt enter exactly `APPROVE <REQUEST_ID>`.
4. X270 polls `GET /agent/commands/next?mode=real`, checks local policy, calls `POST http://127.0.0.1:18765/switch_profile?profile=basic.xml`, and sends a completion report to `/agent/commands/<ID>/complete`.
5. Ask ChatGPT Live to call `get_demo_request_status(<REQUEST_ID>)`. Only `command_status=completed`, `result_ok=true` **and** `real_rrbridge=true` confirm the full X270 command path. Confirm locally in RomRaider UI too.

The approval window is intentionally short. If it expires, request a new proposal; never extend TTL or turn off local checks merely to complete the test. If P9 is unavailable during active logging, do NOT proceed until a safe stopped-logger test can be performed.

### E. Retire temporary no-auth facilities

Disable `ALLOW_VOICE_PROPOSALS`; remove the optional voice demo container, stop the Cloudflare Quick Tunnel, and rotate test secrets if shared.

## Follow-up for the Agent (Claude)

The **upstream contract §C14 is still only a proposed extension**. Before any unattended operation or driving use, reconcile versioned request/response schemas across repos, authenticate each X270 device separately, implement audited identity-based OAuth for ChatGPT, and establish explicit operator consent, stale-command refusal, guarded profile inventory, operation timeout and rollback semantics. Do not consider this script production Supervisor.

## Verification

As of 2026-10-12: server source code is on GitHub. Supervisor safety/idempotency unit tests were run locally (7 passed) before integration. The updated Docker images, new DB migration, voice write-proposal flow, and real X270 operation **have not yet been executed on the user's host**.

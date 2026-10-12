# RomRaiderServer — Docker PoC

> **製品全体の要件定義（正本）**: [RomLogger システム要件定義書 v1.0.0（承認済み）](docs/system_requirements.md)。本READMEおよび [PoC要件](docs/requirements.md) は現行PoCの説明です。走行中の計測制御や認証に関する製品目標・未検証事項は正本を参照してください。文書の追加は実装・安全制限の変更を意味しません。

Small, isolated proof of concept for **ChatGPT Live → Remote MCP → command queue → simulated X270**, and **RRBridge TSV → Ingest API → PostgreSQL → MCP**.

**Not production-ready.** The mock agent never calls RomRaider or RRBridge. The explicit X270 Supervisor can call the local RRBridge only when armed and after server-admin approval; all remote control remains disabled by default.

## ChatGPT Live without OAuth: restricted demo and non-executing proposals

ChatGPT's custom MCP registration UI offers OAuth, No authentication, or OAuth/No authentication; it does **not** offer a static Bearer header input. The existing secured `/mcp` endpoint must remain protected.

For a **temporary proof of concept only**, enable a separate public demo MCP that reads a single synthetic test row already loaded into the database (`poc_001`, `segment=1`, `seq=1`; only `TEST_RPM` and `TEST_ECT`). It has **no executable command submission, SQL access, access to other sessions, or ECU control tool**. Optional tools may store short-lived proposals but cannot dispatch them without interactive server-admin approval and X270 local arming. Do not change it to return live vehicle data without introducing user authentication.

This is an optional Compose overlay so it does not overwrite local `compose.yaml` edits (such as the host port changed to `18767`).

```bash
git pull --ff-only
docker compose -f compose.yaml -f compose.voice-demo.yaml up -d --build voice-demo
docker compose -f compose.yaml -f compose.voice-demo.yaml restart proxy
docker compose -f compose.yaml -f compose.voice-demo.yaml ps
```

On the current test host where the proxy binds to `127.0.0.1:18767`:

```bash
curl -si http://127.0.0.1:18767/mcp  # Must remain 401
curl -sS -X POST http://127.0.0.1:18767/voice-demo/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"get_demo_vehicle_status","arguments":{}}}' | python3 -m json.tool
```

Expected: `demo=true`, `live=false`, `engine_rpm=2500`, `coolant_temperature_c=87`, `isError=false` (provided that the prior `poc_001` sample is present).

With the existing **temporary** Cloudflare Tunnel, register
`https://<current-quick-tunnel-host>/voice-demo/mcp` in ChatGPT with authentication **なし / No authentication**. Do **not** use the protected `/mcp` path. Try: "RomRaiderServer Voice Demo の get_demo_vehicle_status ツールを実行して、ダミーのエンジン回転数と水温を読み上げてください。"

**Any Internet user who knows the URL can query these two deliberately fake demo values.** Stop the quick tunnel when finished; remove the overlay in production. The main `/mcp` remains Bearer-protected, and the agent/ingest API still require their independent tokens. For genuine remote control and real vehicle data, implement OAuth and a safe X270 Supervisor first.

### Live demo: latest verified RRBridge selftest values

The public `/voice-demo/mcp` includes `get_latest_rrbridge_selftest`.
It returns only `TEST_RPM` (rpm), `TEST_TPS` (%), and `TEST_MRP` (kPa)
from the **newest verified RRBridge synthetic selftest sample**. The query
requires *all* of the following for the same session/segment:

- Exactly those three `TEST_*` sample keys, **no other keys**.
- Matching `parameters` metadata with the precise selftest names and units emitted by RRBridge `Stream.selftest()`.
- A matching `selftest start count=<n> hz=<n>` event in the same segment.

Samples missing proof, or containing even one real ECU parameter such as `P8`,
cannot appear in this public tool. This is a synthetic-only debugging facility,
**not** a real-time ECU monitor. The result contains `timestamp_ms`, `session`,
`segment`, `seq`, and `live=false`; it may be historical. It never performs
RomRaider operations. Existing tools `get_demo_vehicle_status`,
`propose_demo_profile_switch` and `get_demo_request_status` remain available.

After pushing new code to the repository:

```bash
git pull --ff-only
docker compose -f compose.yaml -f compose.voice-demo.yaml up -d --build voice-demo
```

Only the `voice-demo` container is recreated. In the ChatGPT custom MCP UI,
refresh/reconnect the existing custom MCP so it discovers
`get_latest_rrbridge_selftest`.

When an X270 selftest has been ingested, ask ChatGPT Live:

> RomRaiderServer Voice Demo の get_latest_rrbridge_selftest を実行し、最後に受信した合成データの回転数、スロットル開度、相対圧力とサンプル番号を教えて。実ECUの値ではないことも明言して。

To verify without ChatGPT:

```bash
curl -sS -X POST http://127.0.0.1:18767/voice-demo/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":11,"method":"tools/call","params":{"name":"get_latest_rrbridge_selftest","arguments":{}}}' \
  | python3 -m json.tool
```

The local `/mcp` endpoint remains Bearer-protected and can read all samples,
so do not expose its token in the no-auth demo.

## Verification milestones

### 2026-10-12 — ChatGPT Live (Android) + Remote MCP (user-reported PASS)

**Verified by the user in an actual running Docker environment:**

- Container startup and PostgreSQL health check.
- Local Caddy HTTP `/health` returned HTTP 200; protected `/mcp` returned HTTP 401 without a token.
- Authenticated MCP `initialize`, `tools/list` (four tools) and `get_vehicle_status` calls returned successfully.
- Ingest API accepted one synthetic M/S TSV sample, `session=poc_001`, `TEST_RPM=2500`, `TEST_ECT=87`, `samples=1`, `duplicates=0`.
- Protected MCP readback returned the same sample from PostgreSQL (`isError=false`).
- Cloudflare Quick Tunnel established externally reachable HTTPS; unauthenticated request to protected `/mcp` returned HTTP 401.
- A dedicated, no-auth **read-only** `/voice-demo/mcp` was registered in ChatGPT. User confirmed that ChatGPT Live returned a response successfully. The demo only exposes synthetic `poc_001` values.

**Not yet verified:** whether mock X270 command polling/acknowledgment works end-to-end; actual RRBridge and ECU telemetry; real vehicle control; OAuth authorization, reliability, throughput and operational security.

This is a user-reported test outcome, not an automated CI result. The public no-auth demo must remain limited to synthetic test data and be disabled after testing.

For the proposed voice-to-X270 bench command path and full safeguards, see [C14 control PoC contract](docs/control_protocol_poc.md). **Do not run a real-vehicle test while driving.**

## Quick start

1. Copy `.env.example` to `.env`. Choose **different long random secrets** for `POSTGRES_PASSWORD`, `INGEST_TOKEN`, `AGENT_TOKEN`, and `MCP_TOKEN`; update the password in `DATABASE_URL` to match (URL-encode special characters, or use alphanumeric secrets).
2. Run `docker compose up -d --build`.
3. Check `curl http://127.0.0.1:8080/health`.
4. Run a simulated X270 in a separate terminal: `docker compose run --rm -e SERVER_URL=http://proxy:80 api python scripts/mock_agent.py`.
5. For ChatGPT Live without OAuth, use the isolated `/voice-demo/mcp` overlay described above. The secured `/mcp` is not directly registerable as a Bearer-header custom MCP in the current UI.

The Compose reverse proxy **binds only 127.0.0.1:8080**, not the public Internet. For a temporary ChatGPT Live test, expose this port using a secure HTTPS tunnel. Do not publish port 8080 or the MCP app directly. Authentication occurs at the Caddy proxy. The MCP backend trusts the proxy and must not be separately exposed.

## API and contract

- `POST /ingest`: RRBridge M/S/E TSV (max 512 KiB) with `Authorization: Bearer INGEST_TOKEN`; sample duplicates deduplicated by `(session,seq)`. Metadata and event deduplication is simplified for the PoC.
- `GET /agent/commands/next`: authenticated X270 outgoing poll, returns at most one leased command (30-second lease).
- `POST /agent/commands/{id}/complete`: authenticated completion result.
- `GET /health`: health check.
- `/mcp`: Streamable HTTP MCP with tools `get_vehicle_status`, `get_command_status`, `propose_measurement_command` and `submit_test_command`.

Only `logging_start`, `logging_stop`, `filelog_start`, `filelog_stop` and `switch_profile` are whitelisted. Proposed commands cannot execute. `submit_test_command` requires `ALLOW_TEST_COMMANDS=true` and MUST ONLY be used with the mock agent. Do not set this when an actual X270 client is connected.

To test the mock command path, set `ALLOW_TEST_COMMANDS=true` in `.env` and restart the MCP container (`docker compose up -d --force-recreate mcp`). Ask ChatGPT to submit a test command, then query its ID using `get_command_status`. Confirm the mock agent log says `MOCK received`, and the result indicates `mock: true`.

## Design choices and limitations

- Services: Caddy proxy, MCP Python process, FastAPI ingestion/agent endpoints, PostgreSQL 16.
- Outbound-only command delivery: X270 initiates polling; no Internet-facing listener on the vehicle.
- Separate random secrets for ingest, agent, and MCP. DB not publicly exposed.
- Command table is a prototype only: **no per-device ownership, device authentication identity, profile inventory, cryptographic receipts, cancellation, stale-command policy or user confirmation workflow**. No direct real-car connection.
- PoC has a simple sample schema storing ID/value maps as JSONB rather than the eventual normalized time-series schema.
- No idempotency for command submissions, no replay prevention beyond command leases. Lost acknowledgment can cause retries; the mock client must be treated as disposable.
- `docker compose config` and live MCP/HTTP integration need to be verified on a Docker-enabled machine.
- Source-of-truth Agent protocol: [RRBridge design](https://github.com/zawa356/RomRaider_agent/blob/main/docs/03_rrbridge_design.md).

## Next gates

1. Confirm ChatGPT Live connection, read tool invocation, and audible response.
2. Confirm mock command submission, lease, completion, and trace.
3. Validate TSV replays against the real RRBridge spool.
4. Specify and implement safe Supervisor, approvals, device identity and retry/idempotency BEFORE allowing physical X270 control.

# RomRaiderServer — Docker PoC

Small, isolated proof of concept for **ChatGPT Live → Remote MCP → command queue → simulated X270**, and **RRBridge TSV → Ingest API → PostgreSQL → MCP**.

**Not production-ready. It cannot operate a real vehicle.** The mock agent never calls RomRaider or RRBridge. Commands submitted by MCP are disabled by default.

## ChatGPT Live without OAuth: isolated read-only demo

ChatGPT's custom MCP registration UI offers OAuth, No authentication, or OAuth/No authentication; it does **not** offer a static Bearer header input. The existing secured `/mcp` endpoint must remain protected.

For a **temporary proof of concept only**, enable a separate, public **read-only** MCP that exposes a single safe test row already loaded into the database (`poc_001`, `segment=1`, `seq=1`; only `TEST_RPM` and `TEST_ECT`). It has **no command submission, SQL access, access to other sessions, or ECU control tool**. Do not change it to return live vehicle data without introducing user authentication.

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

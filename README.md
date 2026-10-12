# RomRaiderServer — Docker PoC

Small, isolated proof of concept for **ChatGPT Live → Remote MCP → command queue → simulated X270**, and **RRBridge TSV → Ingest API → PostgreSQL → MCP**.

**Not production-ready. It cannot operate a real vehicle.** The mock agent never calls RomRaider or RRBridge. Commands submitted by MCP are disabled by default.

## Quick start

1. Copy `.env.example` to `.env`. Choose **different long random secrets** for `POSTGRES_PASSWORD`, `INGEST_TOKEN`, `AGENT_TOKEN`, and `MCP_TOKEN`; update the password in `DATABASE_URL` to match (URL-encode special characters, or use alphanumeric secrets).
2. Run `docker compose up -d --build`.
3. Check `curl http://127.0.0.1:8080/health`.
4. Run a simulated X270 in a separate terminal: `docker compose run --rm -e SERVER_URL=http://proxy:80 api python scripts/mock_agent.py`.
5. Register the public HTTPS URL ending in `/mcp` as a custom MCP plugin. Use the `Authorization: Bearer <MCP_TOKEN>` header when supported.

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

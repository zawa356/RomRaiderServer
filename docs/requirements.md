# PoC requirements and boundaries

- REQ-001: ChatGPT Live can query the latest received telemetry via Remote MCP.
- REQ-002: RRBridge M/S/E data is received over authenticated HTTP and survives container restart in PostgreSQL.
- REQ-003: ChatGPT can propose a measurement command; when explicitly enabled in test mode it can enqueue a simulated command.
- REQ-004: A mock X270 agent polls commands outbound and returns execution results. No server-to-X270 inbound port is required.
- REQ-005: Real vehicle operation, arbitrary XML paths, ROM reading/writing, DTC clearance, ECU reset and ECU firmware updates are outside PoC scope.
- REQ-006: Command receipts/status and failures must be observable.

The PoC is not a final design of command authorization or delivery reliability. Real driving scenarios require separate safety policy, driver approval model, stale command expiry, profile allowlist reconciliation, and dedicated on-device Supervisor.

## Added 2026-10-12: Bidirectional voice-driven measurement requests

- REQ-CONTROL-001: ChatGPT Live must be able to propose logger/measurement changes and retrieve the result, not merely read telemetry.
- REQ-CONTROL-002: X270 must initiate outbound HTTPS command polling and send execution feedback; no Internet-to-X270 inbound listener is required.
- REQ-CONTROL-003: Neither anonymous MCP nor a queued instruction authorizes a real vehicle operation. Server-side approval and local X270 policy must both pass; the final production auth will require OAuth and a bound user/device identity.
- REQ-CONTROL-004: Allowlisted commands, preapproved profile names, expiry, replay protection, stationarity checks when logging, and local arming are required before any real operation. Fail closed when speed data cannot establish stationarity.
- REQ-CONTROL-005: Default mode must be dry-run and mock test commands cannot be executed as real commands.
- REQ-CONTROL-006: The client must distinguish queued/leased/completed/expired and never present queue acceptance alone as a successful vehicle action.

Implementation/protocol draft: [control_protocol_poc.md](control_protocol_poc.md).
Upstream C2/C3/C4/C14 source of truth: [RomRaider_agent interface contract](https://github.com/zawa356/RomRaider_agent/blob/main/docs/10_interfaces.md). This server-side draft has NOT been merged into the upstream Agent contract yet.

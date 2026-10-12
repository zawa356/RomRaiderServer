# PoC requirements and boundaries

- REQ-001: ChatGPT Live can query the latest received telemetry via Remote MCP.
- REQ-002: RRBridge M/S/E data is received over authenticated HTTP and survives container restart in PostgreSQL.
- REQ-003: ChatGPT can propose a measurement command; when explicitly enabled in test mode it can enqueue a simulated command.
- REQ-004: A mock X270 agent polls commands outbound and returns execution results. No server-to-X270 inbound port is required.
- REQ-005: Real vehicle operation, arbitrary XML paths, ROM reading/writing, DTC clearance, ECU reset and ECU firmware updates are outside PoC scope.
- REQ-006: Command receipts/status and failures must be observable.

The PoC is not a final design of command authorization or delivery reliability. Real driving scenarios require separate safety policy, driver approval model, stale command expiry, profile allowlist reconciliation, and dedicated on-device Supervisor.

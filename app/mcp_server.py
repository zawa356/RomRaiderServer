"""Remote MCP tools. Command submission is disabled until explicitly opted in."""
import os
from mcp.server.fastmcp import FastMCP
from . import store

mcp = FastMCP("RomRaiderServer PoC", host="0.0.0.0", port=8001,
              stateless_http=True, json_response=True)

@mcp.tool()
def get_vehicle_status() -> dict:
    """Read the latest received telemetry; never a live ECU operation."""
    store.init()
    return store.latest()

@mcp.tool()
def get_command_status(command_id: int) -> dict:
    """Read the status and outcome of an already submitted command."""
    store.init()
    return store.command_status(command_id) or {"error": "not_found"}

@mcp.tool()
def propose_measurement_command(command: str, profile: str = "") -> dict:
    """Validate a request but DO NOT dispatch it. Only logging/file-log start/stop and switch_profile are allowed."""
    if command not in store.ALLOWED:
        return {"ok": False, "error": "command not allowed"}
    try:
        import re
        if command == "switch_profile":
            if not re.fullmatch(r"[A-Za-z0-9_.-]+\.xml", profile) or profile.startswith("."):
                return {"ok": False, "error": "invalid profile"}
        elif profile:
            return {"ok": False, "error": "unexpected profile"}
    except TypeError:
        return {"ok": False, "error": "invalid profile"}
    return {"ok": True, "proposal_only": True, "command": command, "profile": profile or None}

@mcp.tool()
def submit_test_command(command: str, profile: str = "") -> dict:
    """Queue a command ONLY for a MOCK vehicle agent. Disabled by default. Never connect to a car."""
    if os.getenv("ALLOW_TEST_COMMANDS", "false").lower() != "true":
        return {"ok": False, "error": "test commands are disabled"}
    try:
        store.init()
        return store.submit(command, profile or None)
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}

if __name__ == "__main__":
    store.init()
    mcp.run(transport="streamable-http")

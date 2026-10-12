"""No-auth, read-only MCP for temporary ChatGPT Live validation.

This process deliberately has NO command tools and exposes only synthetic test
session poc_001, seq=1. Never use it for real ECU telemetry.
"""
import os
from mcp.server.fastmcp import FastMCP
from . import store
from .store import connect

mcp = FastMCP(
    "RomRaiderServer Voice Demo",
    host="0.0.0.0",
    port=8002,
    stateless_http=True,
    json_response=True,
)

@mcp.tool()
def get_demo_vehicle_status() -> dict:
    """Read ONLY the synthetic poc_001 sample: test RPM and coolant temperature.
    Not live data; this tool cannot read other sessions or control RomRaider.
    """
    with connect() as db:
        row = db.execute(
            """SELECT values_json->>'TEST_RPM' AS rpm,
                      values_json->>'TEST_ECT' AS coolant_c
               FROM samples
               WHERE session = %s AND segment = 1 AND seq = 1
               LIMIT 1""",
            ("poc_001",),
        ).fetchone()

    if not row or row["rpm"] is None or row["coolant_c"] is None:
        return {
            "ok": False,
            "demo": True,
            "live": False,
            "message": "Synthetic poc_001 test sample was not found",
        }
    return {
        "ok": True,
        "demo": True,
        "live": False,
        "sample": "poc_001",
        "engine_rpm": float(row["rpm"]),
        "coolant_temperature_c": float(row["coolant_c"]),
        "message": "Historical synthetic test data, not a current vehicle reading",
    }

@mcp.tool()
def propose_demo_profile_switch(profile: str) -> dict:
    """Create a short-lived profile-switch PROPOSAL ONLY, not an executable vehicle
    command. Requires explicit physical operator approval on X270/server afterward.
    Limited to basic.xml and fuel.xml. No real-world effect from this tool.
    """
    if os.getenv("ALLOW_VOICE_PROPOSALS", "false").lower() != "true":
        return {"accepted": False, "error": "voice proposals disabled"}
    try:
        store.init()
        return store.propose_voice(profile)
    except ValueError as exc:
        return {"accepted": False, "error": str(exc)}

@mcp.tool()
def get_demo_request_status(request_id: int) -> dict:
    """Check the state of a previously proposed (not automatically executed) demo request."""
    store.init()
    return store.voice_request_status(request_id)

if __name__ == "__main__":
    store.init()
    mcp.run(transport="streamable-http")

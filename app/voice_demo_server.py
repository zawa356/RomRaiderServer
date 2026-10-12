"""No-auth, read-only MCP for temporary ChatGPT Live validation.

This process deliberately has NO command tools and exposes only synthetic test
session poc_001, seq=1. Never use it for real ECU telemetry.
"""
from mcp.server.fastmcp import FastMCP
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

if __name__ == "__main__":
    mcp.run(transport="streamable-http")

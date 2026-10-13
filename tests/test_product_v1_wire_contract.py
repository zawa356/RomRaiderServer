"""Machine-checkable Agent API v1 contract drift and runtime boundary tests.

The committed OpenAPI is the product wire specification, not FastAPI's generated
schema. Compare their overlapping request models and validate real responses.
"""
from pathlib import Path
import hashlib
import json
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from jsonschema import Draft202012Validator, FormatChecker

from product_v1 import store
from product_v1.api import app


CONTRACT = json.loads((Path(__file__).resolve().parents[1] /
                       "docs/interfaces/agent_api_v1.openapi.json").read_text(encoding="utf-8"))
RUNNING = app.openapi()
ROOT = "/api/agent/v1"


def ref(schema, document):
    while "$ref" in schema:
        path = schema["$ref"]
        assert path.startswith("#/")
        node = document
        for token in path[2:].split("/"):
            node = node[token]
        schema = node
    return schema


def test_all_seven_product_agent_routes_match_committed_spec():
    expected = {
        (path, method)
        for path, operations in CONTRACT["paths"].items()
        for method in operations
        if method in ("get", "put", "post", "patch", "delete")
    }
    assert len(expected) == 7
    actual = {
        (path, method)
        for path, operations in RUNNING["paths"].items()
        for method in operations
        if path.startswith(ROOT) and method in ("get", "put", "post", "patch", "delete")
    }
    # Product-only diagnostic readback is documented separately. It is not
    # part of the seven immutable Agent wire-v1 operations.
    actual.discard((ROOT+"/telemetry/recent", "get"))
    assert expected == actual


def test_top_level_request_required_fields_and_property_names_have_no_drift():
    for path, operations in CONTRACT["paths"].items():
        for method, expected in operations.items():
            if method not in ("put", "post"):
                continue
            legacy_request=ref(
                expected["requestBody"]["content"]["application/json"]["schema"], CONTRACT
            )
            running_request=ref(
                RUNNING["paths"][path][method]["requestBody"]["content"]["application/json"]["schema"],
                RUNNING
            )
            assert set(legacy_request.get("required", [])) == set(running_request.get("required", [])), (
                f"Required fields drift: {method.upper()} {path}"
            )
            assert set(legacy_request["properties"]) == set(running_request["properties"]), (
                f"Known properties drift: {method.upper()} {path}"
            )


@pytest.mark.parametrize("reference,actual", [
    ("ProfileParameter", "ProfileParameter"),
    ("ObservationValue", "MeasurementValue"),
    ("ObservationRecord", "Observation"),
    ("EventRecord", "Event"),
    ("GapRecord", "Gap"),
    ("AcquisitionStatus", "Acquisition"),
    ("SpoolStatus", "Spool"),
    ("ParameterCapability", "CapabilityParameter"),
])
def test_nested_wire_models_keep_required_fields(reference, actual):
    static = CONTRACT["components"]["schemas"][reference]
    live = RUNNING["components"]["schemas"][actual]
    assert set(static.get("required", [])) == set(live.get("required", []))
    assert set(static["properties"]) == set(live["properties"])


def test_restricted_action_and_state_enumerations_do_not_drift():
    enums = (
        ("CommandLease", "action"),
        ("CommandReportRequest", "state"),
        ("ParameterCapability", "availability"),
    )
    mapping = {
        "CommandLease":"CommandLease",
        "CommandReportRequest":"CommandReportRequest",
        "ParameterCapability":"CapabilityParameter",
    }
    for schema_name, field in enums:
        reference = CONTRACT["components"]["schemas"][schema_name]["properties"][field]
        live = RUNNING["components"]["schemas"][mapping[schema_name]]["properties"][field]
        assert set(reference["enum"]) == set(live["enum"])


def assert_matches(schema_name, value):
    container={
        "$ref":"#/components/schemas/"+schema_name,
        "components":CONTRACT["components"],
    }
    Draft202012Validator(container,format_checker=FormatChecker()).validate(value)


@pytest.fixture
def device():
    store.require_schema()
    vehicle, ident = uuid4(),uuid4()
    token="contract_ci_"+uuid4().hex
    with store.connect() as db:
        db.execute("INSERT INTO v1_vehicles(vehicle_id,display_name) VALUES (%s,%s)",
                   (vehicle,"CI contract wire vehicle"))
        db.execute("INSERT INTO v1_devices(device_id,vehicle_id,token_sha256) VALUES (%s,%s,%s)",
                   (ident,vehicle,hashlib.sha256(token.encode()).hexdigest()))
    with TestClient(app) as client:
        yield {"client":client,"vehicle":str(vehicle),"device":str(ident),
               "headers":{"Authorization":"Bearer "+token}}


def test_live_status_response_and_optional_quality_fields_match_wire(device):
    body={
        "protocol_version":1, "device_id":device["device"],"vehicle_id":device["vehicle"],
        "reported_at":"2026-10-13T02:10:00+09:00",
        "agent_version":"synthetic-ci","logger_state":"logging",
        "acquisition":{"last_observed_at":"2026-10-13T02:09:59+09:00",
                       "recent_hz":2.5,"drop_count":0},
        "spool":{"unacked_records":12,"pending_bytes":10000},
        "ecu_state":"read_only","link_error_count":3,
    }
    result=device["client"].post(ROOT+"/status",json=body,headers=device["headers"])
    assert result.status_code==200,result.text
    assert_matches("DeviceStatusResponse", result.json())
    with store.connect() as db:
        stored=db.execute("SELECT state FROM v1_device_status WHERE device_id=%s",
                          (device["device"],)).fetchone()["state"]
    assert stored["ecu_state"]=="read_only"
    assert stored["link_error_count"]==3
    assert stored["acquisition"]["recent_hz"]==2.5


def test_unsupported_major_version_returns_426_not_422(device):
    body={
        "protocol_version":2,"device_id":device["device"],"vehicle_id":device["vehicle"],
        "reported_at":"2026-10-13T02:10:00Z",
        "agent_version":"synthetic-ci","logger_state":"unknown",
        "acquisition":{"last_observed_at":None,"recent_hz":None,"drop_count":0},
        "spool":{"unacked_records":0,"pending_bytes":0},
    }
    response=device["client"].post(ROOT+"/status",json=body,headers=device["headers"])
    assert response.status_code==426,response.text
    assert response.json()["error"]["code"]=="UNSUPPORTED_PROTOCOL_VERSION"
    assert_matches("ErrorResponse",response.json())


def test_quality_input_rejects_invalid_rates_timestamps_and_counters(device):
    base={
        "protocol_version":1,"device_id":device["device"],"vehicle_id":device["vehicle"],
        "reported_at":"2026-10-13T02:10:00Z",
        "agent_version":"synthetic-ci","logger_state":"unknown",
        "acquisition":{"last_observed_at":None,"recent_hz":None,"drop_count":0},
        "spool":{"unacked_records":0,"pending_bytes":0},
    }
    cases=[
        ("recent_hz",-1.0),
        ("recent_hz","NaN"),
        ("last_observed_at","2026-10-13T02:00:00"),
        ("drop_count",-1),
    ]
    for name,bad in cases:
        body=json.loads(json.dumps(base))
        body["acquisition"][name]=bad
        response=device["client"].post(ROOT+"/status",json=body,headers=device["headers"])
        assert response.status_code==422,(name,response.text)
        assert_matches("ErrorResponse",response.json())
    invalid=json.loads(json.dumps(base))
    invalid["link_error_count"]=-2
    assert device["client"].post(ROOT+"/status",json=invalid,
                                 headers=device["headers"]).status_code==422

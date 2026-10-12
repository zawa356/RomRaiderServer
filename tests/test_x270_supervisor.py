"""Run: python -m pytest -q tests/test_x270_supervisor.py"""
import importlib.util
from pathlib import Path
import sys
import time
import json
import pytest

spec = importlib.util.spec_from_file_location(
    "rr_supervisor", Path(__file__).resolve().parents[1] / "scripts/x270_supervisor.py")
s = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = s
spec.loader.exec_module(s)

def test_endpoints_must_be_https_and_rrbridge_loopback():
    assert s.validate_endpoints("https://example.org", "http://127.0.0.1:18765") == (
        "https://example.org", "http://127.0.0.1:18765")
    with pytest.raises(s.Refused):
        s.validate_endpoints("http://example.org", "http://127.0.0.1:18765")
    with pytest.raises(s.Refused):
        s.validate_endpoints("https://example.org", "http://192.168.1.3:18765")

def test_only_preapproved_logging_commands_and_profiles():
    s.validate_command("switch_profile", "basic.xml")
    with pytest.raises(s.Refused):
        s.validate_command("switch_profile", "../../evil.xml")
    with pytest.raises(s.Refused):
        s.validate_command("switch_profile", "unknown.xml")
    with pytest.raises(s.Refused):
        s.validate_command("ecu_reset", "")
    with pytest.raises(s.Refused):
        s.validate_command("logging_stop", "fuel.xml")

def test_local_arming_expires(tmp_path, monkeypatch):
    monkeypatch.setenv("RR_SUPERVISOR_ARM_FILE", str(tmp_path / "arm.json"))
    with pytest.raises(s.Refused):
        s.require_arm()
    s.arm()
    s.require_arm()
    s.write_json_atomic(s.arm_path(), {"expires_epoch": time.time()-1})
    with pytest.raises(s.Refused):
        s.require_arm()

def test_missing_stale_or_moving_speed_fails_closed(tmp_path):
    sess = "test_1"
    p = tmp_path / f"rr_{sess}.tsv"
    now = int(time.time()*1000)
    p.write_text(f"S\t{sess}\t1\t1\t{now}\tP9=0.0,P8=800\n")
    s.recent_stationary_sample(tmp_path, sess)
    p.write_text(f"S\t{sess}\t1\t1\t{now}\tP9=12.0\n")
    with pytest.raises(s.Refused):
        s.recent_stationary_sample(tmp_path, sess)
    p.write_text(f"S\t{sess}\t1\t1\t{now-10000}\tP9=0.0\n")
    with pytest.raises(s.Refused):
        s.recent_stationary_sample(tmp_path, sess)
    p.write_text(f"S\t{sess}\t1\t1\t{now}\tP8=800\n")
    with pytest.raises(s.Refused):
        s.recent_stationary_sample(tmp_path, sess)

def test_duplicate_command_never_executes_twice(tmp_path):
    p = tmp_path/"receipts.json"
    cmd = {"id":123,"command":"switch_profile","profile":"fuel.xml"}
    a = s.handle_command(cmd,real=False,rr_url="",rr_token="",
                         spool_dir="",receipt_file=p)
    assert a["ok"] and a["simulated"]
    b = s.handle_command(cmd,real=False,rr_url="",rr_token="",
                         spool_dir="",receipt_file=p)
    assert b == a
    assert len(json.loads(p.read_text()))==1

def test_restart_after_unknown_execution_fails_closed(tmp_path):
    p = tmp_path/"receipts.json"
    s.write_json_atomic(p,{"4":{"state":"started"}})
    result = s.handle_command({"id":4,"command":"switch_profile","profile":"basic.xml"},
                              real=False,rr_url="",rr_token="",spool_dir="",receipt_file=p)
    assert not result["ok"]
    assert "unknown outcome" in result["error"]

def test_rrbridge_profile_requires_guard_and_allowlist(monkeypatch):
    calls=[]
    def fake(url, **kwargs):
        calls.append(url)
        if url.endswith("/status"):
            return {"ready":True,"logging":False,"fileLogging":False,"guard":{"enabled":True}}
        return {"profiles":[{"name":"basic.xml","allowed":True}]}
    monkeypatch.setattr(s,"http_json",fake)
    s.validate_rrbridge_status("http://127.0.0.1:18765","",
                               "switch_profile","basic.xml","")
    assert len(calls)==2
    with pytest.raises(s.Refused):
        s.validate_rrbridge_status("http://127.0.0.1:18765","",
                                   "filelog_start","","")

import copy
import json
import pytest
from werewolf_sft.io import ROOT, read_jsonl, content_hash
from werewolf_sft.skill_diagnostic import (PACKET, validate_packet, validate_saved, execute)


@pytest.fixture
def frozen():
    spec = json.loads((ROOT / PACKET / "experiment.json").read_text(encoding="utf-8"))
    packet = read_jsonl(ROOT / PACKET / "inputs.jsonl")
    cases = [c for suite in ("rules", "strategy", "counterfactual", "blind")
             for c in read_jsonl(ROOT / f"eval/{suite}.jsonl") if c["split"] == "dev"]
    return spec, packet, cases


def test_frozen_packet_rejects_test_or_changed_prompt(frozen):
    spec, packet, cases = frozen
    validate_packet(spec, packet, cases)
    changed = copy.deepcopy(packet)
    changed[0]["split"] = "test"
    with pytest.raises(ValueError, match="test"):
        validate_packet(spec, changed, cases)
    changed = copy.deepcopy(packet)
    changed[0]["treatment_messages"][0]["content"] += " altered"
    with pytest.raises(ValueError, match="only skill_state"):
        validate_packet(spec, changed, cases)
    changed = copy.deepcopy(packet)
    changed[0]["treatment_messages"][1]["content"] += " changed task"
    with pytest.raises(ValueError, match="only skill_state"):
        validate_packet(spec, changed, cases)


def test_frozen_packet_rejects_duplicate_or_unknown_ids(frozen):
    spec, packet, cases = frozen
    changed = copy.deepcopy(packet)
    changed[-1] = changed[0]
    with pytest.raises(ValueError, match="IDs"):
        validate_packet(spec, changed, cases)


def fake_result():
    return {"raw_response": "{}", "truncated": False, "seconds": 0.0}


def test_resume_keeps_completed_bytes_and_skips_loading_when_done(tmp_path, frozen):
    spec, packet, cases = frozen
    count = 0
    def interrupted(*args):
        nonlocal count
        count += 1
        if count == 2:
            raise RuntimeError("interrupted")
        return fake_result()
    run = {"test_run": 1}
    args = (tmp_path, {}, spec, packet, cases, [], run)
    with pytest.raises(RuntimeError, match="interrupted"):
        execute(*args, loader=lambda *a: (None, None), generator=interrupted)
    first = tmp_path / "cases" / (packet[0]["id"] + ".json")
    saved = (first.read_bytes(), first.stat().st_mtime_ns)
    (tmp_path / "cases/orphan.pending").write_text("{")
    visited = []
    def remaining(model, tokenizer, messages, config):
        visited.append(messages)
        return fake_result()
    report = execute(*args, loader=lambda *a: (None, None), generator=remaining)
    assert len(visited) == 22 and packet[0]["treatment_messages"] not in visited
    assert report["treatment"]["status"] == "complete"
    assert (first.read_bytes(), first.stat().st_mtime_ns) == saved
    def forbidden(*a):
        raise AssertionError("completed runs must not load or generate")
    execute(*args, loader=forbidden, generator=forbidden)
    with pytest.raises(ValueError, match="fingerprint"):
        execute(tmp_path, {}, spec, packet, cases, [], {"changed": True}, loader=forbidden)


def test_truncation_is_preserved_and_never_retried(tmp_path, frozen):
    spec, packet, cases = frozen
    args = (tmp_path, {}, spec, packet, cases, [], {"test_run": 1})
    with pytest.raises(ValueError, match="truncation"):
        execute(*args, loader=lambda *a: (None, None),
                generator=lambda *a: {**fake_result(), "truncated": True})
    assert len(list((tmp_path / "cases").glob("*.json"))) == 1
    with pytest.raises(ValueError, match="truncated"):
        execute(*args, loader=lambda *a: pytest.fail("must not load"))


def test_resume_rejects_wrong_input_fingerprint_or_non_dev(frozen):
    _, packet, _ = frozen
    run = {"test_run": 1}
    pred = {"id": packet[0]["id"], "input_hash": "wrong", "run_fingerprint": content_hash(run), "truncated": False}
    with pytest.raises(ValueError, match="input differs"):
        validate_saved([pred], packet, run)
    pred["id"] = "eval-test-only"
    with pytest.raises(ValueError, match="non-dev"):
        validate_saved([pred], packet, run)

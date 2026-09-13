import copy
import json
import shutil
from collections import Counter

import pytest

from werewolf_sft.dataset import split_by_family
from werewolf_sft.evaluation import parse_response
from werewolf_sft.io import ROOT, sha256_file
from werewolf_sft.perspective import player_view, response_payload
from werewolf_sft.rule_repairs import visible_changes
from werewolf_sft.rules import action
from werewolf_sft.strategy_repairs import prepare_strategy_repair_batch, strategy_repair_batch
from werewolf_sft.validation import validate_dataset, validate_row


def test_strategy_updates_have_lawful_available_evidence():
    rows, pairs = strategy_repair_batch()
    assert len(rows) == 24 and len(pairs) == 12
    assert validate_dataset(rows) == []
    assert Counter(r["training_stage"] for r in rows) == {"strategy": 14, "tactics": 10}
    by_id = {r["id"]: r for r in rows}
    for pair in pairs:
        a, b = [by_id[i] for i in pair["members"]]
        before, after = a["public_info"]["events"], b["public_info"]["events"]
        assert after[:-1] == before
        assert pair["latest_evidence"] == after[-1]["id"]
        assert pair["latest_evidence"] not in a["evidence_ids"]
        assert pair["latest_evidence"] in b["evidence_ids"]
        assert a["private_info"] == b["private_info"]
        assert a["task"] == b["task"]  # Update is evidence, not a changed answer instruction.
        assert pair["changed_paths"] == visible_changes(player_view(a), player_view(b))
        assert set(pair["changed_paths"]) <= {"public_info.events", "public_info.alive"}
        assert a["analysis"] != b["analysis"] and a["strategy"] != b["strategy"]
        for r in (a, b):
            assert all(e["round"] <= r["round"] for e in r["public_info"]["events"])
            assert parse_response(json.dumps(response_payload(r))) == response_payload(r)
            assert not {"analysis", "action", "review", "tactical_tags"} & player_view(r).keys()
            assert not r["review"]["human_approved"]


def test_seer_update_retargets_without_fabricating_results():
    rows, _ = strategy_repair_batch()
    a, b = [r for r in rows if "seer_retarget" in r["id"]]
    assert a["action"] == action("check", 9) and b["action"] == action("check", 5)
    assert 9 in a["public_info"]["alive"] and 9 not in b["public_info"]["alive"]
    assert a["private_info"]["facts"] == b["private_info"]["facts"]
    assert [(f["target"], f["value"]) for f in b["private_info"]["facts"]] == [(7, "good")]
    assert a["public_response"] == b["public_response"] == ""
    stale = copy.deepcopy(b)
    stale["action"] = action("check", 9)
    assert "illegal target/action/phase/skill" in validate_row(stale)
    wrong_role = copy.deepcopy(a)
    wrong_role["role"] = "villager"
    assert validate_row(wrong_role)


def test_wolf_private_team_is_not_published_or_mistaken_for_good_evidence():
    rows, _ = strategy_repair_batch()
    for r in rows:
        if r["role"] != "werewolf":
            continue
        assert r["seat"] == 9
        assert {f["target"] for f in r["private_info"]["facts"] if f["kind"] == "wolf_team"} == {3, 6, 10}
        assert {f["kind"] for f in r["private_info"]["facts"]} == {"wolf_team"}
        assert r["action"] == action("speak") and r["public_response"]
        for secret in ("队友", "狼队", "我是狼", "3、6、10", "私有"):
            assert secret not in r["public_response"]
    # This is a syntax/private-fact gate, not a substitute for semantic review.


def test_strategy_families_keep_siblings_and_related_wolf_examples_together():
    rows, pairs = strategy_repair_batch()
    train, val = split_by_family(rows)
    assert len(train) == 20 and len(val) == 4
    assert {r["scenario_id"] for r in train}.isdisjoint({r["scenario_id"] for r in val})
    for group in (train, val):
        ids = {r["id"] for r in group}
        assert all(len(ids.intersection(p["members"])) in (0, 2) for p in pairs)
    binding = [r for r in rows if r["scenario_id"] == "v02-strategy-wolf_binding"]
    assert len(binding) == 6
    assert all(r in train for r in binding) or all(r in val for r in binding)


def test_strategy_snapshot_resumes_and_protects_both_previous_versions(tmp_path):
    manifests = ["data/versions/dataset_v0.1.json",
                 "data/candidates/dataset_v0.2/rules_batch_v0.1/manifest.json"]
    paths = set(manifests + ["reports/dev_semantic_review_v01.json"])
    for relative in manifests:
        paths.update(json.loads((ROOT / relative).read_text(encoding="utf-8"))["files"])
    for relative in paths:
        dest = tmp_path / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, dest)
    before = {p: (sha256_file(tmp_path / p), (tmp_path / p).stat().st_mtime_ns) for p in paths}
    manifest = prepare_strategy_repair_batch(tmp_path)
    assert manifest["protected_files_verified"] == 23
    assert manifest["ready_for_training"] is False
    candidate = tmp_path / "data/candidates/dataset_v0.2/strategy_batch_v0.1"
    stamps = {p: (sha256_file(p), p.stat().st_mtime_ns) for p in candidate.iterdir()}
    assert prepare_strategy_repair_batch(tmp_path) == manifest
    assert all((sha256_file(p), p.stat().st_mtime_ns) == s for p, s in stamps.items())
    missing = candidate / "validation.jsonl"
    missing.unlink()
    prepare_strategy_repair_batch(tmp_path)
    assert sha256_file(missing) == stamps[missing][0]
    assert all((sha256_file(p), p.stat().st_mtime_ns) == s for p, s in stamps.items() if p != missing)
    assert {p: (sha256_file(tmp_path / p), (tmp_path / p).stat().st_mtime_ns) for p in paths} == before
    assert not (tmp_path / "data/versions/dataset_v0.2.json").exists()
    assert not (tmp_path / "data/prepared/dataset_v0.2").exists()
    (candidate / "samples.jsonl").write_text("corrupt\n", encoding="utf-8")
    missing.unlink()
    with pytest.raises(ValueError, match="immutable snapshot differs"):
        prepare_strategy_repair_batch(tmp_path)
    assert not missing.exists()  # All existing members are checked before repairing any gap.
    protected_rule = tmp_path / "data/candidates/dataset_v0.2/rules_batch_v0.1/rules.jsonl"
    protected_rule.write_text("changed\n", encoding="utf-8")
    with pytest.raises(ValueError, match="dataset snapshot missing or changed"):
        prepare_strategy_repair_batch(tmp_path)
    assert not missing.exists()

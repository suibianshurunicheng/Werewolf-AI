import copy
import json
import shutil

import pytest

from werewolf_sft.dataset import split_by_family
from werewolf_sft.evaluation import parse_response
from werewolf_sft.io import ROOT, sha256_file
from werewolf_sft.perspective import player_view, response_payload
from werewolf_sft.rule_repairs import prepare_rule_repair_batch, rule_repair_batch, visible_changes
from werewolf_sft.rules import action, winner
from werewolf_sft.validation import validate_dataset, validate_row


def test_rule_repair_labels_and_visibility():
    rows, pairs = rule_repair_batch()
    assert validate_dataset(rows) == []
    by_id = {r["id"]: r for r in rows}
    expected = {
        "guard_repeat": (action("pass"), action("guard", 6)),
        "guard_empty_break": (action("guard", 2), action("pass")),
        "hunter_permission": (action("pass"), action("shoot", 9)),
        "hunter_spent": (action("shoot", 9), action("pass")),
        "hunter_late_round": (action("shoot", 9), action("shoot", 9)),
        "witch_poison_stock": (action("pass"), action("poison", 7)),
        "witch_current_target": (action("heal", 5), action("heal", 8)),
        "witch_self_round": (action("heal", 2), action("pass")),
        "witch_one_potion": (action("poison", 7), action("pass")),
        "sheriff_registration": (action("vote", 7), action("pass")),
        "vote_living_target": (action("vote", 7), action("pass")),
        "role_skill": (action("check", 11), action("pass")),
        "public_boundary": (action("check", 11), action("speak")),
        "victory_villagers": (action("speak"), action("speak")),
        "victory_gods": (action("speak"), action("speak")),
        "victory_no_wolves": (action("speak"), action("speak")),
    }
    assert len(rows) == 32 and len(pairs) == 16
    for pair in pairs:
        a, b = [by_id[i] for i in pair["members"]]
        assert (a["action"], b["action"]) == expected[pair["id"]]
        assert pair["changed_paths"] == visible_changes(player_view(a), player_view(b))
        assert pair["changed_paths"] and a["scenario_id"] == b["scenario_id"]
        # Time-shifted self-heal must also move the lawful knife notice, not use stale information.
        if pair["id"] == "witch_self_round":
            assert set(pair["changed_paths"]) == {"round", "private_info.facts.0.round"}
        else:
            assert len(pair["changed_paths"]) == 1
    for row in rows:
        assert parse_response(json.dumps(response_payload(row))) == response_payload(row)
        assert row["board"] == "classic_12" and row["dataset_version"] == "dataset_v0.2"
        assert not row["review"]["human_approved"]
        if row["stage"] == "night":
            assert row["public_response"] == ""
        assert not {"analysis", "action", "tactical_tags", "review", "scenario_id"} & player_view(row).keys()


def test_rule_repair_groups_do_not_split_counterparts():
    rows, pairs = rule_repair_batch()
    train, val = split_by_family(rows)
    assert len(train) + len(val) == len(rows) and train and val
    assert {r["scenario_id"] for r in train}.isdisjoint({r["scenario_id"] for r in val})
    for group in (train, val):
        ids = {r["id"] for r in group}
        for pair in pairs:
            assert len(ids.intersection(pair["members"])) in (0, 2)


def test_rule_repair_rejects_wrong_role_or_stale_knife():
    rows, _ = rule_repair_batch()
    by_id = {r["id"]: r for r in rows}
    guard = copy.deepcopy(by_id["v02-rule-guard_repeat-b"])
    guard["action"] = action("check", 6)
    assert "illegal target/action/phase/skill" in validate_row(guard)
    witch = copy.deepcopy(by_id["v02-rule-witch_current_target-b"])
    witch["private_info"]["facts"][0]["round"] -= 1
    assert "illegal target/action/phase/skill" in validate_row(witch)


def test_victory_hypotheses_are_not_current_player_truth():
    rows, _ = rule_repair_batch()
    counts = [(4, 3, 1, None), (4, 0, 4, "wolves"), (2, 3, 1, None),
              (2, 4, 0, "wolves"), (1, 2, 2, None), (0, 2, 2, "good")]
    victory_rows = [r for r in rows if "victory_" in r["id"]]
    for row, (wolves, villagers, gods, expected) in zip(victory_rows, counts):
        roles = dict(enumerate(["werewolf"] * wolves + ["villager"] * villagers
                              + ["seer", "witch", "hunter", "guard"][:gods], 1))
        assert winner(roles, list(roles)) == expected
        assert f"{wolves}狼、{villagers}民、{gods}神" in row["task"]
        assert "假设" in row["task"] and "不是本局真实底牌" in row["task"]
        assert row["private_info"]["facts"] == []
        assert row["public_info"]["alive"] == list(range(1, 13))


def test_candidate_resume_preserves_frozen_data_and_rejects_edits(tmp_path):
    frozen = "data/versions/dataset_v0.1.json"
    original = json.loads((ROOT / frozen).read_text(encoding="utf-8"))
    paths = list(original["files"]) + [frozen, "reports/dev_semantic_review_v01.json"]
    for relative in paths:
        dest = tmp_path / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, dest)
    before = {p: sha256_file(tmp_path / p) for p in paths}
    result = prepare_rule_repair_batch(tmp_path)
    assert result["ready_for_training"] is False
    assert not (tmp_path / "data/versions/dataset_v0.2.json").exists()
    assert not (tmp_path / "data/prepared/dataset_v0.2").exists()
    candidate = tmp_path / "data/candidates/dataset_v0.2/rules_batch_v0.1"
    stamps = {p: p.stat().st_mtime_ns for p in candidate.iterdir()}
    assert prepare_rule_repair_batch(tmp_path) == result
    assert all(p.stat().st_mtime_ns == stamp for p, stamp in stamps.items())
    # Interrupted output is completed without touching existing members.
    missing = candidate / "validation.jsonl"
    missing.unlink()
    prepare_rule_repair_batch(tmp_path)
    assert all(p.stat().st_mtime_ns == stamp for p, stamp in stamps.items() if p != missing)
    assert {p: sha256_file(tmp_path / p) for p in paths} == before
    (candidate / "rules.jsonl").write_text("corrupt\n", encoding="utf-8")
    with pytest.raises(ValueError, match="immutable snapshot differs"):
        prepare_rule_repair_batch(tmp_path)
    # Edited v0.1 is rejected before any new component files can be written.
    (tmp_path / next(iter(original["files"]))).write_text("changed\n", encoding="utf-8")
    with pytest.raises(ValueError, match="dataset snapshot missing or changed"):
        prepare_rule_repair_batch(tmp_path)

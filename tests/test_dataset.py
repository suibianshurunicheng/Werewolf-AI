import copy
import json

import pytest

from werewolf_sft.benchmark_data import build_benchmark
from werewolf_sft.dataset import prepare_stage, save_snapshot, split_by_family
from werewolf_sft.io import ROOT, read_jsonl
from werewolf_sft.perspective import player_view, render_input
from werewolf_sft.seed_data import TACTICS, rule_samples, strategy_samples, wolf_tactics
from werewolf_sft.validation import assert_disjoint, validate_dataset


def test_full_seed_validation():
    rows = rule_samples() + strategy_samples() + wolf_tactics()
    assert len(rows) > 180
    assert validate_dataset(rows) == []


def test_tactics_have_five_conditions():
    rows = wolf_tactics()
    assert len(TACTICS) == 25
    for tag, *_ in TACTICS:
        assert {r["tactical_tags"][1] for r in rows if r["tactical_tags"][0] == tag} == {
            "正确使用", "错误使用", "被识破", "对方反制", "调整策略"}


def test_scenario_family_split():
    train, val = split_by_family(wolf_tactics())
    assert {r["scenario_id"] for r in train}.isdisjoint({r["scenario_id"] for r in val})


def test_phase1_rejects_mirror():
    rows = rule_samples()
    rows[0]["board"] = "mirror_12"
    with pytest.raises(ValueError, match="classic_12"):
        prepare_stage(rows)


def test_immutable_snapshot(tmp_path):
    first, second = tmp_path / "a.json", tmp_path / "b.json"
    save_snapshot({first: "one"})
    stamp = first.stat().st_mtime_ns
    save_snapshot({first: "one", second: "two"})
    assert first.stat().st_mtime_ns == stamp
    with pytest.raises(ValueError, match="immutable"):
        save_snapshot({first: "changed", second: "changed"})
    assert second.read_text() == "two"


def visible_diff(a, b, path=""):
    if isinstance(a, dict) and isinstance(b, dict):
        return [p for key in a for p in visible_diff(a[key], b[key], (path + "." + key).strip("."))]
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [p for i in range(len(a)) for p in visible_diff(a[i], b[i], f"{path}.{i}")]
    return [] if a == b else [path]


def test_evaluation_is_independent_and_valid():
    suites = build_benchmark()
    rows = [c["scenario"] for cases in suites.values() for c in cases]
    assert validate_dataset(rows) == []
    assert_disjoint(rule_samples() + strategy_samples() + wolf_tactics(), rows)
    assert set(suites) == {"rules", "strategy", "counterfactual", "blind"}


def test_counterfactual_one_visible_variable():
    pairs = {}
    for case in build_benchmark()["counterfactual"]:
        pairs.setdefault(case["pair_id"], []).append(case)
    for pair in pairs.values():
        assert len(pair) == 2
        a, b = pair
        assert visible_diff(player_view(a["scenario"]), player_view(b["scenario"])) == [a["changed_path"]]
        assert a["expected"]["actions"] != b["expected"]["actions"]


def test_blind_prompts_have_no_annotations():
    for case in build_benchmark()["blind"]:
        text = render_input(case["scenario"])
        assert "tactical_tags" not in text and "expected" not in text
        assert not any(hint in text for hint in ["建议倒钩", "考虑悍跳", "你可以狼踩狼", "建议卖队友"])


def test_disk_snapshot_matches_generator():
    rows = read_jsonl(ROOT / "data/gold/dataset_v0.1/rules.jsonl")
    assert len(rows) == len(rule_samples())
    manifest = json.loads((ROOT / "data/versions/dataset_v0.1.json").read_text(encoding="utf-8"))
    assert manifest["counts"]["tactics"] == 125

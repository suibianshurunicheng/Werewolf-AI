import copy
import json

import pytest

from werewolf_sft.io import ROOT, read_jsonl, write_jsonl
from werewolf_sft.perspective import player_view, project_events, render_input, to_messages
from werewolf_sft.rules import action, legal_actions, settle_night, winner, hunter_permission, tally_votes
from werewolf_sft.schema import new_sample, add_fact
from werewolf_sft.validation import validate_row, validate_dataset, assert_disjoint, require_silver_reviews


def test_schema_and_example():
    row = json.loads((ROOT / "data/examples/player_sample.json").read_text(encoding="utf-8"))
    assert validate_row(row) == []
    assert len(row["private_info"]["facts"]) == 3


@pytest.mark.parametrize("role", ["werewolf", "villager", "seer", "witch", "hunter", "guard"])
def test_minimum_row(role):
    assert validate_row(new_sample("valid", role=role)) == []


def test_jsonl_strict(tmp_path):
    path = tmp_path / "rows.jsonl"
    row = new_sample("one")
    write_jsonl(path, [row])
    assert read_jsonl(path) == [row]
    path.write_text("{}\n\n", encoding="utf-8")
    with pytest.raises(ValueError, match="empty JSONL"):
        read_jsonl(path)


def test_hidden_labels_never_export():
    row = new_sample("one")
    row["hidden_info"] = {"all_roles": "SECRET_TRUTH"}
    row["tactical_tags"] = ["SECRET_TACTIC"]
    assert "SECRET" not in render_input(row)
    assert "hidden_info" not in player_view(row)
    assert validate_row(row)


def test_teacher_visibility():
    events = [{"visibility": "public", "payload": "speech"},
              {"visibility": [7], "payload": "team"}, {"visibility": [0], "payload": "truth"}]
    assert project_events(events, 3) == ["speech"]
    assert project_events(events, 7) == ["speech", "team"]
    with pytest.raises(ValueError):
        project_events([{"payload": "no audience"}], 3)


def test_villager_cannot_see_wolves():
    row = new_sample("leak")
    add_fact(row, "wolf_team", 5, "werewolf")
    assert any("unauthorized" in e for e in validate_row(row))


def test_seer_gets_alignment_only():
    row = new_sample("seer", role="seer")
    row["skill_state"]["checked_seats"] = [5]
    add_fact(row, "check_result", 5, "witch")
    assert any("result type" in e for e in validate_row(row))
    row["private_info"]["facts"][0]["value"] = "good"
    assert not validate_row(row)


def test_future_fact_fails():
    row = new_sample("future", role="werewolf")
    add_fact(row, "wolf_team", 5, "werewolf", round_no=2)
    assert any("future" in e for e in validate_row(row))


def test_unknown_private_field_fails():
    row = new_sample("unknown")
    row["private_info"]["all_roles"] = {"5": "werewolf"}
    assert validate_row(row)


def test_messages_separate_private_public():
    row = new_sample("one")
    messages = to_messages(row)
    assert [m["role"] for m in messages] == ["system", "user", "assistant"]
    answer = json.loads(messages[-1]["content"])
    assert answer["analysis"] != answer["public_response"]
    assert row["strategy"] not in messages[1]["content"]
    assert len(to_messages(row, include_answer=False)) == 2


@pytest.mark.parametrize("name", ["classic_day", "classic_sheriff", "classic_night", "vote", "seer", "witch", "hunter", "guard"])
def test_prompts(name):
    text = (ROOT / f"prompts/{name}.md").read_text(encoding="utf-8")
    for field in ["【板子】", "【我的座位】", "【我的私有信息】", "【历史发言】", "【当前任务】"]:
        assert field in text
    assert "ww-v1.0" in text


def test_guard_cannot_repeat():
    row = new_sample("guard", role="guard", stage="night", round_no=2)
    row["skill_state"]["last_guard_target"] = 5
    assert action("guard", 5) not in legal_actions(row)
    assert action("guard", row["seat"]) in legal_actions(row)


def test_witch_self_save_first_night_only():
    row = new_sample("witch", role="witch", stage="night")
    row["skill_state"]["antidote_available"] = True
    add_fact(row, "witch_knife", row["seat"], "attacked")
    assert action("heal", row["seat"]) in legal_actions(row)
    row["round"] = 2
    row["private_info"]["facts"][0]["round"] = 2
    assert action("heal", row["seat"]) not in legal_actions(row)
    row["skill_state"]["potion_used_tonight"] = True
    row["skill_state"]["poison_available"] = True
    assert not any(a["type"] in {"heal", "poison"} for a in legal_actions(row))


def test_spent_antidote_cannot_see_new_knife():
    row = new_sample("witch", role="witch", stage="night")
    add_fact(row, "witch_knife", 7, "attacked")
    assert any("antidote spent" in e for e in validate_row(row))


@pytest.mark.parametrize("kwargs,expected", [
    ({"knives": [5], "guarded": 5}, {}),
    ({"knives": [5], "healed": 5}, {}),
    ({"knives": [5], "guarded": 5, "healed": 5}, {5: ["guard_heal_conflict"]}),
    ({"knives": [5], "poisons": [5], "guarded": 5}, {5: ["poison"]}),
    ({"poisons": [5], "healed": 5}, {5: ["poison"]}),
])
def test_night_settlement(kwargs, expected):
    assert settle_night(**kwargs) == expected


def test_hunter_poison_and_death_phase():
    assert not hunter_permission(["knife", "poison"])
    assert hunter_permission(["knife"])
    row = new_sample("hunter", role="hunter", stage="hunter_shot")
    row["skill_state"]["hunter_can_shoot"] = True
    assert action("shoot", 5) not in legal_actions(row)
    row["public_info"]["alive"].remove(row["seat"])
    assert action("shoot", 5) in legal_actions(row)
    row["skill_state"]["shot_used"] = True
    assert action("shoot", 5) not in legal_actions(row)


def test_edge_win_not_parity():
    roles = {1: "werewolf", 2: "werewolf", 3: "villager", 4: "seer"}
    assert winner(roles, [1, 2, 3, 4]) is None
    assert winner(roles, [1, 2, 4]) == "wolves"
    assert winner(roles, [3, 4]) == "good"
    assert winner(roles, [1, 2, 4], pending_shots=True) is None


def test_sheriff_votes_and_withdrawn():
    assert tally_votes({1: 5, 2: 6}, sheriff=1) == [5]
    assert tally_votes({1: 5, 2: 6}, sheriff=1, election=True) == [5, 6]
    row = new_sample("election", stage="sheriff_vote")
    row["public_info"].update(candidates=[5], sheriff_registered=[3, 5])
    assert action("vote", 5) not in legal_actions(row)


def test_duplicate_and_cross_split():
    row = new_sample("one")
    assert any("duplicate" in e for e in validate_dataset([row, row]))
    with pytest.raises(ValueError, match="contamination"):
        assert_disjoint([row], [copy.deepcopy(row)])


def test_silver_cannot_self_approve():
    with pytest.raises(ValueError):
        require_silver_reviews(new_sample("one"))


def test_invalid_action_type_or_skill():
    row = new_sample("villager", stage="night")
    row["action"] = action("poison", 5)
    assert any("illegal" in e for e in validate_row(row))
    row["skill_state"]["poison_available"] = True
    assert any("unauthorized poison" in e for e in validate_row(row))

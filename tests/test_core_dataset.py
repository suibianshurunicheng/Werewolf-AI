import copy
import json
import shutil

import pytest

from werewolf_sft.classic_messages import classic_messages, FORBIDDEN
from werewolf_sft.core_dataset import COMPONENTS, coverage, freeze_core, load_core, require_core_source
from werewolf_sft.core_supplement import supplement
from werewolf_sft.dataset import split_by_family
from werewolf_sft.io import ROOT, sha256_file
from werewolf_sft.perspective import response_payload
from werewolf_sft.validation import validate_dataset


def test_core_coverage_and_autonomous_actions():
    rows, provenance = load_core(ROOT)
    assert len(rows) == len(provenance) == 86
    assert validate_dataset(rows) == [] and not coverage(rows)["missing"]
    train, val = split_by_family(rows)
    assert {r["scenario_id"] for r in train}.isdisjoint({r["scenario_id"] for r in val})
    autonomous = supplement()
    assert len({r["task"] for r in autonomous}) == 1
    assert {r["action"]["type"] for r in autonomous} >= {"speak", "vote", "check", "guard", "knife", "pass", "heal"}
    assert all(r["round"] == 1 for r in autonomous if r["stage"] == "sheriff_vote")
    assert all(r["public_response"] == "" for r in rows if r["stage"] == "night")


def test_core_rejects_video_sources_and_unknown_lineage():
    row = supplement()[0]
    require_core_source(row)
    for patch in ({"kind": "licensed_match"}, {"reference_urls": ["https://www.bilibili.com/video/example"]},
                  {"author": "video_distilled_v0.1"}, {"author": "ASR transcript"}):
        invalid = copy.deepcopy(row)
        invalid["source"].update(patch)
        with pytest.raises(ValueError):
            require_core_source(invalid)
    invalid = copy.deepcopy(row)
    invalid["id"] = "video-M01"
    with pytest.raises(ValueError):
        require_core_source(invalid)
    assert not any("video" in p for p in COMPONENTS)


def test_classic_messages_exclude_annotation_and_extension_fields():
    for row in load_core(ROOT)[0]:
        messages = classic_messages(row)
        assert [m["role"] for m in messages] == ["system", "user", "assistant"]
        user = json.loads(messages[1]["content"])
        assert not {"source", "review", "analysis", "action", "tactical_tags", "scenario_id"} & user.keys()
        assert json.loads(messages[2]["content"]) == response_payload(row)
        assert all(x not in json.dumps(messages, ensure_ascii=False) for x in FORBIDDEN)
    bad = supplement()[0]
    bad["public_info"]["events"][0]["text"] = "狼美人连人"
    with pytest.raises(ValueError, match="non-Classic"):
        classic_messages(bad)


def test_core_freeze_reuses_files_and_rejects_review_changes(tmp_path):
    old = json.loads((ROOT / "data/versions/dataset_v0.1.json").read_text(encoding="utf-8"))
    paths = set(old["files"]) | {"data/versions/dataset_v0.1.json", "reports/dataset_v02_core_review.json"}
    for component in COMPONENTS:
        manifest_path = f"data/candidates/dataset_v0.2/{component}/manifest.json"
        paths.add(manifest_path)
        paths.update(json.loads((ROOT / manifest_path).read_text(encoding="utf-8"))["files"])
    for name in paths:
        destination = tmp_path / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, destination)
    first = freeze_core(tmp_path)
    files = [tmp_path / p for p in first["files"]] + [tmp_path / "data/versions/dataset_v0.2.json"]
    before = {p: (sha256_file(p), p.stat().st_mtime_ns) for p in files}
    assert freeze_core(tmp_path) == first
    assert all((sha256_file(p), p.stat().st_mtime_ns) == v for p, v in before.items())
    missing = files[0]
    missing.unlink()
    freeze_core(tmp_path)
    assert sha256_file(missing) == before[missing][0]
    assert all((sha256_file(p), p.stat().st_mtime_ns) == v for p, v in before.items() if p != missing)
    review_path = tmp_path / "reports/dataset_v02_core_review.json"
    review = json.loads(review_path.read_text(encoding="utf-8"))
    review["items"][0]["row_sha256"] = "0" * 64
    review_path.write_text(json.dumps(review), encoding="utf-8")
    with pytest.raises(ValueError, match="unreviewed"):
        freeze_core(tmp_path)

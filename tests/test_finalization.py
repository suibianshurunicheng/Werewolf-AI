import importlib.util
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import finalize_training as module
from werewolf_sft.io import write_json, sha256_file
from werewolf_sft.training import mark_checkpoint_complete


def fixture(tmp_path, monkeypatch, step=2):
    monkeypatch.setattr(module, "ROOT", tmp_path)
    run = tmp_path / "outputs/test"
    checkpoint = run / f"checkpoint-{step}"
    checkpoint.mkdir(parents=True)
    manifest = {"stage": "tactics", "effective_schedule": {"optimizer_steps": 2}}
    write_json(run / "run_manifest.json", manifest)
    write_json(checkpoint / "run_manifest.json", manifest)
    write_json(checkpoint / "trainer_state.json", {"global_step": step, "max_steps": 2, "epoch": 1,
        "best_model_checkpoint": str(checkpoint), "best_metric": 1.5,
        "log_history": [{"step": step, "eval_loss": 1.5}]})
    for name in ["adapter_model.safetensors", "adapter_config.json", "tokenizer_config.json",
                 "tokenizer.json", "optimizer.pt", "scheduler.pt"]:
        (checkpoint / name).write_bytes(b"test fixture")
    mark_checkpoint_complete(checkpoint)
    return run, checkpoint


def test_completed_export_is_idempotent_and_preserves_checkpoint(tmp_path, monkeypatch):
    run, cp = fixture(tmp_path, monkeypatch)
    before = {p.name: sha256_file(p) for p in cp.iterdir()}
    result = module.finalize(run)
    assert result["peak_vram_mib"] is None
    assert result["global_step"] == 2
    assert module.finalize(run) == result
    assert not (run / "final/optimizer.pt").exists()
    assert before == {p.name: sha256_file(p) for p in cp.iterdir()}
    assert (run / "final/adapter_model.safetensors").read_bytes() == b"test fixture"


def test_rejects_incomplete_training(tmp_path, monkeypatch):
    run, _ = fixture(tmp_path, monkeypatch, step=1)
    with pytest.raises(ValueError, match="not complete"):
        module.finalize(run)


def test_rejects_corrupt_checkpoint(tmp_path, monkeypatch):
    run, cp = fixture(tmp_path, monkeypatch)
    (cp / "adapter_model.safetensors").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="no complete"):
        module.finalize(run)


def test_refuses_conflicting_final(tmp_path, monkeypatch):
    run, _ = fixture(tmp_path, monkeypatch)
    (run / "final").mkdir()
    (run / "final/adapter_model.safetensors").write_bytes(b"other adapter")
    with pytest.raises(ValueError, match="refuse overwrite"):
        module.finalize(run)

import copy
import json

import pytest

from werewolf_sft.config import load_config, validate_config
from werewolf_sft.encoding import encode_messages, encode_rows, SequenceTooLong
from werewolf_sft.evaluation import parse_response, score_case, summarize, comparison
from werewolf_sft.io import ROOT
from werewolf_sft.perspective import response_payload
from werewolf_sft.runtime import load_cases, prepare_journal, append_prediction, protocol


def test_all_saved_configs_load():
    for path in (ROOT / "configs").glob("*.yaml"):
        load_config(path)


@pytest.mark.parametrize("change", [
    lambda c: c["training"].update(batch_size=2),
    lambda c: c["data"].update(board="mirror_maze_12"),
    lambda c: c["data"].update(overlength="truncate"),
    lambda c: c["training"].update(output_root="../outside"),
    lambda c: c["lora"].update(rnak=8),
])
def test_unsafe_or_misspelled_config_rejected(change):
    config = load_config(ROOT / "configs/qlora_classic.yaml")
    change(config)
    with pytest.raises(ValueError):
        validate_config(config)


def test_config_cycle(tmp_path):
    (tmp_path / "a.yaml").write_text("extends: b.yaml")
    (tmp_path / "b.yaml").write_text("extends: a.yaml")
    with pytest.raises(ValueError, match="cyclic"):
        load_config(tmp_path / "a.yaml")


class CharacterTokenizer:
    def apply_chat_template(self, messages, tokenize, add_generation_prompt, **kwargs):
        return "".join(m["role"] + ":" + m["content"] + "\n" for m in messages) + (
            "assistant:" if add_generation_prompt else "")

    def __call__(self, text, **kwargs):
        return {"input_ids": list(text.encode("utf-8"))}


def test_prompt_mask_and_no_truncation():
    messages = [{"role": r, "content": c} for r, c in [
        ("system", "规则"), ("user", "局面"), ("assistant", "答案")]]
    encoded = encode_messages(CharacterTokenizer(), messages, 1000)
    supervised = bytes(t for t in encoded["labels"] if t != -100).decode("utf-8")
    assert supervised == "答案\n"
    with pytest.raises(SequenceTooLong):
        encode_messages(CharacterTokenizer(), messages, 10)
    with pytest.raises(ValueError, match="empty"):
        encode_rows(CharacterTokenizer(), [{"id": "long", "messages": messages}], 10, "filter")


def test_broken_chat_prefix_rejected():
    class Broken(CharacterTokenizer):
        def apply_chat_template(self, *args, **kwargs):
            return "different" if kwargs["add_generation_prompt"] else "answer"
    with pytest.raises(ValueError, match="prefix"):
        encode_messages(Broken(), [{"role": r} for r in ("system", "user", "assistant")], 100)


def test_atomic_case_resume_and_mixed_run(tmp_path):
    run = {"revision": "abc", "generation": {"max_new_tokens": 768}}
    assert prepare_journal(tmp_path, run) == []
    prediction = {"id": "test-1", "raw_response": "完整"}
    append_prediction(tmp_path, prediction)
    original = (tmp_path / "cases/test-1.json").stat().st_mtime_ns
    append_prediction(tmp_path, prediction)
    assert (tmp_path / "cases/test-1.json").stat().st_mtime_ns == original
    (tmp_path / "cases/test-2.pending").write_text("{")
    assert prepare_journal(tmp_path, run) == [prediction]
    with pytest.raises(ValueError, match="fingerprint"):
        prepare_journal(tmp_path, {"revision": "changed"})
    with pytest.raises(ValueError, match="changing"):
        append_prediction(tmp_path, {"id": "test-1", "raw_response": "changed"})
    with pytest.raises(ValueError, match="unsafe"):
        append_prediction(tmp_path, {"id": "../../outside"})


def test_evaluation_denominators_and_json_errors():
    cases = load_cases(load_config(ROOT / "configs/qlora_classic.yaml"))
    case = cases[0]
    payload = response_payload(case["scenario"])
    raw = json.dumps(payload)
    assert parse_response(raw) == payload
    assert score_case(case, raw)["action_legal"]
    assert not score_case(case, raw, truncated=True)["format_valid"]
    summary = summarize(cases, [{"id": case["id"], "raw_response": raw}])
    assert summary["status"] == "partial"
    assert summary["metrics"]["rules"]["total"] == 12
    assert summary["metrics"]["rules"]["format_valid_rate"] == pytest.approx(1 / 12)
    payload["identity_reads"] = [{"seat": True, "assessment": "未知", "confidence": 0.5}]
    with pytest.raises(ValueError):
        parse_response(json.dumps(payload))
    with pytest.raises(ValueError, match="unknown"):
        summarize(cases, [{"id": "missing", "raw_response": raw}])
    with pytest.raises(ValueError, match="duplicate"):
        summarize(cases, [{"id": case["id"]}] * 2)


def test_generation_changes_invalidate_comparison():
    config = load_config(ROOT / "configs/qlora_classic.yaml")
    cases = load_cases(config)
    old = protocol(config, cases)
    config["inference"]["max_new_tokens"] += 1
    assert protocol(config, cases) != old
    with pytest.raises(ValueError, match="protocol"):
        comparison({"protocol_fingerprint": "old"}, {"protocol_fingerprint": "new"})


def test_selected_completion_loss_and_gradients_match_standard():
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    from werewolf_sft.training import completion_loss
    torch.manual_seed(42)
    cfg = transformers.Qwen3Config(vocab_size=97, hidden_size=32, intermediate_size=48,
        num_hidden_layers=1, num_attention_heads=4, num_key_value_heads=2,
        head_dim=8, attention_dropout=0.0)
    model = transformers.Qwen3ForCausalLM(cfg).float().eval()
    reference = copy.deepcopy(model)
    inputs = {"input_ids": torch.randint(0, 97, (2, 43)), "attention_mask": torch.ones((2, 43), dtype=torch.long)}
    inputs["labels"] = inputs["input_ids"].clone()
    inputs["labels"][0, :7] = -100
    inputs["labels"][1, :11] = -100
    inputs["labels"][1, -3:] = -100
    inputs["attention_mask"][1, -3:] = 0
    standard = reference(**inputs, use_cache=False).loss
    optimized, _ = completion_loss(model, inputs)
    assert torch.allclose(standard, optimized, atol=1e-6)
    standard.backward()
    optimized.backward()
    for a, b in zip(reference.parameters(), model.parameters()):
        assert torch.allclose(a.grad, b.grad, atol=1e-6), "completion-only gradient differs"


def test_tiny_lora_checkpoint_roundtrip(tmp_path):
    torch = pytest.importorskip("torch")
    transformers = pytest.importorskip("transformers")
    peft = pytest.importorskip("peft")
    from werewolf_sft.training import completion_loss
    cfg = transformers.Qwen3Config(vocab_size=97, hidden_size=32, intermediate_size=48,
        num_hidden_layers=1, num_attention_heads=4, num_key_value_heads=2, head_dim=8)
    base = transformers.Qwen3ForCausalLM(cfg)
    original = copy.deepcopy(base)
    model = peft.get_peft_model(base, peft.LoraConfig(task_type="CAUSAL_LM", r=2,
        lora_alpha=4, target_modules=["q_proj", "v_proj"], lora_dropout=0.0))
    inputs = {"input_ids": torch.tensor([[3, 4, 5, 6, 7]]), "attention_mask": torch.ones(1, 5, dtype=torch.long),
              "labels": torch.tensor([[-100, -100, 5, 6, 7]])}
    optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=0.01)
    loss, _ = completion_loss(model, inputs)
    loss.backward()
    optimizer.step()
    model.save_pretrained(tmp_path)
    loaded = peft.PeftModel.from_pretrained(original, tmp_path, is_trainable=True)
    model.eval()
    loaded.eval()
    assert torch.allclose(model(input_ids=inputs["input_ids"]).logits,
                          loaded(input_ids=inputs["input_ids"]).logits, atol=1e-6)
    assert any(p.requires_grad and "lora_" in name for name, p in loaded.named_parameters())

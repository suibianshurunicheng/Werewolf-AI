"""Chat-template faithful assistant-only SFT, with explicit length failures."""
from __future__ import annotations


class SequenceTooLong(ValueError):
    pass


def encode_messages(tokenizer, messages, max_length):
    if [m["role"] for m in messages] != ["system", "user", "assistant"]:
        raise ValueError("expected one complete system/user/assistant turn")
    prefix = tokenizer.apply_chat_template(messages[:-1], tokenize=False, add_generation_prompt=True,
                                           enable_thinking=False)
    full = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=False,
                                         enable_thinking=False)
    if not full.startswith(prefix):
        raise ValueError("chat template assistant prefix mismatch; refusing incorrect label masking")
    prompt_ids = tokenizer(prefix, add_special_tokens=False)["input_ids"]
    input_ids = tokenizer(full, add_special_tokens=False)["input_ids"]
    if input_ids[:len(prompt_ids)] != prompt_ids:
        raise ValueError("token boundary mismatch at assistant prefix")
    if len(input_ids) > max_length:
        raise SequenceTooLong(f"sample length {len(input_ids)} exceeds {max_length}")
    labels = [-100] * len(prompt_ids) + input_ids[len(prompt_ids):]
    if not any(label != -100 for label in labels):
        raise ValueError("no assistant supervision tokens")
    return {"input_ids": input_ids, "attention_mask": [1] * len(input_ids), "labels": labels}


def encode_rows(tokenizer, rows, max_length, overlength="reject"):
    features, rejected = [], []
    for row in rows:
        try:
            features.append(encode_messages(tokenizer, row["messages"], max_length))
        except SequenceTooLong as exc:
            rejected.append({"id": row["id"], "reason": str(exc)})
    if rejected and overlength == "reject":
        raise SequenceTooLong(f"{len(rejected)} overlength rows; first={rejected[0]}")
    if not features:
        raise ValueError("no samples fit; never train an empty dataset")
    return features, rejected


class SFTCollator:
    def __init__(self, pad_id):
        self.pad_id = pad_id

    def __call__(self, features):
        import torch
        size = max(len(row["input_ids"]) for row in features)
        pad_values = {"input_ids": self.pad_id, "attention_mask": 0, "labels": -100}
        return {key: torch.tensor([row[key] + [pad] * (size - len(row[key])) for row in features])
                for key, pad in pad_values.items()}

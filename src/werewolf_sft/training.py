"""Trainer integration, exact completion loss, and resumable stage manifests."""
from __future__ import annotations

import json
from pathlib import Path

from .config import load_config, model_revision
from .encoding import SFTCollator, encode_rows
from .io import ROOT, canonical, content_hash, read_jsonl, sha256_file, write_json
from .modeling import load_base, load_tokenizer, prepare_trainable
from .runtime import load_cases, protocol, adapter_digest, run_lock


def completion_loss(model, inputs):
    """Compute only supervised logits; same causal loss with much smaller VRAM."""
    import torch
    import torch.nn.functional as F
    labels = inputs["labels"]
    positions = (labels[:, 1:] != -100).any(dim=0).nonzero(as_tuple=True)[0]
    if not len(positions):
        raise ValueError("no supervised next-token positions")
    output = model(input_ids=inputs["input_ids"], attention_mask=inputs["attention_mask"],
                   use_cache=False, logits_to_keep=positions)
    target = labels[:, 1:][:, positions]
    # Limit fp32 softmax workspace to 32 positions without detaching gradients.
    loss = output.logits.new_zeros((), dtype=torch.float32)
    for offset in range(0, len(positions), 32):
        logits = output.logits[:, offset:offset + 32, :].float()
        current = target[:, offset:offset + 32].to(logits.device)
        loss = loss + F.cross_entropy(logits.reshape(-1, logits.shape[-1]), current.reshape(-1),
                                      ignore_index=-100, reduction="sum")
    return loss / (target != -100).sum(), output


def make_trainer_class():
    from transformers import Trainer
    class CompletionTrainer(Trainer):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.model_accepts_loss_kwargs = False

        def compute_loss(self, model, inputs, return_outputs=False, num_items_in_batch=None):
            loss, output = completion_loss(model, inputs)
            return (loss, output) if return_outputs else loss
    return CompletionTrainer


def check_baseline(config):
    path = ROOT / config["evaluation"]["baseline_dir"] / "summary.json"
    if not path.exists():
        raise ValueError("complete the full Base benchmark before formal QLoRA")
    report = json.loads(path.read_text(encoding="utf-8"))
    expected = content_hash(protocol(config, load_cases(config)))
    if report["summary"]["status"] != "complete" or report["adapter_digest"] is not None:
        raise ValueError("baseline must be complete and use the unmodified Base")
    if report["protocol_fingerprint"] != expected:
        raise ValueError("baseline protocol differs from this training/evaluation config")


def prepare_stage_data(config, stage, tokenizer):
    root = ROOT / config["data"]["root"] / stage
    train_path, val_path = root / "train.messages.jsonl", root / "validation.messages.jsonl"
    train_rows, val_rows = read_jsonl(train_path), read_jsonl(val_path)
    for row in train_rows + val_rows:
        if row["dataset_version"] != config["data"]["version"]:
            raise ValueError("dataset version mismatch")
    train, dropped_train = encode_rows(tokenizer, train_rows, config["data"]["max_length"], config["data"]["overlength"])
    val, dropped_val = encode_rows(tokenizer, val_rows, config["data"]["max_length"], config["data"]["overlength"])
    info = {"version": config["data"]["version"], "train_hash": sha256_file(train_path),
            "validation_hash": sha256_file(val_path), "train_rows": len(train), "validation_rows": len(val),
            "dropped_train": dropped_train, "dropped_validation": dropped_val,
            "train_lengths": [len(f["input_ids"]) for f in train]}
    return train, val, info


def run_training(config, stage, resume=False, initial_adapter=None, dry_run=False):
    with run_lock(ROOT / config["training"]["output_root"] / stage):
        return _run_training(config, stage, resume, initial_adapter, dry_run)


def _run_training(config, stage, resume=False, initial_adapter=None, dry_run=False):
    import torch
    from transformers import TrainingArguments, TrainerCallback, set_seed
    from transformers.trainer_utils import get_last_checkpoint
    set_seed(config["training"]["seed"])
    output = ROOT / config["training"]["output_root"] / stage
    tokenizer = load_tokenizer(config)
    train, val, data_info = prepare_stage_data(config, stage, tokenizer)
    if dry_run:
        return {"status": "dry_run", "stage": stage, **data_info}
    check_baseline(config)
    if stage != "rules" and initial_adapter is None:
        previous = {"strategy": "rules", "tactics": "strategy"}[stage]
        initial_adapter = ROOT / config["training"]["output_root"] / previous / "final"
    if initial_adapter:
        previous_manifest = json.loads((Path(initial_adapter) / "run_manifest.json").read_text(encoding="utf-8"))
        if previous_manifest["base_model"] != config["model"]["name"] or previous_manifest["revision"] != model_revision(config):
            raise ValueError("previous adapter uses a different Base/revision")
        if previous_manifest["config"]["lora"] != config["lora"]:
            raise ValueError("stage continuation must preserve LoRA configuration")
    manifest = {
        "project": config["project"], "stage": stage, "base_model": config["model"]["name"],
        "revision": model_revision(config), "dataset": data_info, "config": config,
        "initial_adapter_digest": adapter_digest(initial_adapter),
        "training_source_sha256": sha256_file(Path(__file__)),
    }
    manifest_path = output / "run_manifest.json"
    if manifest_path.exists():
        if json.loads(manifest_path.read_text(encoding="utf-8")) != manifest:
            raise ValueError("training fingerprint mismatch; use a new run directory")
        if (output / "training_result.json").exists() and (output / "final/run_manifest.json").exists():
            return {"status": "already_complete", "stage": stage}
        if not resume:
            raise ValueError("run exists; use --resume to continue")
    output.mkdir(parents=True, exist_ok=True)
    write_json(manifest_path, manifest)
    last_checkpoint = get_last_checkpoint(str(output)) if resume else None
    model, dtype = load_base(config, training=True)
    model = prepare_trainable(model, dtype, config, adapter=last_checkpoint or initial_adapter)
    t = config["training"]

    class JournalCallback(TrainerCallback):
        def on_log(self, args, state, control, logs=None, **kwargs):
            if logs:
                with (output / "training.jsonl").open("a", encoding="utf-8") as handle:
                    handle.write(canonical({"step": state.global_step, "epoch": state.epoch, **logs}) + "\n")
            write_json(output / "progress.json", {"status": "training", "step": state.global_step,
                       "epoch": state.epoch, "best_checkpoint": state.best_model_checkpoint})

        def on_save(self, args, state, control, **kwargs):
            path = output / f"checkpoint-{state.global_step}"
            write_json(path / "run_manifest.json", manifest)

    args = TrainingArguments(
        output_dir=str(output), num_train_epochs=t["epochs"], max_steps=t["max_steps"],
        per_device_train_batch_size=1, per_device_eval_batch_size=1,
        gradient_accumulation_steps=t["gradient_accumulation_steps"],
        learning_rate=t["learning_rate"], warmup_ratio=t["warmup_ratio"], weight_decay=t["weight_decay"],
        max_grad_norm=t["max_grad_norm"], optim=t["optimizer"], lr_scheduler_type="cosine",
        bf16=dtype == torch.bfloat16, fp16=dtype == torch.float16,
        gradient_checkpointing=t["gradient_checkpointing"], gradient_checkpointing_kwargs={"use_reentrant": False},
        save_strategy="steps", save_steps=t["save_steps"], eval_strategy="steps", eval_steps=t["save_steps"],
        logging_steps=t["logging_steps"], save_total_limit=t["save_total_limit"],
        load_best_model_at_end=True, metric_for_best_model="eval_loss", greater_is_better=False,
        seed=t["seed"], data_seed=t["seed"], report_to="none", remove_unused_columns=False,
        prediction_loss_only=True, dataloader_pin_memory=False, dataloader_num_workers=0,
        save_safetensors=True,
    )
    trainer = make_trainer_class()(model=model, args=args, train_dataset=train, eval_dataset=val,
        data_collator=SFTCollator(tokenizer.pad_token_id), processing_class=tokenizer,
        callbacks=[JournalCallback()])
    torch.cuda.reset_peak_memory_stats()
    result = trainer.train(resume_from_checkpoint=last_checkpoint)
    # Trainer chooses the best saved checkpoint by held-out loss; this is not a
    # claim of best game-playing ability. Also keep full latest checkpoints.
    evaluation = trainer.evaluate()
    final = output / "final"
    trainer.save_model(str(final))
    tokenizer.save_pretrained(str(final))
    trainer.save_state()
    write_json(final / "run_manifest.json", manifest)
    summary = {"status": "trained", "stage": stage, "global_step": trainer.state.global_step,
               "epoch": trainer.state.epoch, "best_checkpoint": trainer.state.best_model_checkpoint,
               "peak_vram_mib": torch.cuda.max_memory_allocated() / 2**20,
               "metrics": result.metrics, "validation": evaluation, "model_benchmark": "not_run"}
    write_json(output / "training_result.json", summary)
    write_json(output / "progress.json", summary)
    return summary

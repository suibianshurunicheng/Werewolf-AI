"""Pinned model loading and explicit low-memory choices."""
from __future__ import annotations

import os

from .config import model_revision
from .io import ROOT


def setup_cache():
    os.environ.setdefault("HF_HOME", str(ROOT / "cache/huggingface"))
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def load_tokenizer(config, local_only=True):
    setup_cache()
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        snapshot_path(config) if local_only else config["model"]["name"],
        revision=model_revision(config), trust_remote_code=False,
        cache_dir=ROOT / "cache/huggingface/hub", local_files_only=local_only,
    )
    if not tokenizer.chat_template:
        raise ValueError("upstream tokenizer has no chat template")
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    return tokenizer


def snapshot_path(config):
    """Resolve a pinned directory, avoiding optional tokenizer Hub probes."""
    path = ROOT / "cache/huggingface/hub" / ("models--" + config["model"]["name"].replace("/", "--"))
    path = path / "snapshots" / model_revision(config)
    if not (path / "config.json").exists():
        raise FileNotFoundError("pinned model missing; run scripts/prepare_model.py")
    return str(path)


def choose_dtype(config):
    import torch
    value = config["quantization"]["compute_dtype"]
    if value == "bf16" and not torch.cuda.is_bf16_supported():
        raise RuntimeError("BF16 requested but hardware does not support it")
    return torch.bfloat16 if value == "bf16" or (value == "auto" and torch.cuda.is_bf16_supported()) else torch.float16


def load_base(config, training=False, local_only=True):
    setup_cache()
    import torch
    from transformers import AutoModelForCausalLM, BitsAndBytesConfig
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA unavailable; use CPU smoke tests, not fake QLoRA")
    dtype = choose_dtype(config)
    quantized = config["quantization"]["enabled"]
    kwargs = dict(
        revision=model_revision(config), trust_remote_code=False, torch_dtype=dtype,
        cache_dir=ROOT / "cache/huggingface/hub", local_files_only=local_only,
        attn_implementation="sdpa", low_cpu_mem_usage=True,
    )
    if quantized:
        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True, bnb_4bit_compute_dtype=dtype,
        )
    if config["training"]["cpu_offload"]:
        if training:
            raise ValueError("automatic CPU dispatch is inference-only; not a supported QLoRA training path")
        kwargs["device_map"] = "auto"
        kwargs["max_memory"] = {0: "3000MiB", "cpu": "12GiB"}
        if quantized:
            kwargs["quantization_config"].llm_int8_enable_fp32_cpu_offload = True
    else:
        kwargs["device_map"] = {"": 0}
    model = AutoModelForCausalLM.from_pretrained(
        snapshot_path(config) if local_only else config["model"]["name"], **kwargs)
    model.name_or_path = config["model"]["name"]
    model.config._name_or_path = config["model"]["name"]
    if model.config.model_type not in {"qwen2", "qwen3"}:
        raise ValueError("unsupported V1 model architecture")
    if quantized:
        import bitsandbytes as bnb
        count = sum(isinstance(m, bnb.nn.Linear4bit) for m in model.modules())
        if not getattr(model, "is_loaded_in_4bit", False) or count == 0:
            raise RuntimeError("4-bit loading did not take effect")
    model.config.use_cache = not training
    return model, dtype


def prepare_trainable(model, dtype, config, adapter=None):
    from peft import LoraConfig, PeftModel, get_peft_model, prepare_model_for_kbit_training
    if config["quantization"]["enabled"]:
        model = prepare_model_for_kbit_training(
            model, use_gradient_checkpointing=config["training"]["gradient_checkpointing"],
            gradient_checkpointing_kwargs={"use_reentrant": False},
        )
        # PEFT upcasts large frozen embeddings/head to fp32. Restore only these
        # frozen modules to compute dtype; keep norms and trainable LoRA fp32.
        for module in {model.get_input_embeddings(), model.get_output_embeddings()}:
            if not any(p.requires_grad for p in module.parameters()):
                module.to(dtype=dtype)
    elif config["training"]["gradient_checkpointing"]:
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        model.enable_input_require_grads()
    if adapter:
        model = PeftModel.from_pretrained(model, str(adapter), is_trainable=True)
    else:
        model = get_peft_model(model, LoraConfig(
            task_type="CAUSAL_LM", r=config["lora"]["rank"], lora_alpha=config["lora"]["alpha"],
            lora_dropout=config["lora"]["dropout"], target_modules=config["lora"]["target_modules"], bias="none",
        ))
    if not any(p.requires_grad for p in model.parameters()):
        raise RuntimeError("no trainable adapter parameters")
    if any(p.requires_grad and "lora_" not in name for name, p in model.named_parameters()):
        raise RuntimeError("unexpected full-parameter training")
    return model

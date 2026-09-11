"""Portable environment evidence without home paths, tokens or usernames."""
import importlib.metadata
import json
import platform
import subprocess

import _bootstrap
from werewolf_sft.io import ROOT, write_json


def main():
    packages = {}
    for name in ("torch", "transformers", "peft", "accelerate", "bitsandbytes", "safetensors", "pytest", "PyYAML"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    result = {"python": platform.python_version(), "os": platform.system(), "packages": packages}
    import torch
    result.update(cuda_available=torch.cuda.is_available(), cuda_build=torch.version.cuda)
    if torch.cuda.is_available():
        props = torch.cuda.get_device_properties(0)
        result.update(gpu=props.name, vram_mib=props.total_memory / 2**20,
                      bf16=torch.cuda.is_bf16_supported(), compute_capability=[props.major, props.minor])
        import bitsandbytes as bnb
        layer = bnb.nn.Linear4bit(64, 32, quant_type="nf4", compress_statistics=True,
                                 compute_dtype=torch.float16).to("cuda")
        inputs = torch.randn(1, 4, 64, device="cuda", dtype=torch.float16, requires_grad=True)
        output = layer(inputs)
        output.float().square().mean().backward()
        result["nf4_forward_backward"] = bool(torch.isfinite(output).all() and torch.isfinite(inputs.grad).all())
    write_json(ROOT / "reports/environment.json", result)
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()

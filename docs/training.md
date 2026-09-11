# 分阶段训练与恢复

环境实际验证：Windows / Python 3.12.14 / torch 2.6.0+cu118 / transformers 4.57.6 / PEFT 0.18.1 / bitsandbytes 0.49.2。3050 Ti 4GB 的 NF4 前向和反向微测试通过。整模型训练容量仍须实际验证。

## 准备和顺序

1. 安装 requirements-dev.txt 与 requirements.txt，CUDA PyTorch 按对应驱动安装；当前本机用 cu118。
2. 运行 python scripts/prepare_model.py。固定revision保存于reports/models；缓存不提交Git。
3. 运行 python scripts/check_environment.py 和 python scripts/check_lengths.py。
4. 运行 python scripts/evaluate.py --report reports/base_model_baseline.md。完整36题Base是正式训练入口的强制前置检查。
5. 运行 python scripts/train_qlora.py --stage rules，再 strategy，再 tactics。
6. 每阶段默认1 epoch、r8、alpha16、batch1、累积16、NF4双量化、硬件支持时BF16、gradient checkpointing、无packing、完整1024上下文。185种子最长931，不截断任何答案。
7. 每个优化step评估和保存。小数据只有少量step，原10步保存会缺少中间恢复点，因此改为1。保留最多3个checkpoint、最终最佳验证Loss Adapter。

所有参数在configs YAML中；继承后完整配置随run_manifest保存。12/16/24GB配置可直接传 --config；这些容量配置尚未在对应显卡实测。基础模型的原生长上下文不等于本机训练可用长度。

## 中断恢复

同配置同阶段追加 --resume，例如 python scripts/train_qlora.py --stage rules --resume。Trainer恢复optimizer、scheduler、RNG和step；指纹变化时拒绝复用目录。没有完整checkpoint时只能重做最后尚未保存的部分，不修改已完成数据。

每阶段目录 outputs/classic_v01/{stage}/ 保留run_manifest.json、training.jsonl、progress.json、checkpoint-N、final和training_result.json。checkpoint中有Adapter、训练参数、optimizer/scheduler/RNG、trainer_state；每个checkpoint另存run_manifest。final用于推理，不含继续精确恢复所需的完整优化状态。最佳checkpoint只按验证Loss，不称为最佳博弈能力。

modeling保留冻结大词表参数的计算dtype；训练只更新LoRA。completion loss只计算被监督的位置并分块softmax，CPU小模型验证与标准causal loss及梯度一致。该软件测试不是4B训练成功证据。

若OOM，保存错误后用新的配置及output_root依次缩短长度（显式filter且记录被过滤ID）、维持batch1、增加累积、降低rank、缩小target modules、检查checkpointing/NF4、尝试offload和3B备用。禁止把不支持训练的自动CPU device_map当成有效训练offload。不得静默删样本或宣称未实际发生的OOM。

## LoRA与合并

普通LoRA：python scripts/train_lora.py --config configs/lora_classic.yaml --stage rules。4GB不承诺容纳非量化4B。

合并：python scripts/merge_adapter.py --adapter outputs/classic_v01/tactics/final --output outputs/merged-v01。在CPU加载完整FP32基础权重，RAM和磁盘需充足；不在NF4权重上直接合并。输出继承上游许可。正式模型无成功Adapter时不得运行或发布虚构权重。

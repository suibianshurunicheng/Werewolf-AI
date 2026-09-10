# 3B～4B 底座选择

核对日期：2026-09-10。选通用指令模型作微调起点，不选狼人杀专项模型。下面能力来自官方介绍和架构判断，尚无本项目实测排名。

| 模型 | 参数/上下文 | 中文、推理、指令与角色表达 | 兼容性与代价 | 许可/判断 |
|---|---|---|---|---|
| Qwen3-4B-Instruct-2507 | 4.0B / 原生 262144 | 多语种，改进逻辑/指令/开放写作；无 thinking 块，适合分字段输出 | 原生 Transformers Qwen3、PEFT、bnb QLoRA；标准 Attention/MLP；LlamaFactory qwen3_nothink | Apache-2.0；Primary |
| Qwen2.5-3B-Instruct | 3.09B / 32768 | 中文与结构化输出成熟，推理上限需实测 | 原生 Qwen2、PEFT、bnb；体积较小，作为显存回退；LlamaFactory qwen | Qwen Research，非商业研究/评测；Backup |
| Qwen3-4B | 4.0B / 原生 32768，可扩展 | 中文和推理模式可切换 | 同架构成熟，但需处理 thinking 模板，不比 Primary 更省主要权重 | Apache-2.0；未选 |
| Qwen3.5-4B | 官方标称 4B 语言模型 / 262144 | 较新、多语多模态和推理；狼人杀收益未测 | 混合线性注意力、视觉部件，需新 Transformers；当前锁定 4.57.6 路线不直接兼容；LlamaFactory 已列支持 | Apache-2.0；V1 暂不引入额外架构复杂度 |

Tokenizer：前两者用各自仓库的 AutoTokenizer 和原始 Jinja Chat Template；不手拼 ChatML、不互换词表。Primary 无 thinking 输出。TRL 可接入相同模型与 PEFT，但 V1 使用 Transformers Trainer 与显式 assistant-only labels，避免依赖 TRL 版本变化的掩码 API；不声称已做 TRL 或 LlamaFactory 端到端实测。

## 4GB 资源选择

4B 权重的理想 4-bit 下限约 2GB；实际还需量化元数据、未量化 embedding/head、LoRA、梯度、激活与工作区。因此不能据 2GB 下限承诺 4GB 训练成功。先用 batch 1、r 8、1024 序列、gradient checkpointing、NF4 + double quant；按 OOM 证据减到 512/256、r 4、减少 target modules，再评估 CPU offload 和 3.09B 回退。12/16/24GB 配置按可容纳上下文逐级增加，全部是起始预算而非实测显存保证。

本地推理 tokens/s 尚未测，不能编造速度或跨模型优势。Benchmark 必须记录实际输入/输出 tokens、耗时与峰值显存。4B 长上下文标称值不是 4GB 本机可用上下文。

## 发布条件

Primary 的 Adapter 和合并权重保留 Apache-2.0、上游 NOTICE（如有）与修改说明。项目 MIT 只覆盖原创代码，不能覆盖上游模型许可。Backup 限非商业研究/评测，商业使用需要另向权利人申请；分发衍生物须附协议和归属，并在相关文档标注 Built with Qwen。数据采用项目原创合成场景，网页只作规则核对，不复制攻略正文/视频字幕。合成数据不宣称真人授权或人工复核。

## 核对来源

- [Primary 官方模型卡](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507)
- [Backup 官方模型卡](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct)与[许可全文](https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/raw/main/LICENSE)
- [Qwen3-4B](https://huggingface.co/Qwen/Qwen3-4B)、[Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B)
- [LlamaFactory 支持列表](https://github.com/hiyouga/LlamaFactory)、[PEFT 量化训练](https://huggingface.co/docs/peft/developer_guides/quantization)、[bitsandbytes 平台支持](https://huggingface.co/docs/bitsandbytes/installation)

先前 7B～9B 调研因用户缩小规模而停止，不能把旧 8B 选择恢复为当前默认。

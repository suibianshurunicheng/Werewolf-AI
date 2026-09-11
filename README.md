# Werewolf-3.5B-Classic V1

3B～4B 中文狼人杀专项 SFT 工程，当前仅经典12人预女守猎。操作者人工输入合法视角，只复制正式公开发言。项目未提供自动竞技场、RL或Web前端。

最新真实状态见 PROJECT_STATUS.md。目前已有185条原创种子、36题独立Benchmark和训练/评测工具；尚无训练完成的专项Adapter，不宣称能力提升。

## 恢复

先读取 README.md、PROJECT_STATUS.md、DECISIONS.md、TODO.md 和 git log -5 --oneline，直接执行状态末尾 Resume Here。不得重新初始化或覆盖已有数据版本。当前GitHub仓库：https://github.com/suibianshurunicheng/Werewolf-AI。

## 安装与准备

使用 Python 3.10～3.12 创建虚拟环境：python -m venv .venv。Windows激活 .venv/Scripts/Activate.ps1；Linux激活 .venv/bin/activate。下列python均指该虚拟环境。

1. python -m pip install -r requirements-dev.txt
2. 本机546.30驱动使用：python -m pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cu118
3. python -m pip install -r requirements.txt
4. python -m pytest
5. python scripts/check_environment.py
6. python scripts/prepare_model.py
7. python scripts/check_lengths.py

模型首次下载需要网络；以后从固定revision本地目录加载。缓存和权重不进Git。若仓库已包含dataset_v0.1，直接使用；python scripts/prepare_dataset.py仅验证一致快照并补齐缺失文件，不覆盖异内容。

## 基线、训练、比较

先完整运行：python scripts/evaluate.py --report reports/base_model_baseline.md。中断后执行原命令，只继续未完成题。每题原子保存，修改模型或生成配置会拒绝混入原目录。

按顺序运行：

- python scripts/train_qlora.py --stage rules
- python scripts/train_qlora.py --stage strategy
- python scripts/train_qlora.py --stage tactics

恢复同阶段追加 --resume；脚本保存完整配置、数据哈希、日志、Adapter、optimizer、step/epoch和最佳checkpoint。没有完整Base报告会拒绝正式训练。运行前可加 --dry-run，仅检查真实Tokenizer编码，不代表训练成功。

完成后：python scripts/evaluate.py --adapter outputs/classic_v01/tactics/final --output reports/runs/qlora_v01 --compare-to reports/runs/base_primary --report reports/qlora_v01.md。自动输出reports/base_vs_qlora.md。相同题目与生成协议才允许比较；动作匹配不能替代策略盲审或真实胜率。

4GB起始配置为configs/qlora_classic.yaml；12/16/24GB预设可通过 --config 指定，但不承诺未经实测的显存需求。普通LoRA、合并和OOM处理详见docs/training.md。

## 人工使用

python scripts/inference.py --input-json data/examples/player_sample.json。自由文本用 --prompt-file 填好的模板.txt。成功训练后追加 --adapter outputs/classic_v01/tactics/final。只复制【正式公开发言】；--public-only仅显示这一部分。详见docs/manual_match.md。

## 文档与许可

规则及房规差异：docs/rules_classic.md、docs/rule_conflicts.md。数据、评测、模型选择及模型卡见docs目录。镜隐仅为Phase 2调研，禁止混入当前训练。

代码MIT；原创合成种子CC-BY-4.0，未做独立专家复核。Primary Qwen3-4B-Instruct-2507为Apache-2.0；Backup Qwen2.5-3B-Instruct限非商业研究。Adapter和合并权重仍须遵守相应上游许可。

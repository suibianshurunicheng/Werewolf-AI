# 可独立恢复的任务

状态：`[x]` 已完成；`[ ]` 尚未完成。只依据文件和真实运行证据打勾。

## Phase 0

- [x] 读取用户两版要求，并以 3B～4B / classic_12 为当前目标。
- [x] 初始化一个本地 Git Repository，建立状态、决策、恢复文档。
- [x] 检查本机 GPU、驱动、磁盘与 Python 环境。
- [x] 完成 3B～4B 候选模型调研和初步选择。
- [x] 冻结经典规则 ww-v1.0，镜隐标为 Phase 2。
- [x] 完成数据 Schema、最小合法样本、8 份经典 Prompt；37 项基础测试通过。
- [ ] 建立按战术条件区分的经典 Gold 种子集，标注合成来源与复核状态。
- [ ] 建立四类独立 Benchmark、反事实配对与污染检查。
- [ ] 生成不可覆盖的 dataset_v0.1 快照、messages 和哈希清单。
- [ ] 实现可恢复的 QLoRA/LoRA、推理、评测和 Adapter 合并。
- [ ] 完成 4GB / 12GB / 16GB / 24GB 配置及 CPU 链路验证。
- [ ] 完成 README、数据、训练、评测、手动对局和模型卡。
- [ ] 完成提交前内容检查，推送 GitHub suibianshurunicheng/Werewolf-AI（已确认空仓库、SSH 可用）。

## Phase 1

- [ ] 下载并固定 Primary 模型与 Tokenizer revision。
- [ ] 验证 CUDA 和 NF4 实际加载情况。
- [ ] 完整运行并保存 Base Benchmark，逐条可恢复。
- [ ] 真实尝试 Rule QLoRA；失败时保存错误及逐项低显存调整。
- [ ] 顺序续训 Strategy、Tactics，保留每阶段 Adapter 和日志。
- [ ] 同一 Benchmark 测 Adapter，保留失败案例与配对比较。
- [ ] 依据开发集失败修正数据，生成 dataset_v0.2 并训练第二轮。
- [ ] 通过未参与修正的保留集和人工复制粘贴测试验收。

## Phase 2（暂停）

- [ ] 只有 Phase 1 正式训练和 Benchmark 完成后才冻结完整镜隐规则并生成数据。

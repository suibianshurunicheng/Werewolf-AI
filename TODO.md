# 可恢复的小任务

[x]已完成；[ ]未完成。只凭真实文件和运行证据勾选。

## Phase 0

- [x] 初始化并推送用户指定GitHub仓库，建立状态/决策/恢复文档。
- [x] 固定3B～4B主备模型、经典ww-v1.0；镜隐保留Phase2。
- [x] 规则纯函数、严格Schema、视角验证、8模板和基础37测试。
- [x] 185原创种子及独立36题Benchmark，分组去污染，dataset_v0.1版本化；46测试。
- [x] 可恢复训练/推理/评测/合并脚本与65测试。
- [x] 4GB/12GB/16GB/24GB配置和CPU小模型链路验证（不等于各档GPU实测）。
- [x] README、数据、训练、评测、人工使用和模型卡。

## Phase 1

- [x] Primary固定revision并完整下载权重及Tokenizer。
- [x] 实测CUDA、BF16支持和NF4前向反向。
- [x] 所有训练样本实际Tokenizer长度检查；Rule dry-run零过滤。
- [x] 工具链3110940已提交推送；增加中断精确恢复和运行锁测试。
- [x] 完整Base36/36生成结束，reports/base_model_baseline.md已保存。
- [ ] Base结果保存并commit后实际Rule QLoRA，记录任何OOM及逐项调整。
- [ ] 顺序Strategy、Tactics训练与每阶段checkpoint/log/config。
- [x] 完整结果已统一--score-only，strict-actions-v1.1诊断列已保存，没有重做生成。
- [ ] 分开检查动作词汇接入与真实策略能力；不得用格式改善冒充策略提升。
- [ ] 相同Benchmark评Adapter，reports/qlora_v01.md及base_vs_qlora.md。
- [ ] 仅用dev失败修正并生成dataset_v0.2，第二轮训练。
- [ ] 未用于修正的保留集及真实人工复制粘贴对局验收。

## Phase 2（暂停）

- [ ] Phase1验收后才正式冻结镜隐、生成镜隐数据与训练。

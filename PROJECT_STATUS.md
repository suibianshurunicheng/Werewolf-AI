# Werewolf-3.5B-Classic V1 工程状态

更新：2026-09-11。当前Phase：Phase 1，完整Base和Rule QLoRA已完成，准备Strategy SFT。

## 已完成任务

- 用户指定GitHub仓库已多阶段提交推送；最近确定完成训练检查点4904dda，未重新初始化或重做已冻结数据。
- classic_12 / ww-v1.0、严格玩家视角Schema、8模板、规则纯函数和完整工具链。
- dataset_v0.1：42规则+18策略+125战术=185原创种子，分场景族训练/验证，无镜隐；未独立人工复核。
- 独立36题Benchmark（规则12、策略8、反事实8、盲测8），dev/test固定，4对单变量反事实。
- Primary Qwen3-4B-Instruct-2507 revision cdbee75f17c01a7cc42f958dc650907174af0554 已下载；不需要再次选型或下载。
- CUDA/NF4前向反向微测试通过；真实4B Base已在RTX3050Ti 4GB完成36/36题，未出现OOM。
- Base以strict-actions-v1.1统一评分完成，reports/base_model_baseline.md及runs/base_primary已保存全部原始回答。

## 当前正在进行

完整Base52514c6已推送。Rule QLoRA实际完成3step/1epoch，Adapter和checkpoint已核验；warmup修复及67项完整测试已通过；Strategy dry-run为15 train/3 val、1 step、0 warmup。保存修复后继续Strategy。新增D:/BiliDownload视频审核任务，已发现185条约77.98小时，尚未评定片段质量。

## 尚未完成任务

- Strategy和Tactics顺序续训；Rule已完成，不要重跑。
- 如果OOM：依顺序保存并实施长度、rank、target modules、offload等合理调整，必要时备用3B；不能因估计显存而放弃。
- 相同协议测Adapter，生成qlora_v01.md与base_vs_qlora.md。
- dev失败修正dataset_v0.2及第二轮训练。
- 独立语义审核、未用于修正的保留集及真实人工复制粘贴对局验收。

## 重要文件

- configs/qlora_classic.yaml：NF4双量化、r8/alpha16、batch1、累积16、1024、每step保存评估、1 epoch、BF16自动、无packing。
- data/versions/dataset_v0.1.json及data/gold、data/prepared；禁止覆盖版本快照。
- scripts/train_qlora.py、train_lora.py、evaluate.py、inference.py、merge_adapter.py、checkpoint_evaluation.py。
- src/werewolf_sft/training.py：版本哈希检查、基线门禁、assistant-only loss、逐步日志、完整checkpoint哈希标记和恢复。
- reports/environment.json、token_lengths.json、toolchain.md、base_model_baseline.md、base_model_baseline.cases.json、base_dev_diagnostics.md、runs/base_primary/{run,summary,predictions,progress}.json/jsonl及cases/。
- reports/base_progress.*保留早期partial历史快照，不是当前最终报告。
- cache/huggingface与outputs为本地大文件目录，不进Git。训练失败会独立保存到reports/training_attempts。

## 已运行测试与结果

- 完整65项pytest通过；随后扩充空Benchmark配置拒绝用例，6项配置参数化测试通过（现共66项）。
- CPU小型Qwen3验证completion-only损失和梯度与标准实现等价；LoRA保存重载一致；step1中断后恢复到step4与连续训练参数/验证结果一致。这不是4B训练成功证据。
- 数据快照篡改拒绝、残缺/损坏checkpoint跳过、OS运行锁测试通过。
- 185条实际Tokenizer长度649～931，全部适配1024。Rule dry-run35训练/7验证、零过滤。
- 完整Base：生成速度中位6.22 tokens/s，PyTorch峰值分配2909.2MiB，36题均未截断。
- 精确参考动作匹配：rules0/12、strategy0/8、counterfactual0/8、blind2/8。JSON有效33/36。未知动作词约束造成明显接口混淆，不等同于狼人杀能力全为0，详见诊断。
- Rule真实训练：3step/1epoch，35 train/7 val，峰值3376.9MiB；验证Loss3.26995→2.96880。252个LoRA B矩阵非零，最终checkpoint-3完整哈希通过。证据reports/training/rules_v01，权重outputs/classic_v01/rules/final。
- GitHub 2e55c70 CI已成功；后续提交CI尚未复查。

## 新增视频审核与磁盘约束

- 来源D:/BiliDownload：185条，元数据总时长77.98小时；没有独立字幕文件，m4s音视频需实际解码/转录，弹幕不是玩家转录。所有条目保持待审核，不按板子直接淘汰。
- 审核执行docs/video_review_policy.md：CLASSIC_GOLD/TRANSFERABLE/BOARD_SPECIFIC/LOW_QUALITY，机制剥离后可生成CLASSIC_ADAPTED，特殊板子原样不得进Phase1。
- 2026-09-11实测C盘剩余49.17GiB，D盘100.84GiB，目前无需迁移。恢复和大文件处理前检查；C不足时保存checkpoint后迁移整个项目到D；D也不足时提醒租云服务器。

## 当前阻塞项

没有外部阻塞。4GB已完成真实Rule QLoRA，不能据此保证所有长度或阶段都稳定。Base的精确动作匹配同时反映接口词汇问题；最终能力提升不能只依据该指标，必须另做语义审核或统一动作字典的新协议重测。

## 下一步具体任务

1. Rule4904dda已提交推送；提交warmup修复并开始Strategy。
2. 继续Strategy/Tactics，逐阶段导出真实参数变化及日志；视频审核先建可恢复索引再完成一局，不批量伪造评级。
3. 每完成一个阶段更新三份状态文档并commit。保持一个确定完成的可恢复检查点。

## Resume Here

先读README、PROJECT_STATUS、DECISIONS、TODO和git log -5 --oneline，再检查git status；不初始化、不重做数据、不重跑已完成Base。

第一项任务：Rule已完成，不要重跑。warmup修复已通过67项测试和Strategy dry-run，提交后执行 .venv/Scripts/python.exe scripts/train_qlora.py --stage strategy 。默认从outputs/classic_v01/rules/final载入已完成Adapter。

训练CLI已开启HF_HUB_OFFLINE，避免PEFT保存时对未固定main的非必要查询；prepare_model.py仍是显式下载入口。Rule保存阶段出现网络探测警告，但最终保存成功，不是OOM。

Strategy成功后用scripts/export_training.py导出日志/哈希，并验证相对Rule权重确有变化；更新状态commit，再训练tactics。中断同配置加--resume，仅加载完整哈希checkpoint。旧Rule源代码由52514c6记录，规则训练结果保持不变。

大权重未进Git：本机outputs/classic_v01/rules保存3个完整checkpoint和final。换主机时必须复制该目录，按reports/training/rules_v01/artifacts.json核对SHA；只有Git副本不含Adapter权重，不能伪称已恢复权重。

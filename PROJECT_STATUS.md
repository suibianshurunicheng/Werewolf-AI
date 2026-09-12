# Werewolf-3.5B-Classic V1 工程状态

更新：2026-09-12。当前Phase：Phase 1，完整Base及Rule→Strategy→Tactics三阶段QLoRA已完成；下一项为同协议Adapter评测。

## 已完成任务

- 用户指定GitHub仓库已多阶段提交推送；Rule、Strategy、Tactics的完整训练检查点均已保存，未重新初始化或重做已冻结数据。
- classic_12 / ww-v1.0、严格玩家视角Schema、8模板、规则纯函数和完整工具链。
- dataset_v0.1：42规则+18策略+125战术=185原创种子，分场景族训练/验证，无镜隐；未独立人工复核。
- 独立36题Benchmark（规则12、策略8、反事实8、盲测8），dev/test固定，4对单变量反事实。
- Primary Qwen3-4B-Instruct-2507 revision cdbee75f17c01a7cc42f958dc650907174af0554 已下载；不需要再次选型或下载。
- CUDA/NF4前向反向微测试通过；真实4B Base已在RTX3050Ti 4GB完成36/36题，未出现OOM。
- Base以strict-actions-v1.1统一评分完成，reports/base_model_baseline.md及runs/base_primary已保存全部原始回答。

## 当前正在进行

三阶段训练均完成，正在保存Tactics最终导出证据，随后执行36题同协议Adapter评测。Strategy为1step/1epoch（15 train/3 val），相对Rule实际改变504个张量，峰值3315.8MiB，验证Loss3.058638。Tactics为7step/1epoch（105 train/20 val），相对Strategy改变504个张量，最佳checkpoint-7验证Loss2.8225455；训练进程在最后checkpoint保存后、final导出前中断，已从完整哈希检查点恢复导出，没有重跑优化步。原训练峰值显存未落盘，记为null，不估造。

视频catalog_v0.1有185条/77.98小时；首局累计31帧完成局部审核，3条迁移候选、1条复盘负例候选，正式入库0，其余184条未审核。固定ASR模型已下载，首局完成1/10块原始转录（未校对），不代表完整音频审核。

## 尚未完成任务

- 三阶段训练均已完成，不要重跑；待同协议Adapter评测及能力审核。
- 如果OOM：依顺序保存并实施长度、rank、target modules、offload等合理调整，必要时备用3B；不能因估计显存而放弃。
- 相同协议测Adapter，生成qlora_v01.md与base_vs_qlora.md。
- dev失败修正dataset_v0.2及第二轮训练。
- 独立语义审核、未用于修正的保留集及真实人工复制粘贴对局验收。

## 重要文件

- configs/qlora_classic.yaml：NF4双量化、r8/alpha16、batch1、累积16、1024、每step保存评估、1 epoch、BF16自动、无packing。
- data/versions/dataset_v0.1.json及data/gold、data/prepared；禁止覆盖版本快照。
- scripts/train_qlora.py、train_lora.py、evaluate.py、inference.py、merge_adapter.py、checkpoint_evaluation.py；scripts/finalize_training.py仅补全已完成训练的最终导出。
- src/werewolf_sft/training.py：版本哈希检查、基线门禁、assistant-only loss、逐步日志、完整checkpoint哈希标记和恢复。
- reports/environment.json、token_lengths.json、toolchain.md、base_model_baseline.md、base_model_baseline.cases.json、base_dev_diagnostics.md、runs/base_primary/{run,summary,predictions,progress}.json/jsonl及cases/。
- reports/base_progress.*保留早期partial历史快照，不是当前最终报告。
- cache/huggingface与outputs为本地大文件目录，不进Git。训练失败会独立保存到reports/training_attempts。

## 已运行测试与结果

- 2026-09-12完整71项pytest通过（foundation37、dataset9、runtime21、finalization4）。新增已完成检查点幂等导出、未完成拒绝、SHA损坏拒绝和已有异内容拒绝；真实Tactics导出后504张量相对Strategy改变。
- CPU小型Qwen3验证completion-only损失和梯度与标准实现等价；LoRA保存重载一致；step1中断后恢复到step4与连续训练参数/验证结果一致。这不是4B训练成功证据。
- 数据快照篡改拒绝、残缺/损坏checkpoint跳过、OS运行锁测试通过。
- 185条实际Tokenizer长度649～931，全部适配1024。Rule dry-run35训练/7验证、零过滤。
- 完整Base：生成速度中位6.22 tokens/s，PyTorch峰值分配2909.2MiB，36题均未截断。
- 精确参考动作匹配：rules0/12、strategy0/8、counterfactual0/8、blind2/8。JSON有效33/36。未知动作词约束造成明显接口混淆，不等同于狼人杀能力全为0，详见诊断。
- Rule真实训练：3step/1epoch，35 train/7 val，峰值3376.9MiB；验证Loss3.26995→2.96880。252个LoRA B矩阵非零，最终checkpoint-3完整哈希通过。证据reports/training/rules_v01，权重outputs/classic_v01/rules/final。
- 实际probe解码H264/AAC、累计31帧；重复请求120/620秒校验SHA后复用，无覆盖。
- Tactics完整7step checkpoint SHA核验与final逐文件复制核验通过；reports/training/tactics_v01含配置、日志、最终结果、参数差异及finalization来源。原训练峰值未持久化，恢复片段的Trainer聚合loss/runtime不冒充全程统计。
- GitHub 2e55c70 CI已成功；后续提交CI尚未复查。

## 新增视频审核与磁盘约束

- 来源D:/BiliDownload：185条，元数据总时长77.98小时；没有独立字幕文件，m4s音视频需实际解码/转录，弹幕不是玩家转录。所有条目保持待审核，不按板子直接淘汰。
- 审核执行docs/video_review_policy.md：CLASSIC_GOLD/TRANSFERABLE/BOARD_SPECIFIC/LOW_QUALITY，机制剥离后可生成CLASSIC_ADAPTED，特殊板子原样不得进Phase1。
- 2026-09-12实测C盘剩余46.09GiB，D盘101.50GiB，目前无需迁移。恢复和大文件处理前检查；C不足时保存checkpoint后迁移整个项目到D；D也不足时提醒租云服务器。

## 当前阻塞项

没有外部阻塞。4GB已完成真实Rule QLoRA，不能据此保证所有长度或阶段都稳定。Base的精确动作匹配同时反映接口词汇问题；最终能力提升不能只依据该指标，必须另做语义审核或统一动作字典的新协议重测。

## 下一步具体任务

1. Tactics最终导出证据、71项测试和恢复工具先commit/push，保存一个完整阶段。
2. 相同协议测Tactics最终Adapter，逐题原子保存；不重做Base，不改变题目、Prompt或动作匹配定义。
3. 首局继续可恢复CPU转录，再校对说话者/房规与可迁移片段；不得把ASR未校对原文作为SFT。
4. 每完成独立阶段更新三份状态文档并commit；只用dev失败改进下一数据版本。

## Resume Here

先读README、PROJECT_STATUS、DECISIONS、TODO和git log -5 --oneline，再检查git status；不初始化、不重做数据、不重跑已完成Base/Rule/Strategy/Tactics。

第一项任务：执行磁盘预检查后，从已有逐题结果继续同协议Adapter评测（当前尚未启动）。有活动同目录评测进程时等待，不重复启动。

```powershell
.venv/Scripts/python.exe scripts/check_disk.py --needed-gib 3
.venv/Scripts/python.exe scripts/evaluate.py --adapter outputs/classic_v01/tactics/final --output reports/runs/qlora_v01 --compare-to reports/runs/base_primary --report reports/qlora_v01.md
```

评测结果在reports/runs/qlora_v01逐题保存，中断后原命令只补缺题；完整结束生成reports/qlora_v01.md与reports/base_vs_qlora.md。比较协议指纹应为1edff4b7a2e8ae73f0294e2988ae69f50cdc58b329eca266a755db848626d569，评分strict-actions-v1.1。能力解释须分清动作词汇/规则/策略，不能仅凭Loss或格式宣称高手模型。

Tactics训练源提交90a0416，step7/epoch1全部完成。reports/training/tactics_v01已保存finalization证据，final权重SHA为b1103c4bdb6600a04b3fa4dfe87de131a896a9a41e858fcdf342a8bce70cea6d。不需要再训练或重新导出。

视频：先读reports/media/28287501902/review_v0.2.md；两轮票表与刀7/毒4字幕已补证，说话者冲突和完整房规仍未解决。configs/media_asr_v01.json固定模型已下载，不需再次download-model。cache/media/28287501902/transcript_v0.1已有chunks/0000.json；总10块仅完成1块，ASR_UNVERIFIED，尚未入库。继续下一块：

```powershell
.media-venv/Scripts/python.exe scripts/transcribe_video.py --video-id 28287501902 --max-chunks 1
```

去掉max-chunks即可继续剩余全部，已完成chunk须哈希校验复用。首块内容哈希d107efb68693c7e52f8abf521db7e7eda76a531f76a4915265f376ad09c99704；8.72～9.76秒有明显识别错误，需要另存校对，不覆盖原转录。原D:/BiliDownload不改动，非经典板不丢弃，正式SFT入库0。

大权重未进Git：本机outputs/classic_v01/{rules,strategy,tactics}含完整checkpoint和final；跨主机必须复制并按reports/training/*/artifacts.json核对SHA。Git副本本身不含权重。空间不足按docs/disk_recovery.md迁移，不能在活动训练或下载写入时搬目录。

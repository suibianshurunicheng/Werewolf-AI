# Werewolf-3.5B-Classic V1 工程状态

更新：2026-09-11。当前Phase：Phase 1，完整Base、Rule及Strategy QLoRA已完成，Tactics SFT正在运行。

## 已完成任务

- 用户指定GitHub仓库已多阶段提交推送；最近确定完成训练检查点4904dda，未重新初始化或重做已冻结数据。
- classic_12 / ww-v1.0、严格玩家视角Schema、8模板、规则纯函数和完整工具链。
- dataset_v0.1：42规则+18策略+125战术=185原创种子，分场景族训练/验证，无镜隐；未独立人工复核。
- 独立36题Benchmark（规则12、策略8、反事实8、盲测8），dev/test固定，4对单变量反事实。
- Primary Qwen3-4B-Instruct-2507 revision cdbee75f17c01a7cc42f958dc650907174af0554 已下载；不需要再次选型或下载。
- CUDA/NF4前向反向微测试通过；真实4B Base已在RTX3050Ti 4GB完成36/36题，未出现OOM。
- Base以strict-actions-v1.1统一评分完成，reports/base_model_baseline.md及runs/base_primary已保存全部原始回答。

## 当前正在进行

Strategy已从Rule续训完成1step/1epoch（15 train/3 val），相对Rule实际改变504个张量，峰值3315.8MiB，验证Loss3.058638。完整证据已导出reports/training/strategy_v01。Tactics已在90a0416提交后启动（105 train/20 val，计划7step）；确认checkpoint-1已保存，当前进行step2验证，须检查实时progress，不另启重复任务。视频catalog_v0.1有185条/77.98小时；首局18帧完成局部审核，3条迁移候选、1条复盘负例候选，正式入库0，其余184条未审核。无完整音频转录。

## 尚未完成任务

- Tactics从Strategy续训；Rule和Strategy已完成，不要重跑。
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

- 完整67项pytest通过，包含单step非零更新调度；实际Strategy训练再核验504个张量相对Rule改变。
- CPU小型Qwen3验证completion-only损失和梯度与标准实现等价；LoRA保存重载一致；step1中断后恢复到step4与连续训练参数/验证结果一致。这不是4B训练成功证据。
- 数据快照篡改拒绝、残缺/损坏checkpoint跳过、OS运行锁测试通过。
- 185条实际Tokenizer长度649～931，全部适配1024。Rule dry-run35训练/7验证、零过滤。
- 完整Base：生成速度中位6.22 tokens/s，PyTorch峰值分配2909.2MiB，36题均未截断。
- 精确参考动作匹配：rules0/12、strategy0/8、counterfactual0/8、blind2/8。JSON有效33/36。未知动作词约束造成明显接口混淆，不等同于狼人杀能力全为0，详见诊断。
- Rule真实训练：3step/1epoch，35 train/7 val，峰值3376.9MiB；验证Loss3.26995→2.96880。252个LoRA B矩阵非零，最终checkpoint-3完整哈希通过。证据reports/training/rules_v01，权重outputs/classic_v01/rules/final。
- 实际probe解码H264/AAC、抽取18帧；重复请求120/620秒校验SHA后复用，无覆盖。
- GitHub 2e55c70 CI已成功；后续提交CI尚未复查。

## 新增视频审核与磁盘约束

- 来源D:/BiliDownload：185条，元数据总时长77.98小时；没有独立字幕文件，m4s音视频需实际解码/转录，弹幕不是玩家转录。所有条目保持待审核，不按板子直接淘汰。
- 审核执行docs/video_review_policy.md：CLASSIC_GOLD/TRANSFERABLE/BOARD_SPECIFIC/LOW_QUALITY，机制剥离后可生成CLASSIC_ADAPTED，特殊板子原样不得进Phase1。
- 2026-09-11实测C盘剩余48.64GiB，D盘100.84GiB，目前无需迁移。恢复和大文件处理前检查；C不足时保存checkpoint后迁移整个项目到D；D也不足时提醒租云服务器。

## 当前阻塞项

没有外部阻塞。4GB已完成真实Rule QLoRA，不能据此保证所有长度或阶段都稳定。Base的精确动作匹配同时反映接口词汇问题；最终能力提升不能只依据该指标，必须另做语义审核或统一动作字典的新协议重测。

## 下一步具体任务

1. Strategy真实结果、视频不可变索引和磁盘预检查入本次检查点后，执行Tactics。
2. Tactics完成后导出参数变化/日志，按相同协议测Adapter；视频先实际解码首局，再获得带时间戳的证据并审核，不批量伪造评级。
3. 每完成一个阶段更新三份状态文档并commit。保持一个确定完成的可恢复检查点。

## Resume Here

先读README、PROJECT_STATUS、DECISIONS、TODO和git log -5 --oneline，再检查git status；不初始化、不重做数据、不重跑已完成Base/Rule/Strategy。

第一项任务：.venv/Scripts/python.exe scripts/check_disk.py --needed-gib 3 。检查outputs/classic_v01/tactics/progress.json与training_result.json和活动进程。Tactics已启动，训练源提交90a0416；活动进程存在时等待，不重复启动。若确已中断，执行 .venv/Scripts/python.exe scripts/train_qlora.py --stage tactics --resume ，只恢复完整哈希checkpoint。完成时先导出证据、更新状态commit。

Tactics成功后用scripts/export_training.py导出日志/哈希，--initial-adapter outputs/classic_v01/strategy/final；更新三份文档commit。然后用README中的同协议evaluate命令生成qlora_v01和base_vs_qlora报告。

视频：data/media/catalog_v0.1已完整索引185条；不要重建覆盖。首局28287501902已实际解码并保存18帧SHA及局部审核reports/media/28287501902/review_v0.1.md。读取该报告后补齐列出的房规、票型、说话者冲突及完整覆盖，再做review_v0.2与经典改写。复取画面：.media-venv/Scripts/python.exe scripts/probe_video.py --video-id 28287501902 --times 120 620 。原D:/BiliDownload不改动，视频未因9人板丢弃，正式SFT入库0。

大权重未进Git：本机outputs/classic_v01/{rules,strategy}含完整checkpoint和final；跨主机必须复制并按reports/training/*/artifacts.json核对SHA。Git副本本身不含权重。空间不足按docs/disk_recovery.md迁移，不能在活动训练或下载写入时搬目录。

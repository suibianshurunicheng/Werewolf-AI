# Werewolf-3.5B-Classic V1 工程状态

更新：2026-09-14。当前Phase：Phase 1，v0.2-core数据、三阶段正式训练、36题同协议评测和23条dev模型语义审核全部完成；定向修复能力验收未通过，v0.3视频合并门禁关闭。

## 已完成任务

- Phase 0工程基础、classic_12 / ww-v1.0、严格Schema/合法动作/玩家视角、可恢复训练与评测工具。
- Base继续固定Qwen/Qwen3-4B-Instruct-2507，revision cdbee75f17c01a7cc42f958dc650907174af0554；本地权重缓存已在，不重新调研或下载。
- v0.1保留185条原创种子、三阶段Adapter和完整36题对照。Rule3步/Strategy1步/Tactics7步，旧Tactics最佳checkpoint-7，Loss2.8225455；旧训练峰值未记录，不补造。
- v0.2-core冻结86条/50族：42 Rule、22 Strategy、22 Tactics。阶段train/val为32/10、17/5、21/1，11项覆盖能力两侧均非空。覆盖不等于规模充分，战术验证仅1例。
- 原32条规则、24条策略候选不改；补充30条自主场景。初版3条警徽票轮次错误由core_supplement_v0.2修正，旧v0.1候选保留并标superseded，未重复入库。
- 86条准入均有SHA和具体模型语义审核理由，另记录旧30条superseded；非独立人工专家或Gold认证。来源显式白名单，不读取视频候选目录合并，video_rows=0。
- data/versions/dataset_v0.2.json、data/{gold,prepared}/dataset_v0.2和Classic训练messages完整冻结。专用训练消息移除扩展技能/角色内容，旧Benchmark Prompt/输入不变。
- 实际Tokenizer525～791 tokens，1024内零过滤/截断；独立配置configs/qlora_classic_v02.yaml冻结并在f89d910提交推送后才训练。
- v0.2同Base从头建Adapter，Rule→Strategy→Tactics各2步/1epoch；最佳均checkpoint-2。保持NF4、r8/alpha16、累积16、学习率5e-5，未使用旧v0.1 Adapter作为初始权重。
- Rule Loss3.0613351/峰值3414.2MiB；Strategy Loss3.7053094/3316.9MiB；Tactics Loss3.8002665/3443.7MiB。全部252个LoRA B非零；后两阶段各相对前阶段改变504个张量。完整checkpoint、final、配置、step/epoch、日志与SHA已保存。
- 2026-09-14发现评测停在14题且OS锁已释放，按原命令恢复，旧14文件SHA不变，只完成剩余22题；36/36已结束，运行锁空闲。
- 23条dev全部完成模型语义复核，v0.1/v0.2原始回答SHA已保存；13条test仅冻结自动评分，未用test文本修正数据。

## 当前正在进行的任务

本轮工程阶段已完成，无活动训练/评测/ASR进程。当前需要继续的是core失败诊断，而不是重新训练完成阶段或合入视频。先保存下一小实验的证据和单一变量选择，再考虑新运行；不改已冻结v0.2。

## 已运行测试、核验与结果

- 冻结前完整85项pytest通过、9条既有PEFT夹具警告。含CPU梯度/损失、LoRA保存恢复、断点等价、运行锁、core来源拒绝、Classic消息边界、冻结审核/补缺/篡改拒绝。
- 真实v0.2快照重跑16文件SHA/mtime不变；最终再次核验v0.1 manifest的19文件与v0.2 manifest的15数据文件；恢复前14个评测文件SHA不变。
- 三阶段final权重与最佳checkpoint-2的实际SHA相同，分别匹配导出报告；36个唯一case和run指纹正确，无保存结果截断。
- Base/v0.1/v0.2同协议1edff4b7a2e8ae73f0294e2988ae69f50cdc58b329eca266a755db848626d569，评分strict-actions-v1.1。

|指标|Base|v0.1|v0.2-core|
|---|---:|---:|---:|
|严格结构有效|33/36|27/36|34/36|
|合法动作|5/36|1/36|5/36|
|参考动作命中|2/36|0/36|2/36|
|反事实双题同时命中|0/4|0/4|0/4|

- v0.2参考命中分组为Rule0/12、Strategy0/8、Counterfactual0/8、Blind2/8；自动动作数量恢复到Base水平，未证明超过Base。
- 局部收益：猎人禁枪状态、女巫结构类型、部分公开主张核对、Blind预言家自主目标和票型公开追问。
- 仍失败：守卫连守/查验混淆、票权、屠边假设响应、动态改判、验人计划与结果区分、夜间信息公开。猎人新增频次/时机幻觉，狼队反事实否定确定队友知识，4个相关dev案例触发预先严重回归门禁；不是4个独立统计实验。
- 自动public_leak_flag=0不能否定语义复核发现的夜间公开泄漏。小样本、训练消息呈现变化、仅3个非零学习率参数步等限制不能用于反推唯一失败原因。
- CPU AdamW诊断校正预热解释：零学习率步仍累积动量，不能说只有最后microbatch影响参数；未重做4B训练，亦未声称是paged_adamw_8bit等价实验。

## 视频支线

- D:/BiliDownload只读索引185条、77.98小时，原catalog不重建。首局28287501902 / BV1p4N5eJEtL为9人预女猎，完整房规仍BOARD_UNKNOWN。
- 首局10/10 ASR块、1146.7406875秒处理完成但全文ASR_UNVERIFIED；已读37帧，源码料/完整转录留本地cache。已纠正ASR漏掉死队友信息，未据误转录误判玩家。
- data/candidates/video_distilled_v0.1独立保存M01～M04：3个B级TRANSFERABLE局部候选、1个LOW_QUALITY复盘负例候选；CLASSIC_GOLD/BOARD_SPECIFIC/正式训练样本/Critic通过均0。
- M01局部合法视角与机制剥离已记录，未观察实际动态改判，不标adaptive_strategy。M02复用已核票表，M03排除泛化毒人建议。非经典不丢局，原ASR/原话不直接变SFT。
- 独立池11源文档及4帧SHA核验通过；视频审核任务因额度结束，已落盘池可继续，不能冒称Critic已完成。
- v0.2有严重回归，暂不创建dataset_v0.3或合并视频。视频池可继续单独审核。

## 重要文件

- reports/v01_vs_v02.md：完整结论；reports/qlora_v02.md：自动逐题报告。
- reports/dev_semantic_review_v02.{md,json}：23条dev审核；reports/v02_acceptance_gate.json：预先门禁结果。
- reports/runs/{base_primary,qlora_v01,qlora_v02}：原始回答、protocol、summary、comparison。
- reports/dataset_v02_{core_review,coverage}.*、reports/v02_training_readiness.json、reports/v02_preflight_tests.json。
- reports/v02_final_verification.json、reports/v02_resume_20260914.json、reports/v02_warmup_interpretation.json。
- reports/training/{rules,strategy,tactics}_v02：训练与权重证据；源提交分别f89d910、dc7357a、014c168。
- data/versions/dataset_v0.{1,2}.json；data/{gold,prepared}/dataset_v0.2；configs/qlora_classic_v02.yaml。
- scripts/{prepare_core,check_core_ready,inspect_v02_dev,summarize_v02_gate}.py；src/werewolf_sft/{classic_messages,core_dataset,core_supplement}.py。
- docs/{data_version_policy,video_review_policy,disk_recovery,training,model_card}.md；视频池README和reports/video_distilled_v01.md。
- 大权重只在outputs/classic_v0{1,2}和cache，不进Git。v0.2 Tactics final SHA：f7b0075954f1d3daa59677f994e68ea931b830a7e732585e060f07f5e787f687。
- v0.1 Tactics final SHA仍为b1103c4bdb6600a04b3fa4dfe87de131a896a9a41e858fcdf342a8bce70cea6d。迁盘/跨主机须复制outputs/cache并按artifacts.json核验，单Git副本不足以恢复optimizer。

## 尚未完成任务与当前阻塞项

- 无外部工程阻塞；v0.2定向修复能力未达标。不能宣称高手模型或视频数据已证明有效。
- 下一core诊断：区分训练呈现差异、技能/状态读取和小步数日程问题，依据dev记录提出单一变量的小实验；不从test文本构造新训练数据。
- 独立人工语义盲审、未用于修正的保留集、真实复制粘贴对局验收仍未完成。
- 视频M01～M03完整历史校对、合法经典化与Critic待做，其他184局待审核。
- v0.3-video与Phase2镜隐均暂停，满足前置能力门禁后再考虑。

## 磁盘状态

2026-09-14最近检查：C42.60GiB、D100.95GiB，CONTINUE，无需迁移。大文件任务与恢复前继续检查；C不足时先保存/结束写入再按docs/disk_recovery.md迁全项目到D，D也不足才提醒租云服务器。无会话结束后的后台监控承诺。

## Resume Here

先读README、PROJECT_STATUS、DECISIONS、TODO和最近Git提交。v0.1/v0.2训练和所有36题评测均已完成，禁止重训重测或重建已有候选。当前无活动模型进程。

下一次直接执行的第一项任务：基于现有dev复核，检查Classic训练消息与冻结评测输入呈现的差异、技能状态读取，以及实际优化日程，保存reports/v02_core_diagnosis.md。先形成可审查的core诊断和一个变量明确的小实验，不重新选Base、不改已冻结v0.2、不使用test文本调参，也不合并视频。

```powershell
.venv/Scripts/python.exe scripts/check_disk.py --needed-gib 3
Get-Content reports/v01_vs_v02.md
Get-Content reports/dev_semantic_review_v02.md
Get-Content reports/v02_training_readiness.json
Get-Content src/werewolf_sft/classic_messages.py
Get-Content src/werewolf_sft/perspective.py
```

若只需重新核对门禁并恢复报告，可执行.venv/Scripts/python.exe scripts/summarize_v02_gate.py；它只读取已完成结果，不加载模型或重新生成回答。视频支线从data/candidates/video_distilled_v0.1/README.md恢复，独立完成合法经典化及Critic，保持v0.2准入为false。

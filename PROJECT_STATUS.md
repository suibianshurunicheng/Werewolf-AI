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

v0.2正式训练和原评测阶段已完成；当前投影诊断推理运行中，以OS锁和诊断progress为准。core离线失败诊断及23条dev单变量输入包已完成。独立运行器和5项必要测试已完成，实际权重/配置/冻结输入包核验通过；先提交检查点，随后只生成23条dev处理侧。

- 04608b1保存并推送完整v0.2评测。新增reports/v02_core_diagnosis.md/.json，核实训练/评测呈现差异、角色曝光和优化日程；未认定唯一因果。冻结v02_skill_projection_v0.1，仅裁剪无关skill_state，其余输入/系统/权重/生成/评分保持不变。

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

- 本轮离线核验通过：23条dev ID和原回答SHA一致，无assistant答案，投影外玩家视角与系统提示不变；固定Tokenizer控制559～766/处理459～666，均小于2048；v0.1/v0.2 manifest通过，三个新快照二次运行SHA/mtime不变。证据reports/v02_core_diagnosis_verification.json。未重新运行完整pytest或GPU生成。

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
- core诊断已完成；尚待实现独立运行器并执行v02_skill_projection_v0.1的23条dev处理侧推理/配对复核。它是探索性诊断，不替代原验收，不解锁视频。
- 独立人工语义盲审、未用于修正的保留集、真实复制粘贴对局验收仍未完成。
- 视频M01～M03完整历史校对、合法经典化与Critic待做，其他184局待审核。
- v0.3-video与Phase2镜隐均暂停，满足前置能力门禁后再考虑。

## 磁盘状态

2026-09-14最近检查：C41.74GiB、D100.94GiB，CONTINUE，无需迁移。大文件任务与恢复前继续检查；C不足时先保存/结束写入再按docs/disk_recovery.md迁全项目到D，D也不足才提醒租云服务器。无会话结束后的后台监控承诺。

## 投影诊断规则组检查点

规则dev 7题已生成并完成模型语义复核；全部7题结构有效，合法0→2、严格参考0→1，未知动作词4→2。守卫连守和夜间泄漏持续，猎人出现错误夜间技能措辞；部分状态复述改善。完整分支尚未判定，继续策略与反事实/Blind。运行已在reports/diagnostics/v02_skill_projection_v0.1逐题保存；日志progress为实时状态。

## 投影诊断策略组检查点

规则+策略12条dev已复核，另首个守卫反事实已保存。5条策略题出现更准确的主张转述，也有无依据支持8、pass退回none及继续不回应任务；不据未知词下降宣布能力提升。继续原运行完成6条反事实与5条Blind，再选择A/B/C。

## 投影诊断反事实检查点

18条dev已生成并完成模型语义复核；三组成对参考命中仍0/3。守卫B出现合法guard7但违背指定12任务，猎人B由查验变击杀仍有每轮击杀幻觉/shot未知词，狼队A具体投票却仍否定确定队伍信息。剩余5条Blind按原运行继续，全量后才定分支。

## Resume Here

已读取状态并完成独立运行器；5项测试通过，真实check-only确认23条dev与模型权重、配置、旧控制来源一致。提交后开始v02_skill_projection_v0.1。无需重训或重建输入包。

恢复第一项任务：读取reports/diagnostics/v02_skill_projection_v0.1/progress.json（若存在）和cases数量；用原命令继续，仅补缺。运行器OS锁拒绝重复进程；不得更换输出路径覆盖旧评测。

```powershell
.venv/Scripts/python.exe scripts/check_disk.py --needed-gib 3
.venv/Scripts/python.exe -X utf8 scripts/run_skill_projection.py
```

完成后正式报告必须覆盖23题前后语义、严格动作/合法性/未知动作词、技能/权限/队伍知识、公开边界/夜漏、角色分组与反事实配对。不读取test答案，不修改评分。按用户A/B/C结果进入新Classic Schema设计或Training Schedule Diagnostic；不得提前宣称根因或解锁视频/v0.3/Persona/Phase2/RL。

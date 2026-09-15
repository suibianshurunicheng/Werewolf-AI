# Werewolf-3.5B-Classic V1 工程状态

更新：2026-09-15。当前Phase：Training Schedule Diagnostic B，三阶段真实训练已完成，原23-dev生成/语义复核进行中（规则7题已完成）。历史主线：Phase 1，v0.2-core数据、三阶段正式训练、36题同协议评测和23条dev模型语义审核全部完成；定向修复能力验收未通过，v0.3视频合并门禁关闭。

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

B_warmup0 Rule→Strategy→Tactics已真实完成并逐阶段推送，实际6步/6非零LR更新。当前进程仅生成B final的冻结原23-dev；规则7题已全部语义复核，均未改善合法动作（A/B均0/7）。策略/反事实/Blind继续生成与审核；C/D尚未启动。无当前阻塞。

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
- 日程矩阵与预检已完成；B/C/D尚未训练，无新Adapter/训练日志/成绩。下一步B启动前dry-run与状态提交，再只执行B；C/D按B结果有条件推进。尚未证实日程是主因。
- 独立人工语义盲审、未用于修正的保留集、真实复制粘贴对局验收仍未完成。
- 视频M01～M03完整历史校对、合法经典化与Critic待做，其他184局待审核。
- v0.3-video与Phase2镜隐均暂停，满足前置能力门禁后再考虑。

## 磁盘状态

2026-09-15最近检查：C43.23GiB、D100.95GiB，CONTINUE，无需迁移。大文件任务与恢复前继续检查；C不足时先保存/结束写入再按docs/disk_recovery.md迁全项目到D，D也不足才提醒租云服务器。无会话结束后的后台监控承诺。

## 投影诊断最终结果

- 23条dev独立生成、零截断；原控制输出、23题输入、模型与配置SHA核验通过，v0.1/v0.2 manifest不变。恢复检查时已23/23完成，没有重复生成。
- 结构23→23、合法动作3→7、严格参考1→2、未知动作词14→10（分母23）。反事实双正确0/3→0/3，动作变化1/3→3/3不是正确重规划。
- 模型语义复核：4局部改善、8混合、4无变化、7退步；均保留。技能错误7/9→8/9、相关状态读取错误18/23→12/23、权限错误10/17→7/17、队伍确定知识错误3/4→4/4、夜间泄漏7/7→7/7。维度重叠、可评估分母不同，非独立人工评分。
- 已证实这批dev局部动作变化；有支持证据说明表示影响部分状态读取；暂不支持投影稳定修复核心技能；日程不足/遗忘/覆盖是否主因尚未验证。保守进入B，不声称全面无效或全面退化。
- 5项运行器测试此前通过；最终23题/指纹/权重/旧manifest核验通过，峰值2908.9MiB，生成时间合计1582.27秒。详见final_verification.json。
- 报告逐题列技能/权限/队伍知识/信息边界、角色分组和三组反事实。猎人技能宣告不自动按无遗言权判泄漏，未知维度记null。Blind-04含公开目标提示，命中不单独证明自主选人。

## 训练日程矩阵已保存

- reports/training_schedule_diagnostic_v01.md及training_schedule_v01_preflight.json记录A复用、B仅warmup=0、C相对B仅accum16→8、D相对B仅epoch1→2；输出目录独立。
- 三阶段计划optimizer步总数A/B/C/D=6/6/10/12，计划非零LR=3/6/10/12；只有A有真实训练日志，B/C/D仍未执行。B的LR计划为每阶段[5e-5,2.5e-5]，不是两个5e-5。
- 6个配置/协议/预检快照二次运行SHA/mtime不变；真实Tokenizer/冻结manifest/配置差异白名单/CPU scheduler与A日志核验通过。CPU scheduler检查不等于模型训练或8bit优化器等价实测。
- configs/diagnostics/schedule_v0.1/{B_warmup0,C_accum8,D_epochs2}.yaml，旧控制dev协议固定在data/diagnostics/training_schedule_v0.1/dev_protocol.json。
- 保留按阶段验证Loss选best/final的原规则，未来报告同时列真实总更新数与所选checkpoint的累计更新数；不把后续步计入早期best。阶段遗忘待用已有阶段Adapter的同dev对照验证，暂不合并阶段或改框架。

## B_warmup0 启动检查已完成（2026-09-15）

- 当前Phase：Training Schedule Diagnostic B。三阶段dry-run、冻结六文件SHA、仅warmup配置差异、86条真实tokenizer编码、原23条dev输入逐条一致性、GPU NF4前反向检查全部通过。
- 重要文件：reports/diagnostics/schedule_v0.1/B_warmup0/launch_preflight.json；scripts/preflight_schedule_b.py；scripts/audit_schedule_stage.py。
- 正在进行：提交启动检查后启动B Rule。尚未完成：B三阶段实际训练、23-dev生成与全量语义复核；无当前阻塞。
- 权重、冻结数据、旧评测未覆盖。启动检查记录C/D磁盘余量；当前无需迁移。


## B rules完成（2026-09-15）

- 实测optimizer=2、非零LR=2，每步LR=[5e-5,2.5e-5]；epoch=1，best=checkpoint-2，final与best SHA相同。
- trainLoss=3.273305，valLoss=2.971962；峰值显存=3414.2MiB；final Adapter SHA=b7c6e157a5bcf722fac53aa88e0e6fcfdad5049d5d6d2c9c9d505bd1ba6894fc。
- 两个checkpoint均完整校验；252个LoRA B矩阵从零变非零，后续步张量变化已核验。数据SHA、初始来源和全部日志见reports/diagnostics/schedule_v0.1/B_warmup0/rules/；能力尚未评测。


## B Strategy完成（2026-09-15）

- 实测2步/2非零LR=[5e-5,2.5e-5]，epoch=1，best=checkpoint-2，final同best。trainLoss=3.781560，valLoss=3.491447；峰值显存=3316.9MiB。
- final SHA=ea4799d04f57919ac7d92ec23cd856b6f2db3bc8c1a2ae1049f782c0dc2cb287；初始为B Rule final，504个张量实际改变；checkpoint逐文件SHA验证通过。完整日志/数据SHA/来源位于reports/diagnostics/schedule_v0.1/B_warmup0/strategy/。
- 复用原子推理运行器的5项测试通过，新日程入口/报告脚本编译通过；原运行器、评分和训练框架未改。

## B三阶段训练完成（2026-09-15）

- Rule/Strategy/Tactics均实际2 optimizer步、2非零LR步，三阶段总计6/6；全部best=checkpoint-2，链中保留全部6次有效更新。A对应6/3。
- Tactics final SHA=da5172fa95537b65a59c50e7edb603f96436dee051ed5de56daeadffda855777；trainLoss=3.705547、valLoss=3.568643；峰值显存=3443.7MiB。相对B Strategy改变504张量。
- 已验证：每步LR符合矩阵、checkpoint文件SHA、final=best、初始Adapter链、数据冻结SHA；新23-dev入口预检通过，复用原输入和原原子保存运行器（5项恢复/防篡改测试通过）。
- 重要证据：reports/diagnostics/schedule_v0.1/B_warmup0/training_report.md、training_comparison.json、各阶段目录以及dev/preflight.json；新训练全部完成，未生成任何新dev答案。

## B dev规则组检查点

规则7题已生成/逐题语义复核：2 mixed、3 unchanged、2 regressed；动作合法0/7→0/7、严格命中0/7→0/7，未知动作4/7→4/7。所有回答已原子保存。策略推理继续；这些是局部检查点，不是B最终结论。

## Resume Here

当前Phase：Training Schedule Diagnostic B同23-dev评测。规则7题审核已保存；下一项首先检查dev/progress.json和OS运行锁，若进程仍运行继续审核已生成且未审核的策略题；若锁已释放则用下列原命令恢复，自动跳过已完成题，不重跑训练。

```powershell
.venv/Scripts/python.exe -X utf8 scripts/run_schedule_dev.py --arm B_warmup0
.venv/Scripts/python.exe -X utf8 scripts/inspect_schedule_dev.py --arm B_warmup0 --limit 3
.venv/Scripts/python.exe -X utf8 scripts/summarize_schedule_dev.py --arm B_warmup0
```

推理输出：reports/diagnostics/schedule_v0.1/B_warmup0/dev/。只跑冻结23条dev，输入为旧control_messages，绝不采用投影输入；A复用原v0.2对应题输出。每题原子保存；原始输出和全部语义变化都保留。语义复核用review_schedule_cases.py写入，汇总对比A后决定分支。当前无阻塞，剩余为生成、23题全量复核、正式报告和分支决策。

若B一致改善且无新严重退化，记录有限支持证据并停止C/D；若B无稳定改善，完整报告commit/push后才进入C_accum8。不用13条test调参，不加入视频/Persona/v0.3。恢复首先读取README、三状态文档、日程报告和最近提交；旧A/v0.1/v0.2、投影诊断均已完成，禁止重训/覆盖冻结数据。

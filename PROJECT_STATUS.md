# Werewolf-3.5B-Classic V1 工程状态

更新：2026-09-13。当前Phase：Phase 1，v0.1验收未通过；dataset_v0.2规则与策略修正两个组件已完成，共56条候选，尚未冻结完整训练版。

## 已完成任务

- 仓库多阶段commit/push，沿既有Resume Here继续；没有重新初始化、重新选Base或覆盖冻结数据。
- classic_12 / ww-v1.0、严格玩家视角Schema、规则纯函数、8模板和训练/评测/人工推理工具。
- Primary Qwen/Qwen3-4B-Instruct-2507，固定revision cdbee75f17c01a7cc42f958dc650907174af0554；完整权重已缓存，不需再次下载。Backup仍未启用。
- dataset_v0.1为185条原创合成种子：42规则、18策略、125战术；场景族划分，无独立专家复核，不宣称3000+高质量对局。
- 独立Benchmark36题（rules12/strategy8/counterfactual8/blind8），23 dev/13 test；两方全部完成。没有把test文本用于本次修正建议。
- Rule：35 train/7 val，3step/1epoch，最佳Loss2.9687984，峰值3376.9MiB，252个LoRA B矩阵非零。
- Strategy：15/3，1step/1epoch，实际warmup0，最佳Loss3.0586383，峰值3315.8MiB，相对Rule改变504张量。
- Tactics：105/20，7step/1epoch，最佳checkpoint-7 Loss2.8225455，相对Strategy改变504张量。最后checkpoint保存后中断，已核验SHA补齐final导出，未重跑完成步。训练峰值未持久化，记null；不把恢复片段聚合loss/runtime冒充全程统计。
- 真实训练源Tactics为90a0416；完整导出及恢复工具提交e7785d0，规则组快照bf0638f，首局全音轨与画面纠错eecf348均已推送。
- 23/23 dev逐题语义复核及两方原始回答SHA已保存reports/dev_semantic_review_v01.*；这是model_review，不是独立人工盲审。

## 当前正在进行

v0.1训练、36题评测和首局10块ASR均已结束。本轮承接Resume Here完成第二个策略修正组件：24条/12对/10族，20训练侧/4验证侧；第一批规则32条保持原样。合计56条候选，完整81项测试通过，仍未开始v0.2正式训练。

- rules_batch_v0.1：32条规则候选、24训练侧/8验证侧，已冻结于1f19f28。
- strategy_batch_v0.1：14条Strategy与10条Tactics原创候选，重点为证据更新、声称与事实区分、队友失信后的公开切割及反证后的撤回。
- 当前正在推进完整v0.2的覆盖补齐与整合。两个组件均ready_for_training=false，无messages、未独立专家复核、不是最终Gold训练集。

## 已运行测试与结果

- 完整71项pytest通过（foundation37/dataset9/runtime21/finalization4）。包含CPU损失与梯度等价、LoRA保存重载、step1中断恢复至step4与连续训练等价、单step实际参数更新、运行锁与损坏checkpoint拒绝。
- 新增最终导出4测试：完整检查点幂等导出、未完成拒绝、SHA损坏拒绝、已有异内容拒绝；实际Tactics final与checkpoint-7逐文件SHA一致。
- 185种子实际Tokenizer长度649～931，1024内零过滤；三阶段均真实完成。CPU小模型测试不冒充4B训练成果。
- 两方36题完全相同协议指纹1edff4b7a2e8ae73f0294e2988ae69f50cdc58b329eca266a755db848626d569、评分strict-actions-v1.1；Adapter36个唯一case及run指纹核验通过，均未截断，没有生成失败/OOM。
- Base→Adapter严格结构有效33/36→27/36，合法动作5/36→1/36，参考动作2/36→0/36。参考动作分组Base为0/12、0/8、0/8、2/8；Adapter四组全0。反事实成对命中均0/4，动作变化2/4→1/4。
- Base生成速度中位6.22 tokens/s、PyTorch峰值2909.2MiB；Adapter中位5.18 tokens/s、峰值2973.4MiB。桌面/并行CPU媒体处理负载未控制，这不是严格吞吐基准；评测峰值不能代替Tactics训练峰值。
- 语义复核证实角色技能混淆、忽略技能/公开历史、编造规则、夜间公开泄漏。也有个别目标/公开表态局部改善，但整体没有证明专项能力提升。未知动作词导致接口混淆，0匹配不等于所有狼人杀理解为0。
- GitHub e7785d0的Ubuntu foundation与CPU Trainer工作流成功，证据reports/ci.json。

- 2026-09-13新增规则组件5项针对测试通过；完整测试76 passed、9条PEFT测试夹具警告，47.42秒。规则假设不注入真实底牌，夜间public_response为空，成对分组不跨训练/验证侧。

- 2026-09-13第二组件5项专项测试通过；完整81项测试通过、9条既有PEFT夹具警告，安静输出无耗时统计。覆盖成对信息先后、死目标拒绝、狼队私有名单与公开发言分离、场景族隔离、幂等补缺与损坏拒绝。
- 第二组件真实重跑5个文件SHA/mtime不变；23个先前冻结文件及2个manifest也不变。报告见reports/dataset_v02_strategy_batch.*。

## 视频审核

- D:/BiliDownload只读索引185条、77.98小时；catalog_v0.1不重建覆盖，弹幕不是发言逐字稿，多视角game_family仍需确认。
- 首局28287501902 / BV1p4N5eJEtL：9人预女猎阵容，完整房规仍BOARD_UNKNOWN。累计37帧实际阅读；全音轨1146.7406875秒、10/10块ASR处理完成，全块指纹/SHA核验，首块复用确认。
- ASR全文留cache/media/28287501902/transcript_v0.1，状态仍ASR_UNVERIFIED。Git只保存asr_evidence_v0.1配置/哈希/覆盖与少量审核引用，不上传整段转录或素材。
- review_v0.1/v0.2/v0.3：3条B级TRANSFERABLE候选M01～M03，1条LOW_QUALITY复盘负例M04，CLASSIC_GOLD/BOARD_SPECIFIC/正式SFT入库均0。不是完整全局玩家评级；其余184条未审核。
- 两轮票表、刀7/毒4字幕已核；382/406秒主持字幕支持9号→8号发言顺序，箭头冲突保留；754/755秒证实ASR漏掉“队友出局、只剩自己”，未据误转录误判玩家。
- 遵守docs/video_review_policy.md：非经典不丢局，机制剥离、合法当时视角、避免结果/事后偏差；经典改写须验证后才入新数据版本。

## 重要文件

- README.md、DECISIONS.md、TODO.md及docs/{model_card,training,evaluation,video_review_policy,disk_recovery}.md。
- configs/qlora_classic.yaml：NF4双量化、r8/alpha16、batch1/累积16、1024、1epoch、BF16自动、无packing。固定CPU媒体配置configs/media_asr_v01.json。
- data/versions/dataset_v0.1.json，data/{gold,prepared}/dataset_v0.1；禁止覆盖。
- data/candidates/dataset_v0.2/strategy_batch_v0.1/{samples,train,validation}.jsonl、pairs.json与manifest.json；src/werewolf_sft/strategy_repairs.py、tests/test_strategy_repairs.py、reports/dataset_v02_strategy_batch.*。
- reports/dataset_v02_rules_batch.*、src/werewolf_sft/rule_repairs.py、tests/test_rule_repairs.py记录第一批规则组件及恢复校验。
- reports/{base_model_baseline,qlora_v01,base_vs_qlora,dev_semantic_review_v01}.md及相关JSON；reports/runs/{base_primary,qlora_v01}完整case/原回答/progress/summary。
- reports/base_progress.*与qlora_progress.*为早期partial历史，不是最终报告。
- reports/training/{rules,strategy,tactics}_v01含配置、结果、日志、权重SHA；Tactics额外finalization.json。
- scripts/finalize_training.py只补全已完成步数的导出；scripts/export_training.py导出紧凑证据。正常训练恢复仍由train_qlora --resume处理。
- reports/media/28287501902/{review_v0.3.md,review_v0.3.json,probe_v0.3.json,asr_evidence_v0.1.json,asr_corrections_v0.1.json}。
- 大权重与缓存仅在本机outputs/cache，不进Git。跨主机必须复制并按reports/training/*/artifacts.json校验；仅Git副本无法恢复optimizer/Adapter。

## 尚未完成任务与当前阻塞项

- 没有外部阻塞，但当前模型未达能力验收。185条小种子、11个计划优化步的结果不能被包装为高手模型；未证明退化的唯一原因。
- 按已保存dev诊断生成并冻结dataset_v0.2，做第二轮训练及评测；规则32条与策略/战术24条修正已完成，接着补覆盖缺口并整合。
- 若另立明确动作词典/清理非经典提示词的新协议，必须对Base与Adapter共同评测并另版保存，不能覆盖v0.1结果或改变一方Prompt。
- 独立语义复核、保留集及真实人工复制粘贴对局验收；Phase2镜隐仍暂停。
- 首局M01～M03完整逐字稿/当时合法历史校对、经典改写和视角验证，后续184素材审核。

## 磁盘状态

2026-09-13末次检查：C44.70GiB、D101.48GiB，CONTINUE，无需迁移。恢复和大文件处理前检查。C不足时先保存checkpoint、结束活动写入，再按docs/disk_recovery.md迁整个项目到D；D也不足提醒租云服务器。没有声称会话结束后后台监控。


## v0.2-core与视频池隔离（2026-09-13）

用户固定dataset_v0.2为v0.1定向修复实验；视频仅进入data/candidates/video_distilled_v0.1/，禁止提前合并。沿当前覆盖缺口补齐并逐条审核core，冻结messages/Tokenizer长度/训练配置，commit后正式QLoRA，同v0.1协议比较。v0.3须等待v0.2比较且没有明显退化；具体门禁见docs/data_version_policy.md。

## Resume Here

先读取README、PROJECT_STATUS、DECISIONS、TODO和git log -5 --oneline，再检查git status。v0.1三阶段及两方36题已完成，不重训、不重测、不重新选Base、不覆盖数据。已无本轮活动训练/评测/ASR进程。

第一项工程任务：基于已冻结的rules_batch_v0.1与strategy_batch_v0.1做完整v0.2能力覆盖表，再新增独立场景族补缺。第一批守卫记忆、自救轮次、角色能力边界仅在验证侧；第二批合法验人备选、票型关系修正仅在验证侧，战术没有验证族。保持现有族划分，不能拆同对、只换座位伪造独立场景或为分数改分组。新样本另建组件，不重复生成已有56条。

```powershell
.venv/Scripts/python.exe scripts/check_disk.py --needed-gib 3
Get-Content reports/dataset_v02_strategy_batch.md
Get-Content data/candidates/dataset_v0.2/rules_batch_v0.1/manifest.json
Get-Content data/candidates/dataset_v0.2/strategy_batch_v0.1/manifest.json
Get-Content reports/dev_semantic_review_v01.md
```

按需校验已有组件：

```powershell
.venv/Scripts/python.exe scripts/prepare_dataset.py --version dataset_v0.2
.venv/Scripts/python.exe scripts/prepare_dataset.py --version dataset_v0.2 --component strategy
```

两条命令分别仅补缺/验证规则和策略组件，不是完整v0.2训练集。已有内容复用，异内容拒绝；不修改旧seed_data、v0.1消息或Benchmark。数据原始结构仍有未激活的扩展字段，最终Classic消息必须裁剪非经典内容。覆盖补齐后依次完成独立语义审核、Classic专用消息、Tokenizer长度、训练配置与dry-run，冻结完整版本并commit后才正式训练。新Prompt协议若用于评测，Base与Adapter必须共同另版测量，不覆盖v0.1。

视频并行支线从reports/media/28287501902/review_v0.3.md与asr_evidence_v0.1.json继续校对M01～M03，无需再次下载或转录首局。必要时用.media-venv/Scripts/python.exe scripts/probe_video.py --video-id 28287501902 --times <秒数>补帧，旧帧复用；新审核另起版本，不擅自填补房规或私密信息。

Tactics final权重SHA b1103c4bdb6600a04b3fa4dfe87de131a896a9a41e858fcdf342a8bce70cea6d，本机outputs/classic_v01/{rules,strategy,tactics}保留完整checkpoint和final。跨主机或迁盘必须复制、验证后再切换；Git仓库只有报告和哈希。

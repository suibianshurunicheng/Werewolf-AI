# video_distilled_v0.1 隔离审核池

本目录保存真实/AI 视频的策略证据、审核记录和改写提案，当前没有 SFT 样本、messages 或训练切分。永远不得合入 dataset_v0.2；v0.2 是针对 v0.1 已暴露缺陷的定向修复实验。

当前复用 28287501902 / BV1p4N5eJEtL 的 M01～M04，不重复计数、不新增 ASR、不扩大视频扫描。四类数量为 CLASSIC_GOLD 0、TRANSFERABLE 3、BOARD_SPECIFIC 0、LOW_QUALITY 1；Negative 候选 1 是 LOW_QUALITY 的子集。原局是 9 人预女猎，完整规则仍 BOARD_UNKNOWN。非经典板子并未整局丢弃。完整音轨处理过不等于逐字稿核验或整局审核完成。

index.json 是片段索引和流水线状态；evidence_manifest.json 保留旧证据文档指纹、视频流既有指纹及本轮实看四帧。M01_reconstruction_v0.1.json 明确只重建已观察的局部公开信息，保留后台 Prompt、剪辑完整性缺口，完成机制剥离与经典改写提案；没有伪造原局完整合法视角。原始 ASR、字幕或玩家原话未复制为训练答案。

M01～M03 仅 B 级局部候选，M04 为 D 级复盘错误。M01 只观察到愿意调整，不能标记已完成 adaptive_strategy。M02 的首日票表已在 review_v0.2 补证；其后次日投票不可回填 620 秒前的玩家输入。M04 的矛盾不能当早期玩家的身份真值，也不能把 ASR 漏句当玩家错误。所有 Critic 均 PENDING，Gold 入库 0，正式训练样本 0。

未来候选必须依次完成：原始局面 → 当时合法视角 → 策略质量 → 机制剥离 → 核心抽象 → 必要的经典改写 → Critic → 候选训练样本。没有证据的项目明确 pending；不按最终胜负评级。对不依赖原板特殊技能的优秀片段保留迁移价值，对依赖特殊技能的内容保留 future_board_specific，低质量局部不作正向答案。

此轮快照由 checkpoint.json 保护。校验器只读，不重跑转录、下载或覆盖已有材料。追加审核使用新版本文件和新 checkpoint；本轮文件不静默改写。源 cache 缺失时默认仍可核对仓库文档，实看帧验证应在媒体缓存可用时运行 --with-local-frames；缺缓存不是已验证。

## Resume Here

先执行隔离快照验证：

    .venv/Scripts/python.exe data/candidates/video_distilled_v0.1/verify_pool.py --with-local-frames

接着读取 M01_reconstruction_v0.1.json 的 critic_handoff：独立构造一个有明确合法公开依据的 classic_12 候选并注明新增合成假设；不得硬保留原来的站边结论。若仍只有“愿意改判”而没有值得正向学习的选择，保留审核记录即可，不凑 Gold。完成后才做 Critic，仍不进入 v0.2。

其后按旧证据续补 M02 原狼私有信息、M03 公开推理细节；无需重复 10 块 ASR。待 v0.2 正式训练和同协议 Benchmark 完成、确认至少没有继续明显退化，再考虑独立 dataset_v0.3，并比较 v0.1 / v0.2 / v0.3-video。

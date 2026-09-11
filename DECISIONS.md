# 工程决策

## dataset_v0.1检查点

- 首版185条原创种子，25战术各五条件、18策略主题、42规则；不靠座位轮换或大量改写凑数量。
- 同scenario_id整体分训练/验证；36题Benchmark独立编写，4对仅变一个可见字段，dev/test预先固定。
- Gold未做独立Critic和人工复核；参考动作不是完整策略质量指标。实际46项测试通过。
- Primary revision固定cdbee75f17c01a7cc42f958dc650907174af0554。CUDA第二次下载成功且已识别GPU。

## 远程仓库与下载恢复

- 用户指定 git@github.com:suibianshurunicheng/Werewolf-AI.git。插件确认空仓库，SSH ls-remote 成功，保留现有本地提交并正常 push，禁止 force push。
- CUDA wheel 第一次下载截断且哈希不符，禁止跳过校验或报告安装成功；升级 pip 25.3 后使用 resume-retries。
- 已保存 r8/1024 的 4GB 起始配置与 12/16/24GB、3B 备用配置；它们尚未通过模型训练实测，不能当成显存保证。

## Schema 与基础测试检查点

- 严格 JSON Schema：禁止未知字段；私有事实按角色授权，事件有证据 ID 与轮次，不接受任意全局身份表。
- 输出独立保存 analysis、identity_reads、wolf_pit、god_pit、round_assessment、strategy、action、public_response。
- 模板生成脚本可重复运行但不覆盖已有异内容文件。当前 1 条 example 只用于演示/测试，不冒充 Gold 数据集。
- 37 项测试真实通过；纯文本语义泄漏仍需人工审核，正则无法证明不存在所有泄漏。

## 可恢复执行与当前底座

- 用户要求每个独立阶段更新三份状态文件并 commit，耗时工作前先保存。数据版本目录和哈希禁止隐式覆盖，评测逐条保存并核验运行指纹。
- Primary 固定 Qwen3-4B-Instruct-2507（成熟纯文本、非 thinking 输出）；Backup 为 Qwen2.5-3B-Instruct（较小、限非商业研究）。详见 docs/base_model_selection.md。
- CUDA 11.8 / PyTorch 2.6.0 用于现有 546.30 驱动，CPU 安装不算 GPU 训练环境。
- ww-v1.0 是经典项目房规；镜隐接口为 Phase 2 草案，不能进入 Phase 1。
- 初始 checkpoint 仅通过语法检查，不把尚未完成的 Schema 和测试说成可运行工具链。

## 2026-09-10：用户变更为 Werewolf-3.5B-Classic

- 以最新附件替代模型规模和阶段范围：3B～4B、classic_12 优先。
- 保留现有通用代码，包名改为 werewolf_sft；不重复建立目录。
- 镜隐迷踪降级 Phase 2，只保留规则调研与扩展接口，数据准备和训练入口禁止混入。
- 本机先尝试 r=8、batch=1、NF4、double quant、gradient checkpointing。不能根据显存估算代替真实尝试或伪称 OOM。

## 2026-09-10：范围与真实性

- 在当前工作目录直接建设一个标准 Python Repository，不创建第二套工程。
- 只实现两个固定板子的玩家视角决策、静态 Benchmark、人工复制粘贴推理；不实现自动竞技场或 Web UI。
- 数据、规则、实验按版本与哈希追踪；合成数据明确来源，不冒充真人对局或人工复核。
- 4GB GPU 不能承担正式 7B～9B QLoRA。尽可能运行 CPU 工程测试与小模型训练链路验证，后者不算专项模型训练结果。

## 2026-09-11：工具链验证与本地加载

- 保持原Base、dataset_v0.1和ww-v1.0，不重做已完成数据。固定revision权重已完整下载。
- 实测所有185样本长度649～931，保留max_length1024且overlength=reject，不需删样本。
- 生成上限在首次Base之前从384改768，为8字段JSON留余量；Base和Adapter必须同协议。不能只给微调模型更多token。
- 小数据每阶段只有少量step，save/eval从10改每1优化step，保证中间恢复和最佳checkpoint。
- 使用原生Qwen logits_to_keep仅计算assistant监督位置、分块softmax；标准loss与梯度等价测试通过。避免大词表全序列logits占用，非截断训练。
- Tokenizer在4.57.6即使local_files_only仍有Mistral探测联网；用已固定的缓存snapshot绝对目录加载，验证离线可运行。
- 评测单题JSON原子落盘为事实来源，JSONL为导出；run指纹固定题目、渲染输入、Base revision、量化与生成参数、Adapter摘要，防止混跑。
- CUDA/NF4微测试通过不等于4B整模型训练成功。60项软件测试与Rule dry-run通过；正式Benchmark尚未开始。

## 运行锁与精确恢复

- 工具链3110940已推送后开始完整Base，已有逐题真实输出。当前运行早于运行锁补丁，恢复须先确认旧进程是否仍活跃；后续运行自动取得OS排他锁，进程异常退出会释放，不依赖聊天或陈旧PID文件。
- CPU小型Qwen3+LoRA测试中断于step1，恢复optimizer/scheduler/RNG后跑到step4，与连续训练参数和验证loss一致；不是4B训练结果。
- 新增GitHub Actions轻量数据测试和CPU Trainer测试；远端CI结果尚待检查。

## Base部分快照

- 规则12题已生成完，完整36题仍在运行。checkpoint_evaluation读取已原子保存的题目，生成单独partial快照，绝不覆盖活动progress或伪造完整summary。
- dev输出暴露动作词汇接入与规则能力混淆。保持当前v0.1协议原样完成，明确不以精确动作匹配独立证明专项能力；正式能力验收需语义审核或给两方同一动作字典后另版重测。
- GitHub 2e55c70的Linux轻量和CPU Trainer CI已成功，证据reports/ci.json。

- strict-actions-v1.1只增加未知动作词诊断列，原精确匹配定义、Prompt、参考答案和原始生成全部不变。没有加入针对Base的别名放宽。当前生成进程结束后用--score-only统一重算；Base和Adapter比较强制相同scoring_version。

## 训练前完整性与失败证据

- 训练入口逐个核验冻结版本清单，禁止文件改变后沿用旧dataset_version。实际Rule dry-run仍35/7零过滤。
- 每个checkpoint的Trainer保存完成后，写入文件SHA清单及完成标记；恢复只选择最新完整匹配点，跳过断电残缺或损坏目录，不删除旧数据。
- 训练manifest记录training/modeling/encoding/dataset源代码哈希，避免代码变化后冒称精确恢复。
- 每次训练失败独立写入带UTC时间与唯一ID的reports/training_attempts，包含config、dry_run标记、最后阶段和原始异常文本；不只保留被覆盖的最后一个错误。
- 模型离线加载后恢复上游模型标识，避免Adapter把本机缓存绝对目录作为未来Base地址。
- 完整65项pytest通过。

## 完整Base先于训练

- 36/36题实际生成完成，再统一strict-actions-v1.1评分；没有跳题、截断或OOM。中位6.22 tokens/s，PyTorch峰值2909.2MiB。
- 精确参考匹配rules0/12、strategy0/8、CF0/8、blind2/8；33/36输出满足严格结构。未知动作词诊断保留原结果，不冒称Base不懂全部规则。
- 先保存完整Base commit，再实际Rule QLoRA；不得跳过这道门禁。空Benchmark配置现在也明确拒绝。

## 本机Rule QLoRA真实完成

- 按52514c6源代码从固定4B Base实际训练35条/验证7条，r8、1024、BF16、NF4双量化、累积16，3step/1epoch完成；峰值3376.9MiB，没有OOM。
- checkpoint-3验证Loss2.968798，完整校验通过；252个LoRA B矩阵非零。日志/参数/哈希导出reports/training/rules_v01，实际权重留outputs。Loss下降不当作狼人杀能力提升。
- PEFT保存会尝试请求上游main/config.json，失败后继续并成功保存。后续训练CLI在导入HF库之前启用offline，下载仍单独prepare_model。
- 发现Strategy只有1个优化step，ratio0.05会向上取整成1个warmup step，唯一更新lr=0。必须在Strategy开始前限制warmup小于总step，并保存effective_schedule；不让空更新冒充训练。
- 跨主机恢复必须复制大权重目录并校验哈希，Git仓库中的报告不能代替实际Adapter/optimizer文件。

## Strategy调度与视频审核新增要求

- warmup=min(ceil(total_steps*ratio), total_steps-1)，effective_schedule写入manifest；1 step阶段有效warmup为0，已测试实际参数发生变化。完整67项测试通过，Strategy实际编码15/3、1 step、0 warmup。
- 保留已完成Rule，不因该修复重训。以后Adapter配置也显式写固定Base revision。
- 用户新增视频高级审核：策略质量优先于板子名称，未知板子不丢整局；跨板机制剥离、玩家当时合法视角、避免结果/事后偏差。审核候选单独版本化，未经经典兼容校验不进入现有SFT快照。
- 用户授权C盘空间不足时迁整个项目到D盘；D盘也不足则提醒租云服务器。先持久化并结束活动写入、复制校验后再切换，不在训练或下载写入过程中搬目录。当前C49.17GiB/D100.84GiB，无需迁移。

## Strategy完成与素材索引检查点

- ba11f0a调度下Strategy实际1step/1epoch、LR5e-5；相对Rule有504个张量改变，峰值3315.8MiB，无OOM。保留原185条种子，Loss不代表能力提升。
- 视频catalog_v0.1只记录来源/元数据哈希/流文件大小与9字节包装观察，不根据标题猜板子或评级。185条全部NOT_REVIEWED，弹幕不作玩家逐字稿，多视角同局必须确认game_family后才能划分数据集。
- CPU媒体处理放独立.media-venv，避免改动已验证的cu118训练依赖；安装版本记录requirements-media-lock.txt。原视频保持D盘只读，缓存转录不上传到公开Git。
- check_disk在恢复/大文件操作前估计新增占用并保留5GiB，返回2即停止后续大文件操作；只是执行时检查，不声称会话结束后后台监控。C48.64GiB/D100.84GiB无需迁移。

## 首局实际画面局部审核

- probe_video保持D盘源只读，缓存去除实际观察到的9字节包装，记录原文件/容器/帧SHA；重复请求验证后复用，不覆盖异内容。
- BV1p4N5eJEtL实际9人预女猎，完整房规仍BOARD_UNKNOWN；不是因板型拒绝，已保留3条B级迁移核心候选和1条D级赛后复盘负例。只核读18个时间点，不伪称完整视频或音频审核，不纳入冻结SFT。
- 赛后身份只供审核元数据核对；400秒指示箭头与文字说话者冲突、840秒复盘死因自相矛盾，都需要核查，不能借上帝视角补齐合法输入。
- Tactics已从Strategy续训，105/20、计划7step；存活进程不得重复启动或修改其源代码/config。每个完整checkpoint自动保存。

## 恢复检查与首局票型补证

- 原Tactics进程继续，checkpoint-3完整SHA核验成功；不重训Base/Rule/Strategy，不改活动训练配置。
- 首局review_v0.2新增13帧，核实首日8投1、次日4投8及夜间刀7/毒4字幕。候选数量不重复计数，后续票型不前灌620秒输入。
- 转录辅助模型固定Systran/faster-whisper-small revision 536b0662742c02347bc0e980a01041f333bce120（公开API核实），CPU int8/2线程、120秒分块两侧2秒重叠，只做证据检索；不是专项Base更换。chunk原子保存、内容哈希/配置/源音频/模型/代码指纹恢复，完整文本留本地cache。

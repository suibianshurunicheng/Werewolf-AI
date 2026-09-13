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

## Tactics完整检查点最终导出恢复（2026-09-12）

- 训练从checkpoint-4恢复后已完成7/7优化步、1epoch及验证，checkpoint-7最佳Loss2.8225455；原进程在final导出前结束。只补最终导出，不重新训练已完成步。
- finalize_training先取得运行锁，校验计划步数、完整文件SHA、manifest、最佳验证指标及路径，再按哈希复制最佳Adapter/Tokenizer。已有相同文件复用，异内容拒绝，optimizer仍保留原checkpoint。finalization.json记录复制来源和SHA，export_training输出紧凑审计证据。
- 原进程训练峰值未写入最终报告，保存null并说明；恢复片段Trainer聚合train_loss/runtime不当作全程统计，逐步日志照原样保留。
- 相对Strategy有504个张量变化、252个LoRA B矩阵非零；真实final与checkpoint-7权重SHA一致。完整71项测试通过；未据验证Loss宣称博弈能力提升。
- Adapter采用已冻结36题/生成协议及strict-actions-v1.1与完整Base对比，不改Prompt/标签补救Base分数。数据仍dataset_v0.1，后续只使用dev失败修订v0.2。
- 首局ASR模型已就绪、1/10块完成，存在“警徽流先报”等识别错误；只能作检索证据，另存校对后再考虑片段入库，不覆盖原块或重复生成。

## Adapter规则组与ASR续作检查点

- 规则12题已全部生成；qlora_progress为13/36题部分快照，不伪称完整评测、不覆盖活动progress。原36题和Base输出不变。
- ASR第二块单独续作成功，第一块内容哈希与先前一致。原始“锦辉刘先暴”在10秒画面中央文字对应“警徽流先报”，另存asr_corrections_v0.1；这是字幕对齐，不声称独立听音核验。口头提到警徽不证明实际有警长竞选，“恋人”等ASR错误不作为新角色证据。
- e7785d0的GitHub push工作流成功，CI证据更新reports/ci.json。

## 首局全音轨处理完成与ASR漏句纠正

- 10/10块共1146.7406875秒全部处理，文件与内容SHA核验，首块未被覆盖；原逐字稿留本地cache，公开Git仅配置/哈希/少量纠错和审核报告。
- 新增6帧累计37帧。382/406秒主持字幕支持383～405秒归9号、随后归8号；保留箭头冲突，后台私密Prompt不凭空补齐。
- ASR把749～759秒狼夜发言压缩，漏掉754/755秒明确显示的“2号和8号已经被投出局”“现在只剩下我一个人”。因此不新增“忽略死队友”的LOW_QUALITY标签。这是源核验推翻自动转录假设的实际例子。
- 785/833秒补证既有M04复盘与夜间自述/已核死亡次序冲突，不重复计数。仍3条迁移候选+1负例候选、入库0；全音轨处理不等于完整逐字稿已校对或全局高级玩家认证。

## v0.1完整比较未通过能力验收（2026-09-12）

- Adapter36/36全部生成、无截断/生成失败，与完整Base同协议同评分；结构有效33→27、合法动作5→1、参考匹配2→0（分母36），成对反事实均0/4。真实训练成功不等于能力提升，当前不得宣传为高手模型。
- 23条dev语义复核及回答SHA完整保存，不读取test文本作为修正来源；个别目标/公开表态有局部改善，但存在角色技能混淆、状态忽略、规则幻觉和不响应任务。0精确匹配也不代表所有语义判断为0。单一策略参考非穷尽最优解，不事后改冻结评分。
- 夜间公开技能内容仍存在，有限正则的0泄漏标记不能当成安全证明。生成吞吐测量受桌面/CPU媒体负载影响，不能直接归因为Adapter。
- 保留v0.1全量证据和三阶段权重，不重复训练或重新选Base。延续原TODO，从dev失败类型构造独立场景族的dataset_v0.2，先做一个完整的小批规则修正阶段，再扩展策略/战术。
- 当前prepare_dataset仅支持v0.1。新增v0.2必须另路径并验证旧快照/Benchmark不变；动作词典或Classic专用Prompt如改变，必须另版协议两方同测，禁止覆盖旧结果或只改一方。

## dataset_v0.2第一批规则组件（2026-09-13）

- 按Resume Here仅完成规则修正小阶段：32条原创样本、16组成对条件、10个场景族；没有复制Benchmark答案、用test修正或把座位排列扩充成虚假规模。
- 独立组件data/candidates/dataset_v0.2/rules_batch_v0.1冻结，完整v0.2未冻结、ready_for_training=false；prepare_dataset --version dataset_v0.2明确只处理该组件。后续扩展另建组件，不能改当前快照。
- 成对对照包含改变动作的权限/目标条件，以及猎人轮次改变但动作不变的控制。首夜自救轮次变化时同步合法刀口通知时间，避免错误地引入过期通知。胜负仅作为假设题，不填入真实底牌。
- 复用save_snapshot与split_by_family。10族按原固定哈希分组：24训练侧/8验证侧，相关条件与同对成员不跨集合。整组守卫、自救与角色边界落入验证侧，正式训练前必须审核完整覆盖并补独立场景，不能为提高分数临时改分组。
- 本批不生成messages，避免把旧共用Prompt及未激活扩展字段误作Classic最终输入。以后确定Classic格式并裁剪非经典内容，若改评测协议须两方共同另版测量；v0.1数据/Prompt/Benchmark保持原样。
- 5项针对测试及本机真实重复执行通过：5组件文件SHA/mtime未改变、19个旧冻结文件核验；旧文件损坏先拒绝，缺失组件成员只补缺，异内容拒绝。未声称数据校验等于独立专家审核或模型能力改善。

- 本阶段完整pytest实测76 passed、9条PEFT测试夹具警告，47.42秒；没有重新运行模型Benchmark或开始训练。

## dataset_v0.2策略修正第二组件（2026-09-13）

- 沿第一组件的下一任务完成24条原创候选、12对、10族，Strategy14/Tactics10；新路径strategy_batch_v0.1，不修改已冻结rules_batch_v0.1、v0.1或Benchmark。CLI新增--component strategy，默认仍只处理规则组件，避免旧恢复命令改变含义。
- 使用顺序证据更新对：后一条保留前一条完整可见历史，只增加新公开记录；验人目标出局同步存活列表。私有技能事实不变，发言和验人计划不是已经获得的结果；公开原文核对也不认证隐藏身份。
- 修正目标包含撤回错误质疑、声称来源分层、未来计划与历史结果区分、暗牌狼数不确定性、票型关系更新、狼队切割与对手识破后的调整。相同speak动作也可有不同策略，不把动作类型不变误判为没有更新。
- 相关狼队维护/切割/反证三对共用wolf_binding族，禁止拆分泄漏。固定哈希得到20训练侧/4验证侧，战术10条全部在训练侧；不靠重命名族把它们移入验证，应新增真正独立战术场景。规则和策略的仅验证能力也要独立补训练覆盖。
- 源为original_synthetic，质量分是作者自评；非B站Gold，未独立专家审核。自动Schema、合法动作与私有字段检查不能证明策略最优或无所有语义泄漏，不据此宣布训练就绪。
- 写入前后核验先前两份manifest覆盖的23文件；真实重跑确认5个新组件文件与25个先前文件/manifest的SHA和mtime不变。缺失仅补缺、异内容先拒绝。新增5测试，完整81项测试通过，9条既有PEFT测试夹具警告；输出未记录耗时，报告记null。
- 两批合计56条候选，仍不生成最终messages或启动训练。下一阶段先补完整覆盖，再确定版本化Classic提示格式、实际Tokenizer长度与配置/dry-run。Base、QLoRA和规则版本继续沿用既定选择，不重复调研。

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

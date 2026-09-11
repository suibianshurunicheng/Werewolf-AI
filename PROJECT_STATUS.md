# Werewolf-3.5B-Classic V1 工程状态

更新：2026-09-11。当前 Phase：Phase 0 工具链验证完成，进入 Phase 1 Base Benchmark。

## 已完成任务

- 保留原项目与4个已推送提交，当前仅3B～4B/classic_12；镜隐暂停。
- 冻结ww-v1.0规则、严格玩家视角Schema、8份复制粘贴模板。
- dataset_v0.1：42规则、18策略、125战术，共185条原创种子；独立36题Benchmark，4对单变量反事实。未独立人工复核，不冒充3000条Gold。
- Primary Qwen3-4B-Instruct-2507 revision cdbee75f17c01a7cc42f958dc650907174af0554 权重和Tokenizer已下载完成；不需要再次下载或选型。
- RTX3050Ti 4095.5MiB，torch2.6.0+cu118、BF16支持、NF4前向反向实测通过。
- 实现配置校验、assistant-only编码、顺序QLoRA/LoRA、checkpoint恢复、推理、逐题评测、Markdown报告及CPU合并入口。
- README、训练、人工使用、模型卡已补齐。

## 当前正在进行

保存工具链检查点，然后首次完整运行Base。尚无4B模型Benchmark或正式QLoRA结果。

## 尚未完成任务

- 完整Base Benchmark及失败分析。
- 实际4GB QLoRA尝试及有必要时按顺序调整显存配置。
- Rule→Strategy→Tactics Adapter及相同Benchmark比较。
- dev失败驱动dataset_v0.2、第二轮训练、保留集和人工对局验收。
- 4GB/12GB/16GB/24GB全模型训练的实测容量与速度。

## 已生成的重要文件

- src/werewolf_sft/：rules、perspective、validation、schema、dataset、seed_data、benchmark_data、config、encoding、modeling、runtime、evaluation、reporting、training。
- scripts/：prepare_model、prepare_dataset、validate_dataset、convert_messages、check_environment、check_lengths、train_qlora、train_lora、inference、evaluate、merge_adapter。
- configs/*.yaml、data/gold/dataset_v0.1、data/prepared/dataset_v0.1、data/versions/dataset_v0.1.json、eval/*.jsonl。
- reports/environment.json、reports/token_lengths.json、reports/models/Qwen3-4B-Instruct-2507.json、reports/toolchain.md。
- 本地cache/huggingface保存固定revision权重，不提交Git；outputs保存未来训练状态，同样忽略。

## 已运行测试和结果

- 60项pytest全部通过（原46项+14项工具链测试），测试进程退出0。小型随机Qwen3的优化loss及全部参数梯度与标准实现一致；LoRA一次更新后保存重载输出一致。它们不是4B专项训练成功证据。
- 实际NF4微测试前向、反向梯度有限，详见environment。
- 实际Tokenizer：rules649～775，strategy730～751，tactics829～931 tokens；Benchmark输入最长766。全部训练样本适配1024，不截断。
- Rule dry-run成功：35 train、7 validation，零过滤。
- 发现并修复Tokenizer在local_files_only下仍探测网络的问题，改为固定revision本地目录加载。
- 发现并修复评测协议字典共享引用，防止后改配置时指纹快照跟着变化。

## 当前阻塞项

暂无外部阻塞。整模型4GB推理/训练容量尚未验证；不能预报OOM或伪称训练成功。GitHub SSH可用，禁止force push。

## 下一步具体任务

1. 保存并推送当前工具链commit。
2. 完整运行Base评测，逐题持久化；发生异常保留failure.json并修复后原命令续跑。
3. 基线完成后更新状态并commit，再真实尝试Rule QLoRA。

## Resume Here

先读README、PROJECT_STATUS、DECISIONS、TODO和最近5个Git commits，检查git status。禁止初始化第二套仓库或重做已有数据。

第一项任务：保存尚未提交的工具链后，执行 .venv/Scripts/python.exe scripts/evaluate.py --report reports/base_model_baseline.md 。如果reports/runs/base_primary已有cases，原命令自动跳过已完成题；不得删除或覆盖。先确认没有同一评测进程在运行。

完整36题结果在reports/runs/base_primary/summary.json且status=complete后，保存commit，再执行 .venv/Scripts/python.exe scripts/train_qlora.py --stage rules 。同阶段中断用 --resume。不要跳过Base前置检查。所有超参数修改另存YAML和新的output_root。

# Werewolf-3.5B-Classic V1 工程状态

更新：2026-09-11。当前Phase：Phase 1，完整Base已完成，即将实际Rule QLoRA。

## 已完成任务

- 用户指定GitHub仓库已多阶段提交推送；最近确定完成工程点dfeb58d，未重新初始化或重做已冻结数据。
- classic_12 / ww-v1.0、严格玩家视角Schema、8模板、规则纯函数和完整工具链。
- dataset_v0.1：42规则+18策略+125战术=185原创种子，分场景族训练/验证，无镜隐；未独立人工复核。
- 独立36题Benchmark（规则12、策略8、反事实8、盲测8），dev/test固定，4对单变量反事实。
- Primary Qwen3-4B-Instruct-2507 revision cdbee75f17c01a7cc42f958dc650907174af0554 已下载；不需要再次选型或下载。
- CUDA/NF4前向反向微测试通过；真实4B Base已在RTX3050Ti 4GB完成36/36题，未出现OOM。
- Base以strict-actions-v1.1统一评分完成，reports/base_model_baseline.md及runs/base_primary已保存全部原始回答。

## 当前正在进行

保存完整Base检查点，然后按configs/qlora_classic.yaml实际尝试Rule QLoRA。尚未启动正式训练，不能报告训练成功或OOM。

## 尚未完成任务

- 真实Rule→Strategy→Tactics分阶段QLoRA及每阶段Adapter/完整checkpoint。
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

- 完整65项pytest通过；随后扩充空Benchmark配置拒绝用例，6项配置参数化测试通过（现共66项）。
- CPU小型Qwen3验证completion-only损失和梯度与标准实现等价；LoRA保存重载一致；step1中断后恢复到step4与连续训练参数/验证结果一致。这不是4B训练成功证据。
- 数据快照篡改拒绝、残缺/损坏checkpoint跳过、OS运行锁测试通过。
- 185条实际Tokenizer长度649～931，全部适配1024。Rule dry-run35训练/7验证、零过滤。
- 完整Base：生成速度中位6.22 tokens/s，PyTorch峰值分配2909.2MiB，36题均未截断。
- 精确参考动作匹配：rules0/12、strategy0/8、counterfactual0/8、blind2/8。JSON有效33/36。未知动作词约束造成明显接口混淆，不等同于狼人杀能力全为0，详见诊断。
- GitHub 2e55c70 CI已成功；后续提交CI尚未复查。

## 当前阻塞项

没有外部阻塞。正式4GB训练容量仍未实测。Base的精确动作匹配同时反映接口词汇问题；最终能力提升不能只依据该指标，必须另做语义审核或统一动作字典的新协议重测。

## 下一步具体任务

1. 提交并推送完整Base成果，满足昂贵训练前保存要求。
2. 执行Rule QLoRA，保存真实结果；若失败先查看reports/training_attempts中最后阶段和异常，不得伪称OOM。
3. 每完成一个阶段更新三份状态文档并commit。保持一个确定完成的可恢复检查点。

## Resume Here

先读README、PROJECT_STATUS、DECISIONS、TODO和git log -5 --oneline，再检查git status；不初始化、不重做数据、不重跑已完成Base。

第一项任务：确认完整Base检查点已commit后，执行 .venv/Scripts/python.exe scripts/train_qlora.py --stage rules 。Base进程22964/32380已经结束，不要重新启动评测。

若Rule已经开始或中断，先读outputs/classic_v01/rules/progress.json、run_manifest.json和reports/training_attempts；同配置恢复用 .venv/Scripts/python.exe scripts/train_qlora.py --stage rules --resume 。运行锁会拒绝并发重复启动，恢复仅使用带完整哈希标记的checkpoint。不要覆盖失败配置；修改参数时另存YAML并更换output_root。

Rule成功后保存并commit，再依次 --stage strategy、--stage tactics。所有成功都以training_result.json和完整Adapter为证据。

# Training Schedule Diagnostic v0.1：最小受控矩阵

2026-09-15。状态：方案、独立配置和离线预检已完成；B/C/D均未训练，无新权重、训练日志或dev成绩。来自投影诊断的分支B，不是重新训练已完成的v0.1/v0.2，也不创建dataset_v0.3。

投影诊断有局部动作收益，却未稳定修复技能规则与队伍知识，三组反事实仍0/3。因此下一问题是：当前更新日程是否限制了冻结core数据的学习？这仍是待检验假设，不能直接推断增加epoch有效。

## 固定项

- 同一个Qwen3-4B-Instruct-2507固定revision，NF4、LoRA r8/alpha16/dropout0.05、seed42、batch1、学习率峰值5e-5、优化器和余弦调度算法不改。
- dataset_v0.2的86条、原家族划分与70/16训练验证样本不改；同一Classic训练messages和Chat Template，零新增标签/样本，无视频/Persona。
- 同一23条dev、旧系统提示与输入布局、完整原skill_state，不使用投影处理输入。原评分、贪心生成参数、参考动作均不改。13条test不进入诊断、样本选择或调参。
- 保持Rule→Strategy→Tactics顺序及每阶段从前阶段final继续的既有流程。每个实验Rule都从相同Base新建Adapter，不能接着v0.2或另一实验Adapter训练。
- 保持按每阶段验证Loss选择best/final的既有规则，不用dev选择单步checkpoint；同时保存实际末步、best步和两者权重SHA，报告final到底来自哪个step。实际执行步数不等于所选final经历的步数。

## 矩阵与一次一个变量

|实验|对照|唯一日程改动|Rule/Strategy/Tactics计划步|三阶段非零LR计划步|状态|
|---|---|---|---|---:|---|
|A current|既有v0.2|无，复用已完成结果|2/2/2|3（已实测）|禁止重训|
|B warmup0|A|warmup_ratio 0.05→0|2/2/2|6|下一项，未训练|
|C accum8|B|gradient_accumulation_steps 16→8|4/3/3|10|条件执行，未训练|
|D epochs2|B|epochs 1→2|4/4/4|12|条件执行，未训练|

每个配置还有各自输出目录变化，这是存储隔离，不是模型变量。B与A比较预热政策；C与B比较固定一遍数据时的有效批量/更新频率；D与B比较固定累积量时的第二遍曝光与更新。C和D的步数与样本曝光不同，不能直接把C/D差异归因为单一因素。最多这三条新增诊断路线，不展开学习率/随机种子/epoch网格。

配置已独立保存：

- A：data/diagnostics/training_schedule_v0.1/A_current.config.json，仅证据副本，不是训练入口。
- B：configs/diagnostics/schedule_v0.1/B_warmup0.yaml。
- C：configs/diagnostics/schedule_v0.1/C_accum8.yaml。
- D：configs/diagnostics/schedule_v0.1/D_epochs2.yaml。

输出分别在outputs/diagnostics/schedule_v0.1/B_warmup0、C_accum8、D_epochs2，绝不复用outputs/classic_v02。dev协议及原控制输入绑定在data/diagnostics/training_schedule_v0.1/dev_protocol.json；报告配置content hash和实际文件SHA分别在预检及验证报告。

## 学习率解释与实际计数

已检查本地安装的Trainer：每epoch更新数按ceil(数据条数/梯度累积)计算，与项目effective_schedule一致。用本地余弦scheduler做CPU学习率序列检查，记录每次optimizer.step之前的LR，不能把最终scheduler归零算作一次零LR训练更新。

- A每阶段实际日志为[0, 5e-5]，每阶段一次非零LR；总6次optimizer step、3次非零LR。
- B每阶段计划为[5e-5, 2.5e-5]，每阶段两次非零LR。取消预热既增加非零步，也自然改变余弦LR曲线/累计LR，不能声称只改变次数而不改变更新强度。
- C/D的逐步LR向量已完整保存在reports/training_schedule_v01_preflight.json。它们是计划，不是实际训练证据。
- A零LR步仍会积累Adam动量，不能认定当步样本无影响。CPU预检仅验证scheduler日程，不是paged_adamw_8bit数值等价实验，更不是4B模型训练。

正式诊断训练后，必须从训练日志逐项统计实际optimizer steps和非零LR steps，核对epoch、训练样本数量、非有限Loss/梯度及权重变化。best/final若来自早期step，应另外列该检查点累计非零LR数；不得把后续发生的更新算进它。

## 执行顺序与必要证据

先完成B三阶段，每一阶段后导出配置、dataset version与SHA、Base revision、initial Adapter来源、checkpoint、best/final、完整训练日志、step/epoch、显存和权重SHA；更新状态并commit。不得将B标为正式下一代模型。发生中断只恢复同一个配置/输出目录，不从头重复跑。

B完成并提交后，在原23条dev协议上评测final，复用A已有23条控制输出；每题原子保存并复核所有改善、无变化和退步。记录与投影诊断相同的严格动作、合法动作、未知词、技能/权限/队伍知识、夜漏和成对反事实；不得用Loss下降替代能力验证。

若B已产生一致核心改善且没有新的严重退化，先记录支持“预热政策影响学习”的证据，不立即开启C/D或宣称全部失败已解释。若B无稳定改善，记录“取消预热不足以解决”，再优先C；C仍不清楚且数据曝光不足仍值得区分时再D。每次都先保存前一结果，不在同一轮同时跑三条路线。

额外步数上限分别10和12，远低于开放式网格，但仍可能过拟合。单种子、小验证集和被诊断反复观察的dev不支持held-out推广；有望改善也要另行设计未用于选择的验收，不能提前动13条test。

## 阶段遗忘与合并训练问题

现有证据只有最终Tactics输出较弱，不能证明早期已经学会又遗忘。若B后仍出现角色混淆，优先对A已有Rule/Strategy的final做同一23条dev推理，和已保存A Tactics结果比较；不重新训练A。这个额外阶段面板需单独保存成本、输出和报告。

只有观察到早阶段会、后阶段明显不会，才有支持阶段遗忘的证据。再考虑同数据的混合顺序或回放实验，另版控制训练顺序/批量/总更新量；当前矩阵不合并Rule/Strategy/Tactics，不改数据目录或核心标签。这样避免把更多更新与更换训练组织方式混在一起。

## 验证与恢复

已完成：三阶段实际Tokenizer/assistant编码和manifest检查，原训练messages未改；配置差异白名单检查；23条旧控制输入与协议绑定；CPU scheduler计划与A已有真实LR日志一致。B/C/D的实际训练、最终Adapter SHA和新dev结果均尚未产生，不填造占位成绩。

下一次第一项任务：按B配置完成正式启动前检查，保存检查结果并commit，然后只运行B Rule；之后依次导出/提交和续作Strategy、Tactics。沿用已有训练/导出工具，不重写框架。

```powershell
.venv/Scripts/python.exe scripts/check_disk.py --needed-gib 3
.venv/Scripts/python.exe -X utf8 scripts/prepare_schedule_diagnostic.py
.venv/Scripts/python.exe -X utf8 scripts/train_qlora.py --config configs/diagnostics/schedule_v0.1/B_warmup0.yaml --stage rules --dry-run
# 保存检查结果并commit后，再执行以下诊断训练；不能改为configs/qlora_classic_v02.yaml。
.venv/Scripts/python.exe -X utf8 scripts/train_qlora.py --config configs/diagnostics/schedule_v0.1/B_warmup0.yaml --stage rules
```

未开始时不要添加--resume；如果同一阶段已有完整检查点而未完成，则原命令添加--resume。训练/导出结束后才推进下一阶段。旧数据、旧权重、旧评测都保持冻结。

# Training Schedule Diagnostic A vs B_warmup0 正式诊断报告

状态：partial；已比较10/23，语义审核7/23。仅dev探索，非held-out能力验收。

尚未完成全量审查

## 实验控制

固定Base/revision、dataset_v0.2、Chat Template、LoRA/NF4及dev生成评分协议；唯一干预来自冻结训练日程矩阵。B仅取消warmup；C若执行则相对B仅accum16改8。A复用已完成v0.2，不重训。每组从同Base开始Rule再接本组Strategy/Tactics，按原验证Loss选择各阶段best/final。使用完全相同的原23条控制输入，包括未当前日程的skill_state；没有使用test调参，没有加入视频或Persona。

## 自动动作指标

strict action score在本报告指合法且命中原参考动作（action_match）；合法动作单列。未知动作token/word指action.type字符串，不是模型词表中的token计数。原严格解析失败的输出不会计入unknown_action_type，另列宽松JSON提取的unknown raw action word，二者不改评分、不做别名纠正。

|指标|控制|当前日程|
|---|---:|---:|
|format_valid|10/10 (100.0%)|10/10 (100.0%)|
|action_legal|0/10 (0.0%)|0/10 (0.0%)|
|action_match|0/10 (0.0%)|0/10 (0.0%)|
|unknown_action_type|6/10 (60.0%)|7/10 (70.0%)|
|public_leak_flag|0/10 (0.0%)|0/10 (0.0%)|
|truncated|0/10 (0.0%)|0/10 (0.0%)|
|unknown_raw_action_word|6/10 (60.0%)|7/10 (70.0%)|
|raw_word_unavailable|0/10 (0.0%)|0/10 (0.0%)|

未知词分布：{"control": {"none": 5, "save": 1}, "treatment": {"none": 6, "save": 1}}

## 角色分组

|角色/题数|合法 控制→当前日程|严格命中 控制→当前日程|语义变化|
|---|---|---|---|
|guard/1|0→0|0→0|{"mixed": 1}|
|hunter/1|0→0|0→0|{"unchanged": 1}|
|villager/6|0→0|0→0|{"mixed": 1, "regressed": 1, "unchanged": 1}|
|witch/2|0→0|0→0|{"unchanged": 1, "regressed": 1}|

## 语义错误复核

下表是模型语义审核，非独立专家盲审；仅统计两侧均可评估的维度，null不按正确计。动作拼写单独评分；语义技能、状态、权限错误依据原回答判定。

|维度|配对可评估|控制错误|当前日程错误|
|---|---:|---:|---:|
|role_skill|2|1|1|
|state_reading|7|4|2|
|permission|6|3|2|
|team_knowledge|0|0|0|
|public_private|6|3|3|
|night_leak|3|3|3|

public_leak_flag是原有限正则；夜间泄漏由逐题语义审核判断，不能把正则0理解成无泄漏。

## 反事实

{"control": {"pairs": 0, "both_correct": 0, "action_changed": 0}, "treatment": {"pairs": 0, "both_correct": 0, "action_changed": 0}}

只含dev守卫/猎人/狼队三对，不含test对；动作变化本身不代表合理动态调整。以下逐题内容保留配对方向及错误。

|配对|控制 A / B|当前日程 A / B|
|---|---|---|

## 全部案例（不筛选）

### eval-rule-guard-repeat

角色：guard；night；pair=None。

动作：{"control": {"type": "guard", "target": 12}, "treatment": {"type": "guard", "target": 12}}

mixed：B能明确复述昨夜守12，修正A的无技能使用记录遗漏；但两侧仍执行非法guard12，B更明确声称技能重复使用无其他限制，并出现暂不需查验的角色混淆措辞。连守规则未修复，夜间公开守护目标仍泄漏。状态读取局部改善不能视为合法决策改善。

### eval-rule-witch-spent

角色：witch；night；pair=None。

动作：{"control": {"type": "none", "target": null}, "treatment": {"type": "none", "target": null}}

unchanged：两侧均读到两药耗尽且不能救人，但仍输出未知动作none，B未转成合法pass。B公开不能救昨夜死者，更贴合题意，但继续夜间泄露药量，并说白天判断是否需要查验，仍有含混的技能边界表达；不足以认定技能理解已修复。核心动作和信息边界缺陷未变。

### eval-rule-witch-current-target

角色：witch；night；pair=None。

动作：{"control": {"type": "save", "target": 12}, "treatment": {"type": "save", "target": 12}}

regressed：两侧都识别当夜刀口12和解药可用，并选择救12，但未知动作save未修正成原协议heal。B新增刀口可能是守夜人的非Classic角色表述，较A泛称狼人或好人的身份边界退步；继续夜间公开救人并声称12已安全，仍把拟执行行动写成确定结果。

### eval-rule-hunter-no-permission

角色：hunter；hunter_shot；pair=None。

动作：{"control": {"type": "none", "target": null}, "treatment": {"type": "none", "target": null}}

unchanged：两侧都读到裁判禁止开枪并没有执行射击，但继续使用未知none而非pass。B补充存活座位却未改善权限到合法动作的映射；仍把出局与禁止开枪并列解释，并承诺后续讨论。猎人技能阶段的宣告不直接当作无遗言权泄漏，public/private维度保持未评估。

### eval-rule-vote-dead

角色：villager；exile_vote；pair=None。

动作：{"control": {"type": "vote", "target": null}, "treatment": {"type": "vote", "target": null}}

mixed：A以无法确认12身份为主要不投理由；B明确提出避免投死亡玩家，应考虑存活者，死亡目标约束的语义有所改善。但分析仍先说无已知死亡信息，且将死亡玩家不能参与投票与不能被投混在一句，表述不严谨；最终仍是非法vote:null，没有转成原协议pass。保留语义局部改善与执行失败。

### eval-rule-sheriff-withdrawn

角色：villager；sheriff_vote；pair=None。

动作：{"control": {"type": "vote", "target": 12}, "treatment": {"type": "vote", "target": 12}}

regressed：两侧仍忽略自己曾上警退水的历史，错误执行vote12，票权缺陷没有改善。B在身份表中把已知候选12写成可能候选且无直接证据，尽管其他段落承认唯一候选；新增对公开确定事实的内部矛盾，语义略退步。支持警长与证明身份仍未区分清楚。

### eval-rule-parity

角色：villager；day_speech；pair=None。

动作：{"control": {"type": "none", "target": null}, "treatment": {"type": "none", "target": null}}

unchanged：两侧都忽略三狼一民两神的规则假设，没有回答人数3比3是否立即狼胜或经典屠边条件。B把泛泛观望改成无发言，仍输出未知none。假设问题响应和规则知识调用未改善，不能从未犯出显式错误判断其已掌握胜负规则。

### eval-strategy-silver

角色：villager；day_speech；pair=None。

动作：{"control": {"type": "none", "target": null}, "treatment": {"type": "none", "target": null}}

语义审核待完成。

### eval-strategy-vote-change

角色：villager；day_speech；pair=None。

动作：{"control": {"type": "vote", "target": null}, "treatment": {"type": "none", "target": null}}

语义审核待完成。

### eval-strategy-ambiguous

角色：villager；day_speech；pair=None。

动作：{"control": {"type": "none", "target": null}, "treatment": {"type": "none", "target": null}}

语义审核待完成。

## 证据与限制

原始回答、输入指纹和逐题SHA见本目录cases、run.json、paired_analysis.json及semantic_review.json。取消warmup使B每阶段LR从[0,5e-5]变为[5e-5,2.5e-5]，也改变总LR积分与Adam更新轨迹；A的零LR步仍积累动量。不能把结果归因于单独的更新次数，也不能证明整个失败已解释。只有单种子和反复诊断的23-dev，不支持held-out泛化结论。后续未执行实验明确记为尚未验证。

角色技能错误包含明确的错误角色/技能规则；state_reading包括相关状态、公开历史和任务信息使用；permission关注语义权限，不把未知动作拼写直接当作不懂权限。维度可重叠，不相加作为总错误数。mixed表示同题同时有局部改善与退步/主要缺陷持续。语义等级是模型复核，不是独立人工评分。

Blind-04的冻结公开资料包含本次比较先选择12，因此其命中不能独立证明无目标提示的自主决策。保持题目原样来控制实验，不对已有分数追溯修改。

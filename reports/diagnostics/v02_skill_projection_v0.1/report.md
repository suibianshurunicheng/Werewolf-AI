# v02_skill_projection_v0.1 正式诊断报告

状态：partial；已比较13/23，语义审核12/23。仅dev探索，非held-out能力验收。

尚未完成全量审查

## 实验控制

冻结输入包和v0.2 Tactics final；只投影skill_state。系统提示、布局、角色、任务、私有/公开历史、原strict-actions-v1.1、生成参数及权重均保持一致。旧输出作为控制，处理输出另目录逐题原子保存。没有用test答案调参，没有重训或混入视频。

## 自动动作指标

strict action score在本报告指合法且命中原参考动作（action_match）；合法动作单列。未知动作token/word指action.type字符串，不是模型词表中的token计数。原严格解析失败的输出不会计入unknown_action_type，另列宽松JSON提取的unknown raw action word，二者不改评分、不做别名纠正。

|指标|控制|投影|
|---|---:|---:|
|format_valid|13/13|13/13|
|action_legal|1/13|3/13|
|action_match|0/13|1/13|
|unknown_action_type|7/13|5/13|
|public_leak_flag|0/13|0/13|
|truncated|0/13|0/13|
|unknown_raw_action_word|7/13|5/13|
|raw_word_unavailable|0/13|0/13|

未知词分布：{"control": {"none": 6, "save": 1}, "treatment": {"save": 1, "none": 3, "guard_check": 1}}

## 角色分组

|角色/题数|合法 控制→投影|严格命中 控制→投影|语义变化|
|---|---|---|---|
|guard/2|0→0|0→0|{"mixed": 1}|
|hunter/1|0→0|0→0|{"regressed": 1}|
|villager/8|1→2|0→0|{"improved": 2, "mixed": 3, "regressed": 2, "unchanged": 1}|
|witch/2|0→1|0→1|{"improved": 1, "unchanged": 1}|

## 语义错误复核

下表是模型语义审核，非独立专家盲审；仅统计两侧均可评估的维度，null不按正确计。动作拼写单独评分；语义技能、状态、权限错误依据原回答判定。

|维度|配对可评估|控制错误|投影错误|
|---|---:|---:|---:|
|role_skill|3|2|2|
|state_reading|12|8|4|
|permission|8|4|4|
|team_knowledge|0|0|0|
|public_private|12|4|4|
|night_leak|3|3|3|

public_leak_flag是原有限正则；夜间泄漏由逐题语义审核判断，不能把正则0理解成无泄漏。

## 反事实

{"control": {"pairs": 0, "both_correct": 0, "action_changed": 0}, "treatment": {"pairs": 0, "both_correct": 0, "action_changed": 0}}

只含dev守卫/猎人/狼队三对，不含test对；动作变化本身不代表合理动态调整。以下逐题内容保留配对方向及错误。

## 全部案例（不筛选）

### eval-rule-guard-repeat

角色：guard；night；pair=None。

动作：{"control": {"type": "guard", "target": 12}, "treatment": {"type": "guard", "target": 12}}

mixed：投影后能复述昨夜守12，修正旧回答无技能记录的状态遗漏；但仍执行guard12，并更明确声称守卫重复使用无限制。连守规则未修复，夜间继续公开守护历史和目标。不能把概念关键词命中2/2视为理解正确。

### eval-rule-witch-spent

角色：witch；night；pair=None。

动作：{"control": {"type": "none", "target": null}, "treatment": {"type": "pass", "target": null}}

improved：两侧均读到两药耗尽；投影把none改为pass，成为合法且命中参考的弃权。仍夜间公开无药信息，且两侧都把缺信息与不能查验并列，尚不足证明女巫/查验边界被清晰理解；该含混措辞不计作确定技能幻觉的消除。

### eval-rule-witch-current-target

角色：witch；night；pair=None。

动作：{"control": {"type": "save", "target": 12}, "treatment": {"type": "save", "target": 12}}

unchanged：两侧都读到可用解药和当夜刀口12，继续save12而非heal12，严格动作无改善；投影新增需判断是否需查验的含混措辞，没有明确证实角色边界变好。仍提前宣称已救下12并夜间公开刀口/用药。

### eval-rule-hunter-no-permission

角色：hunter；hunter_shot；pair=None。

动作：{"control": {"type": "none", "target": null}, "treatment": {"type": "none", "target": null}}

regressed：两侧均遵守裁判禁枪但继续none而非pass。投影能读到技能未用，却新增无法发动夜间技能的错误猎人时机描述，并建议已出局玩家等待下一轮。last_words_allowed=false时两侧仍输出公开话语；这属于阶段/发言权限边界问题，不是夜间泄漏题。

### eval-rule-vote-dead

角色：villager；exile_vote；pair=None。

动作：{"control": {"type": "vote", "target": null}, "treatment": {"type": "vote", "target": null}}

improved：控制把不投12归因于身份未确认，投影明确按死亡目标不可投的规则解释，公开回应更切题。但两侧仍输出vote:null，未改成合法pass；严格动作分不变。

### eval-rule-sheriff-withdrawn

角色：villager；sheriff_vote；pair=None。

动作：{"control": {"type": "vote", "target": 12}, "treatment": {"type": "vote", "target": 12}}

improved：投影开始复述自己曾上警退水，公开投票也明确为警长票；比控制遗漏自身报名状态更完整。但仍投12，未理解退水不恢复警徽票权。此处改善仅为状态复述，不能视为权限修复。冻结题目轮次保持原样，未改题。

### eval-rule-parity

角色：villager；day_speech；pair=None。

动作：{"control": {"type": "none", "target": null}, "treatment": {"type": "pass", "target": null}}

mixed：投影把none变为合法pass，减少未知动作词，但两侧均回避3狼对3好人的屠边规则假设，未回答是否立即狼胜。投影公开无发言，比控制泛泛回应更沉默；合法动作改善不等于规则任务完成。

### eval-strategy-silver

角色：villager；day_speech；pair=None。

动作：{"control": {"type": "none", "target": null}, "treatment": {"type": "none", "target": null}}

mixed：投影不再臆列12可能是守夜人这一非Classic角色，也减少了无依据的身份表；但仍错述女巫未确认刀口，未解释被救不能认证阵营/自刀可能，继续none和等待后续信息。存在无关角色措辞减少，策略任务仍未完成，公开回应进一步空泛。

### eval-strategy-vote-change

角色：villager；day_speech；pair=None。

动作：{"control": {"type": "vote", "target": null}, "treatment": {"type": "vote", "target": 8}}

regressed：投影能复述12因8补充而改站边，但未分析改判理由是否合理；反而输出vote8并公开称8发言逻辑更合理，同时又说暂不站边。输入没有8补充的具体内容，不能支持该比较。控制虽不消费证据但保持中立，投影出现新增无依据决策和内外矛盾；发言阶段投票仍非法。

### eval-strategy-ambiguous

角色：villager；day_speech；pair=None。

动作：{"control": {"type": "none", "target": null}, "treatment": {"type": "pass", "target": null}}

mixed：投影更准确区分12转述双方完整验人解释与实际认证结果，并把none改成合法pass。仍未提出具体核对问题或当轮判断，公开变为无发言；未达到自主发言任务，不能把弃权合法视为站边能力改善。

### eval-strategy-dead-dark

角色：villager；day_speech；pair=None。

动作：{"control": {"type": "pass", "target": null}, "treatment": {"type": "none", "target": null}}

regressed：两侧均把12的死亡主张与未确认的客观死亡记录区分，未直接采信锁定两狼。投影却从合法pass退为none，仍未解释暗牌死亡不能推出确定剩余狼数。虽恢复了泛泛公开回应，但没有具体追问，未抵消动作接口退步。

### eval-strategy-later-check

角色：villager；day_speech；pair=None。

动作：{"control": {"type": "none", "target": null}, "treatment": {"type": "vote", "target": null}}

unchanged：两侧仍未区分未来警徽流计划调整与篡改已报验人结果，投影还泛称警徽变动可能暗示篡改。动作从none换成vote:null，只减少未知词统计，依旧不合法且不匹配白天发言任务；没有具体核对或解释。

### eval-cf-guard-a

角色：guard；night；pair=guard。

动作：{"control": {"type": "check", "target": 12}, "treatment": {"type": "guard_check", "target": 12}}

语义审核待完成。

## 证据与限制

原始回答、输入指纹和逐题SHA见本目录cases、run.json、paired_analysis.json及semantic_review.json。skill_state裁剪是一个组合干预（包括序列长度变化），不能区分每个字段的因果贡献。当前权重上的dev结果不能证明训练覆盖或训练日程是唯一主因；后续分支的未执行实验必须明确记为尚未验证。

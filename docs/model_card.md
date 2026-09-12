# Werewolf-3.5B-Classic V1 模型卡

状态：4GB本机已完成Rule（3step）、Strategy（1step）、Tactics（7step）三阶段Adapter，各1epoch；同协议36题Adapter比较完成：严格结构有效33/36→27/36、合法动作5/36→1/36、参考匹配2/36→0/36，未通过能力验收。开发集语义复核仍发现角色技能/证据利用错误，不能宣称高手模型。Tactics最终权重从最佳checkpoint-7核验导出，验证Loss2.8225455，训练峰值显存未在中断前落盘。禁止把Base或CPU小模型单元测试当成专项模型成果。实时状态和实际分数以PROJECT_STATUS、reports为准。

目标：3B～4B中文玩家视角决策，经典12人4狼4民预女守猎，ww-v1.0暗牌警长屠边。人工复制粘贴使用。镜隐不在Phase 1训练范围。

Primary Qwen/Qwen3-4B-Instruct-2507，Apache-2.0；revision固定在reports/models。Backup Qwen2.5-3B-Instruct使用Qwen Research条款，限非商业研究，不能套用Primary的Apache许可。

数据dataset_v0.1为185条原创合成种子，CC-BY-4.0，未独立人工复核或多Critic复核，无真人对局来源。Gold指作者筛选类别，不代表外部专家认证。训练与验证按场景族隔离，独立Benchmark36题，dev/test冻结；无镜隐数据。

训练预设为Rule→Strategy→Tactics SFT，无RL；r8 NF4 QLoRA，详细超参数见configs。本机RTX3050Ti 4GB已实际完成三阶段，不能保证其他长度/配置显存相同。最优checkpoint按验证Loss选择，不代表最强狼人杀策略。

限制：小样本、静态动作指标偏窄、中文公开发言语义泄漏不能由正则完全判定、房规并非所有平台通用、无真实胜率或“明显优于Base”的先验结论。最终需相同评测、人工盲审、真实复制粘贴对局。模型生成在游戏虚构角色内使用。

代码MIT；数据和基础权重许可分别适用，Adapter和合并权重发布时必须包含所用上游通知、数据版本、配置、评测和限制。

# 数据目录

dataset_v0.1 已生成185条原创合成种子：规则42、策略18、战术125。25种战术各包含正确使用、错误使用、被识破、对方反制、调整策略。

gold 表示作者优先筛选的种子，不代表独立人工复核。quality_score=4 是作者自评，human_approved=false，未进行外部 Critic。它不是3000～10000条正式高质量对局数据。

prepared 保留结构化记录与 messages；同一 scenario_id 家族整体分入训练或验证。versions 保存文件哈希。只有v0.1已生成，v0.2和v0.3尚未执行。examples仅演示，不再重复加入Gold。

运行 python scripts/prepare_dataset.py 会创建或验证快照；一致内容不重写，异内容拒绝覆盖。修改须有新的版本与变更理由。Phase 1仅接受classic_12。

原创合成样本采用CC-BY-4.0，署名Werewolf-Classic contributors。网页只用于规则核对，不复制攻略或字幕。上游模型许可证另计。

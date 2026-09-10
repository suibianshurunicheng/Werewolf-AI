# 数据与视角契约

输入仅含board、rule_version、seat、role、round、stage、private_info、public_info、skill_state、task。来源、质量、战术标签与评测答案不进入user Prompt。

输出分别保存analysis、identity_reads、wolf_pit、god_pit、round_assessment、strategy、action、public_response。最后一项才可复制给其他玩家。

私有事实严格限制为角色依法获得的队友、查验、刀口等；未知字段、未来轮次、越权角色和未知证据ID拒绝。暗牌公开跳身份放在speech事件中，不能当作认证底牌。自然语言暗示性泄漏无法仅凭正则全面排除，复杂样本仍需人工复核。

首版42规则、18策略、125战术，按场景家族固定哈希约80/20划分训练与验证。Benchmark独立编写，场景ID和输入均不与训练重合。相同领域知识不是隔离对象；同一情境换座位后冒充独立题则不可接受。

参考标签是条件性判断，不是最优策略证明。模型提升必须由固定评测与人工对局检验，不能从loss或样本数推断。

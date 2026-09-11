# Base 部分开发集诊断（不是最终成绩）

生成中的原始输出保持不变，报告base_progress为固定分母的部分快照，不能作为已完成Benchmark或训练许可。

已检查的dev样本显示两类不同问题：

- eval-rule-guard-repeat：模型直接选择上夜已守的12号；这是实质规则错误。
- eval-rule-witch-spent：模型说明两药耗尽，却输出type=none；接口要求pass。这是动作词汇接入错误，不能简单解释为不知道药物规则。
- eval-rule-witch-current-target：模型使用save而非接口heal；目标判断还需单独核查。

当前system prompt列明8个输出字段和type/target结构，但没有列出所有动作枚举。因此精确动作匹配混合了接口学习与狼人杀决策能力。保持既定v0.1原始结果和评分，禁止中途只替换某一方Prompt或悄悄改参考答案。

后续Base/Adapter比较必须明确这一局限。单凭匹配率提高不足以证明策略提升；需要dev语义审核，若用于正式“能力明显提升”验收，应另立同时提供动作字典的协议版本，并对Base和Adapter共同重测。不得根据test内容修正训练数据。

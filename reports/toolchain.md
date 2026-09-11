# 工具链验证记录

日期2026-09-11；实际60项pytest通过，退出0。测试包含配置拒绝、标签遮罩、不可静默截断、评测指纹、逐题恢复、固定分母、loss及梯度等价、LoRA更新保存重载。

真实Tokenizer检查见token_lengths.json，所有185样本适配1024。Rule dry-run35训练/7验证，零过滤。NF4微测试实际通过，环境版本见environment.json。4B完整训练与Benchmark尚未完成；不把CPU随机模型测试记作专项能力。

新增中断精确恢复及OS运行锁测试后，完整62项pytest通过，退出0。GitHub CI定义已创建，远端结果尚未确认。

# 工程决策

## 远程仓库与下载恢复

- 用户指定 git@github.com:suibianshurunicheng/Werewolf-AI.git。插件确认空仓库，SSH ls-remote 成功，保留现有本地提交并正常 push，禁止 force push。
- CUDA wheel 第一次下载截断且哈希不符，禁止跳过校验或报告安装成功；升级 pip 25.3 后使用 resume-retries。
- 已保存 r8/1024 的 4GB 起始配置与 12/16/24GB、3B 备用配置；它们尚未通过模型训练实测，不能当成显存保证。

## Schema 与基础测试检查点

- 严格 JSON Schema：禁止未知字段；私有事实按角色授权，事件有证据 ID 与轮次，不接受任意全局身份表。
- 输出独立保存 analysis、identity_reads、wolf_pit、god_pit、round_assessment、strategy、action、public_response。
- 模板生成脚本可重复运行但不覆盖已有异内容文件。当前 1 条 example 只用于演示/测试，不冒充 Gold 数据集。
- 37 项测试真实通过；纯文本语义泄漏仍需人工审核，正则无法证明不存在所有泄漏。

## 可恢复执行与当前底座

- 用户要求每个独立阶段更新三份状态文件并 commit，耗时工作前先保存。数据版本目录和哈希禁止隐式覆盖，评测逐条保存并核验运行指纹。
- Primary 固定 Qwen3-4B-Instruct-2507（成熟纯文本、非 thinking 输出）；Backup 为 Qwen2.5-3B-Instruct（较小、限非商业研究）。详见 docs/base_model_selection.md。
- CUDA 11.8 / PyTorch 2.6.0 用于现有 546.30 驱动，CPU 安装不算 GPU 训练环境。
- ww-v1.0 是经典项目房规；镜隐接口为 Phase 2 草案，不能进入 Phase 1。
- 初始 checkpoint 仅通过语法检查，不把尚未完成的 Schema 和测试说成可运行工具链。

## 2026-09-10：用户变更为 Werewolf-3.5B-Classic

- 以最新附件替代模型规模和阶段范围：3B～4B、classic_12 优先。
- 保留现有通用代码，包名改为 werewolf_sft；不重复建立目录。
- 镜隐迷踪降级 Phase 2，只保留规则调研与扩展接口，数据准备和训练入口禁止混入。
- 本机先尝试 r=8、batch=1、NF4、double quant、gradient checkpointing。不能根据显存估算代替真实尝试或伪称 OOM。

## 2026-09-10：范围与真实性

- 在当前工作目录直接建设一个标准 Python Repository，不创建第二套工程。
- 只实现两个固定板子的玩家视角决策、静态 Benchmark、人工复制粘贴推理；不实现自动竞技场或 Web UI。
- 数据、规则、实验按版本与哈希追踪；合成数据明确来源，不冒充真人对局或人工复核。
- 4GB GPU 不能承担正式 7B～9B QLoRA。尽可能运行 CPU 工程测试与小模型训练链路验证，后者不算专项模型训练结果。

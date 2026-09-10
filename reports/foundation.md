# 基础工程验证

日期：2026-09-10。实际执行：生成 Schema、8 份人工复制模板和 1 个明确标注的合成示例。

命令：`python -m pytest --junitxml=reports/foundation-tests.xml`。

结果：37 passed in 0.86s；退出码 0。此前 `python -m compileall -q src` 也通过。

验证范围：数据结构、视角权限、模板、转换、规则谓词和污染检查。没有加载真实基础模型，没有训练 Adapter，不代表模型规则正确率。

本地 XML 为运行原始证据，忽略提交以免含主机环境信息。独立复现可直接运行同一命令。

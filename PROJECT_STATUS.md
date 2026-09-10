# Werewolf-3.5B-Classic V1 工程状态

更新日期：2026-09-10。当前 Phase：**Phase 0，工程与数据基础**。

## 已完成任务（实际完成）

- 已按用户最新要求切换到 3B～4B / classic_12，镜隐为 Phase 2。
- 已初始化本地 Git，建立 README、DECISIONS、TODO、LICENSE。
- 已检测 RTX 3050 Ti Laptop，4096 MiB，驱动 546.30；Python 3.12.14。
- 已冻结经典规则 ww-v1.0，明确平台房规差异。
- 已选 Primary Qwen3-4B-Instruct-2507；Backup Qwen2.5-3B-Instruct，限非商业研究。
- 已编写规则纯函数、视角投影、字段转换、初版数据校验。

## 当前正在进行

- CUDA第二次安装成功：torch 2.6.0+cu118，cuda_available=True，实际识别RTX 3050 Ti。
- 数据阶段已完成；下一阶段为配置加载、可恢复训练/推理/评测。

## 尚未完成

- 训练/推理/评测脚本尚未完成。
- 模型下载、完整 Base Benchmark、真实 QLoRA、阶段 Adapter、比较报告、人工对局。
- 前三个检查点已推送GitHub suibianshurunicheng/Werewolf-AI，数据阶段正在保存。

## 已生成的重要文件

- README.md、PROJECT_STATUS.md、DECISIONS.md、TODO.md、LICENSE、.gitignore。
- pyproject.toml、requirements*.txt。
- src/werewolf_sft/{io,rules,perspective,validation}.py。
- docs/{base_model_selection,rules_classic,rules_mirror_maze,rule_conflicts}.md。
- data/schemas/sample.schema.json、data/examples/player_sample.json、8 份经典 prompts、tests/test_foundation.py。
- configs/qlora_classic.yaml、lora_classic.yaml、12/16/24GB 与 3B 备用配置；配置加载集成待完成。
- scripts/prepare_model.py已运行metadata-only，Primary revision为cdbee75f17c01a7cc42f958dc650907174af0554，权重未下载。
- data/gold/dataset_v0.1/：42规则+18策略+125战术；prepared保留分阶段原始结构和messages，versions有哈希清单。
- eval/：规则12、策略8、反事实8（4对）、盲测8；均标dev/test。
- scripts/prepare_dataset.py、convert_messages.py；src/werewolf_sft/seed_data.py、benchmark_data.py、dataset.py。
- scripts/generate_assets.py 与 scripts/validate_dataset.py；generate_assets 重跑只验证一致内容，拒绝覆盖修改。

## 已运行的测试与结果

- `.venv/Scripts/python.exe -m compileall -q src`：退出码 0，语法检查通过。
- `.venv/Scripts/python.exe scripts/generate_assets.py`：已实际生成 Schema、8 模板与 1 个明确标注的样本。
- `.venv/Scripts/python.exe -m pytest --junitxml=reports/foundation-tests.xml`：**37 passed in 0.86s**。覆盖 schema、越权事实、未来信息、消息分离、模板、技能、死亡、票权、屠边、去重、跨集合污染。
- 未进行模型 Benchmark，没有模型能力分数或正式训练成功证据。
- 数据生成成功；完整测试46 passed in 0.72s，证据见reports/dataset_v01.md。

## 当前阻塞项

- CUDA下载阻塞已解决，NF4库待安装和实测；4GB模型训练容量尚未验证，不能报告OOM。
- GitHub 认证阻塞已解除：用户给出空仓库，SSH 可用。

## 下一步具体任务

1. 保存数据阶段commit并push，185条是作者种子，不冒充3000条或独立人工复核。
2. 安装剩余依赖，下载固定Primary，完成可恢复脚本，先跑完整Base。
3. 每阶段同步更新三份状态文件并 commit，长任务前先保存。

## Resume Here

先读 README.md、PROJECT_STATUS.md、DECISIONS.md、TODO.md，再运行 `git log -5 --oneline`、`git status --short`，禁止重新初始化。

**第一项任务：完成配置加载及训练/推理/评测脚本，验证assistant-only标签与恢复机制，然后先跑Base。不要重复调研或生成已有数据。**

确认基础状态：`.venv/Scripts/python.exe -m pytest`（最近 37 项通过）。

环境检查：`.venv/Scripts/python.exe -c "import torch; print(torch.__version__, torch.cuda.is_available())"`。

若仍是 CPU torch，先检查已有安装进程，不要并发启动第二个 pip。确需恢复安装时执行：

`.venv/Scripts/python.exe -m pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cu118`

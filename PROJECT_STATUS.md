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

- CUDA 11.8 / torch 2.6.0 安装正在下载约 2.7GB wheel；此前仅有 CPU torch。
- 下一独立阶段：Schema、最小样本、经典 Prompt、基础测试。

## 尚未完成

- Gold、Benchmark、数据版本快照、训练/推理/评测脚本。
- 模型下载、完整 Base Benchmark、真实 QLoRA、阶段 Adapter、比较报告、人工对局。
- GitHub 远程创建与推送；插件已连接，本机 gh CLI 未登录。

## 已生成的重要文件

- README.md、PROJECT_STATUS.md、DECISIONS.md、TODO.md、LICENSE、.gitignore。
- pyproject.toml、requirements*.txt。
- src/werewolf_sft/{io,rules,perspective,validation}.py。
- docs/{base_model_selection,rules_classic,rules_mirror_maze,rule_conflicts}.md。

## 已运行的测试与结果

- `.venv/Scripts/python.exe -m compileall -q src`：退出码 0，语法检查通过。
- 尚未运行单元测试；Schema 尚未生成，校验模块尚不能端到端运行。
- 未进行模型 Benchmark，没有模型能力分数或正式训练成功证据。

## 当前阻塞项

- CUDA 依赖下载正在进行；4GB 容量待真实验证，未发生可报告的 OOM。
- gh CLI 未登录，插件未发现新建仓库工具；先完成本地工程。

## 下一步具体任务

1. 完成 Schema、测试夹具、Prompt；运行规则和视角测试。
2. commit 后再生成 Gold 与四类评测。
3. 每阶段同步更新三份状态文件并 commit，长任务前先保存。

## Resume Here

先读 README.md、PROJECT_STATUS.md、DECISIONS.md、TODO.md，再运行 `git log -5 --oneline`、`git status --short`，禁止重新初始化。

**第一项任务：补齐 data/schemas/sample.schema.json 和 tests/，验证已有 src/werewolf_sft/。**

环境检查：`.venv/Scripts/python.exe -c "import torch; print(torch.__version__, torch.cuda.is_available())"`。

若仍是 CPU torch，先检查已有安装进程，不要并发启动第二个 pip。确需恢复安装时执行：

`.venv/Scripts/python.exe -m pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cu118`

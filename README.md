# Werewolf-3.5B-Classic V1

用 3B～4B 通用中文模型，通过分阶段 QLoRA 学习经典 12 人预女守猎。用户人工输入合法私有信息和公开记录，仅复制模型的正式公开发言回对局。

当前处于 Phase 0 工程建设；没有训练完成的专项 Adapter，也没有模型能力结果。最新事实以 [PROJECT_STATUS.md](PROJECT_STATUS.md) 为准。

## 恢复项目

每次继续工作先读取本文件、[PROJECT_STATUS.md](PROJECT_STATUS.md)、[DECISIONS.md](DECISIONS.md)、[TODO.md](TODO.md) 和最近 Git commits。按状态文件末尾的 `Resume Here` 继续，禁止重新初始化或无依据重复调研与生成数据。

## 已有工程

- `src/werewolf_sft/rules.py`：动作合法性、夜间效果、屠边、警长票权等纯函数。
- `src/werewolf_sft/perspective.py`：玩家信息白名单、教师视角投影、私有与公开分离。
- `src/werewolf_sft/validation.py`：数据、技能、事实授权与跨集合污染检查。
- `requirements-dev.txt`：轻量数据/测试依赖；`requirements.txt`：训练依赖。

这些模块仍在集成。完整命令与验证结果将在各阶段完成时更新，不能将当前状态理解为训练就绪。

Phase 1 仅支持 `classic_12`；镜隐迷踪仅保留 Phase 2 规则调研和接口。不开自动竞技场、不做 RL、不做 Web 前端。

## 许可证

项目原创代码使用 MIT；基础模型、数据、Adapter 和合并模型另按 [模型选择](docs/base_model_selection.md) 中的上游条款处理。

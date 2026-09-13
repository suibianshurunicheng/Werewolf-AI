# 数据版本职责（2026-09-13固定）

- dataset_v0.2 / v0.2-core：只修复v0.1的dev诊断所证实的规则、证据利用、战术、合法动作和自主决策缺陷。只允许本项目原创修正组件，显式路径和哈希准入；禁止扫描整个candidates目录自动合并。
- video_distilled_v0.1：独立视频候选池，保存于data/candidates/video_distilled_v0.1/。不进入v0.2，不能把ASR、字幕或玩家原话直接变成SFT。
- dataset_v0.3：只有v0.2完成正式训练及同协议Benchmark，且没有继续明显退化后才考虑。组成可为v0.2加通过审核的视频数据，必须比较v0.1、v0.2、v0.3-video。

视频流程：原始局面→当时合法玩家视角→策略质量审核→机制剥离→核心博弈思想→必要时经典合法改写→Critic复核→候选。每一步保留证据、状态与未解决问题，不用未来身份或最终胜负倒推当时判断。非经典板子仍按CLASSIC_GOLD/TRANSFERABLE/BOARD_SPECIFIC/LOW_QUALITY分类，TRANSFERABLE必须记录机制剥离。

v0.2仅变更训练数据与其Classic专用消息，Base/revision、QLoRA配置原则和旧Benchmark输入/生成/评分协议不变。训练从同一Base开始，不从v0.1 Adapter续训，避免混淆两种实验。新输出使用outputs/classic_v02、reports/runs/qlora_v02；旧结果不覆盖。

比较预先记录：报告36题结构有效、合法动作、参考动作、反事实成对命中，以及dev语义缺陷。若相对v0.1任一前三项下降至少2题，或成对命中下降，或dev审核出现新的严重规则/私有信息泄漏回归，视为明显退化，v0.3视频合并门禁保持关闭。没有触发此门禁不等于能力验收通过，也不证明统计显著提升。单次小Benchmark只提供定向修正的有限证据。

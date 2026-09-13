# dataset_v0.2第一批规则修正

32条原创合成候选、16组成对条件、10个场景族；训练侧24条、验证侧8条。不是32场独立对局，也未经独立专家认可。组件rules_batch_v0.1已冻结，完整dataset_v0.2尚未冻结、未训练。

由既有dev诊断的错误类型构造，未引用视频逐字稿或test答案；旧dataset_v0.1与Benchmark仅做只读完整性/重复输入检查。没有重建旧数据或重新选择Base。

| 条件组 | A动作 | B动作 | 规则依据 |
|---|---|---|---|
| guard_repeat | pass / None | guard / 6 | 不得连续守同一人 |
| guard_empty_break | guard / 2 | pass / None | 空守打断连守；允许自守 |
| hunter_permission | pass / None | shoot / 9 | 裁判许可且枪未用才可开枪 |
| hunter_spent | shoot / 9 | pass / None | 猎枪全局一次 |
| hunter_late_round | shoot / 9 | shoot / 9 | 枪权不限定第一轮；不变性对照 |
| witch_poison_stock | pass / None | poison / 7 | 药量门禁与合法毒目标 |
| witch_current_target | heal / 5 | heal / 8 | 解药只救当夜刀口 |
| witch_self_round | heal / 2 | pass / None | 首夜可自救，后夜不可；通知时间同步 |
| witch_one_potion | poison / 7 | pass / None | 每夜至多一瓶药 |
| sheriff_registration | vote / 7 | pass / None | 退水不恢复警徽投票权 |
| vote_living_target | vote / 7 | pass / None | 放逐只能投其他存活目标 |
| role_skill | check / 11 | pass / None | 角色能力而非任务措辞决定权限 |
| public_boundary | check / 11 | speak / None | 夜间私有操作与白天公开报告分离 |
| victory_villagers | speak / None | speak / None | 屠边；规则假设不冒充真实身份 |
| victory_gods | speak / None | speak / None | 屠边；规则假设不冒充真实身份 |
| victory_no_wolves | speak / None | speak / None | 屠边；规则假设不冒充真实身份 |

## 校验与恢复

- 所有样本通过Schema、合法动作和视角自动验证；原19个冻结数据/评测文件SHA校验通过。
- 5项针对测试通过：成对标签、可见字段变化、枪权轮次不变性、同族隔离、夜间空公开发言、错误角色/过期刀口拒绝、假设胜负与裁判规则一致、幂等补缺和异内容拒绝。
- 本机真实重复执行复用全部5个组件文件，SHA与修改时间均未改变。完整pytest：76 passed，9条PEFT测试夹具警告，47.42秒。
- 验证侧场景族：v02-rules-guard_memory, v02-rules-role_boundary, v02-rules-witch_self_save。当前整组守卫记忆、自救轮次和角色边界在验证侧；正式训练前需审核完整v0.2的覆盖，不能把这一小批直接当作完整训练方案。

## 本阶段范围

仅保存样本、分组与哈希，没有生成messages或改变v0.1 Prompt。共用结构中仍有未激活的扩展技能字段；最终Classic消息需检查并裁剪非经典内容。旧Prompt及旧比较保持原样，新格式若改变须独立版本并对Base/Adapter共同测量。
后续继续策略/战术修正及完整v0.2审核、消息格式、Tokenizer长度与配置冻结；再提交并训练。CPU/数据测试不代表模型能力改善。

复核组件：.venv/Scripts/python.exe scripts/prepare_dataset.py --version dataset_v0.2。相同内容直接复用；改已有组件必须升组件版本，不覆盖。

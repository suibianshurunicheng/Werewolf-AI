# 人工复制粘贴对局

按prompts内当前角色/阶段模板填入自己依法知道的信息与公开发言。不得粘贴裁判全部底牌。历史发言中的身份声称只是声称，不是查验。每回合自行更新死亡、药物、警徽、投票等状态；此项目没有自动竞技场。

结构化示例：python scripts/inference.py --input-json data/examples/player_sample.json。示例是完整严格schema；输入验证会阻止角色越权、未来信息和非法技能字段。

自由文本：复制prompts/classic_day.md到本地文本并填写，再运行 python scripts/inference.py --prompt-file 文件路径。不得把占位符原样交给模型。自由文本无法自动证明视角合法，操作者需自己核对。

使用已训练模型时追加 --adapter outputs/classic_v01/tactics/final；没有成功Adapter时默认仅为Base，不称为专项模型。

脚本把JSON分为私有分析、身份判断、狼坑、神坑、轮次、策略、行动、正式公开发言。只复制【正式公开发言】，不要复制其余私有内容。--public-only仅显示正式公开发言。夜间public_response可以为空。

JSON不合法、输出截断、明显公开泄漏或结构化输入下动作非法时脚本会报错，原始结果留在outputs用于检查。合理怀疑不等于确定身份；输出不保证正确，尤其房规版本不同需要先确认。

人工验收尚未完成。未来真实复制粘贴测试应另记对局规则、轮次输入、Adapter哈希、输出、人工修正及输赢；单局输赢不能证明训练提升。

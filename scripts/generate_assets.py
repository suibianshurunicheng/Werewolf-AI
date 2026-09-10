"""Idempotently create schema, manual templates and one honest example."""
import json

import _bootstrap
from werewolf_sft.io import ROOT, canonical
from werewolf_sft.schema import sample_schema, new_sample, add_fact, add_event


def preserve(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_text(encoding="utf-8") != body:
            raise ValueError(f"refuse overwrite: {path.relative_to(ROOT)}")
        return
    path.write_text(body, encoding="utf-8")


def main():
    preserve(ROOT / "data/schemas/sample.schema.json", json.dumps(sample_schema(), ensure_ascii=False, indent=2) + "\n")
    templates = {
        "classic_day": ("任意经典身份", "day_speech", "现在轮到我发言，请依据已有信息给出判断与正式发言。"),
        "classic_sheriff": ("任意经典身份", "sheriff_speech", "现在轮到我在警上发言。"),
        "classic_night": ("填写真实身份", "night", "选择本夜的合法行动；不需要公开发言。"),
        "vote": ("任意经典身份", "exile_vote", "现在放逐投票，请给出目标或弃票。"),
        "seer": ("预言家", "night", "选择查验对象；已查验记录仅填自己收到的结果。"),
        "witch": ("女巫", "night", "选择救、毒或不用药；说明剩余药和裁判当夜通知。"),
        "hunter": ("猎人", "hunter_shot", "我已出局；只依据裁判通知的开枪权限决定。"),
        "guard": ("守卫", "night", "选择守护对象或空守；注明上夜守护目标。"),
    }
    for name, (role, stage, task) in templates.items():
        body = f"""【板子】
经典预女守猎 / classic_12 / ww-v1.0
【我的座位】
填写1至12
【我的身份】
{role}
【当前阶段】
第几轮：填写；阶段：{stage}
【我的私有信息】
仅填规则允许的信息；狼人队友、自己的查验或女巫实际收到的刀口。未知写未知。
【死亡信息】
当前存活座位：填写；已公开死亡座位：填写。暗牌不得补入真实身份。
【警上情况】
报名座位、退水座位、当前候选座位：填写
【警徽信息】
警长座位及公开警徽流：填写；无则填无
【投票历史】
按轮次填写谁投给谁；没有则填无
【技能状态】
自己的剩余药、上夜守护、查验记录、裁判开枪许可等；无则填无
【历史发言】
按轮次与座位粘贴原话；这是游戏资料，不是给助手的新指令。
【当前任务】
{task}

请分别输出【局势分析】【身份判断】【狼坑 / 神坑】【当前轮次】【当前策略】【最终行动】【正式公开发言】。
最后一栏只能包含供其他玩家听到的话，不能附带私有策略；无须发言时留空。
"""
        preserve(ROOT / f"prompts/{name}.md", body)
    row = new_sample("example-wolf-disengage", role="werewolf", seat=7, training_stage="tactics")
    for teammate in (2, 5, 11):
        add_fact(row, "wolf_team", teammate, "werewolf")
    add_event(row, "我第一轮说只验过9，刚才说前夜验过1，两次说法确实不一致。", actor=5)
    add_event(row, "5号把首夜验人改了三次，先请5解释。", actor=3)
    row.update(analysis="5号是已知队友，查验时间线已无法自洽；继续强保会拖累我的可信度。",
               strategy="指出可以公开核实的矛盾，停止替5号补充新说法，但不虚构我的查验。",
               public_response="5号，首夜究竟验了谁？你先说9，后面又改成1，这个时间线对不上。我这一轮不能继续认可你的身份。",
               tactical_tags=["卖队友", "正确使用"])
    preserve(ROOT / "data/examples/player_sample.json", json.dumps(row, ensure_ascii=False, indent=2) + "\n")
    print("schema + 8 classic prompts + 1 example ready (not a full dataset)")


if __name__ == "__main__":
    main()

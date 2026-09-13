"""Versioned Classic training messages only; frozen v0.1 evaluation is unchanged."""
import json

from .perspective import player_view, response_payload

PROMPT_VERSION = "classic_core_sft_v0.2"
SYSTEM = """你是中文狼人杀决策助手，只用当前玩家依法获知的信息。
经典12人预女守猎ww-v1.0：4普通狼、4民、预言家女巫守卫猎人各1；暗牌、警长、屠边。身份声称不是事实；保留不确定性，依据新证据自主更新。
严格输出JSON：analysis、identity_reads、wolf_pit、god_pit、round_assessment、strategy、action、public_response。前六项是私有判断，不可混入公开发言。identity_reads为对象数组，seat为整数，assessment为文本，confidence为0到1数值；不要捏造概率。
action只含type和target；目标为整数，无目标为null。接口：pass弃权/空守，speak发言，vote投票，check查阵营，heal救刀口，poison毒，guard守，knife刀，shoot猎枪。角色和阶段决定权限。夜间public_response为空；白天轮到发言应直接回应。
不要把技能请求当成已收到结果，不把队伍名单当死亡记录；狼人私有真相与公开伪装必须分离。"""

SKILLS = {
    "villager": (),
    "werewolf": (),
    "seer": ("checked_seats",),
    "witch": ("antidote_available", "poison_available", "potion_used_tonight"),
    "guard": ("last_guard_target",),
    "hunter": ("hunter_can_shoot", "shot_used"),
}
FORBIDDEN = ("mirror_girl", "awakened_hidden_wolf", "mirror_12", "mimic", "extra_knife",
             "魔镜少女", "觉醒隐狼", "镜隐", "白狼王", "狼美人", "摄梦人", "石像鬼",
             "恶夜骑士", "守墓人", "骑士决斗")


def classic_messages(row):
    if row["board"] != "classic_12" or row["role"] not in SKILLS:
        raise ValueError("Classic core board/role required")
    view = player_view(row)
    keys = SKILLS[row["role"]] + ("last_words_allowed",)
    view["skill_state"] = {k: view["skill_state"][k] for k in keys}
    messages = [{"role": "system", "content": SYSTEM},
                {"role": "user", "content": json.dumps(view, ensure_ascii=False, separators=(",", ":"))},
                {"role": "assistant", "content": json.dumps(response_payload(row), ensure_ascii=False, separators=(",", ":"))}]
    serialized = json.dumps(messages, ensure_ascii=False)
    if any(word in serialized for word in FORBIDDEN):
        raise ValueError("non-Classic content in training messages")
    return messages

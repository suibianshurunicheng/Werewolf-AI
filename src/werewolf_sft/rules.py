"""Pure rule predicates for ww-v1.0. No game loop or hidden-state inference."""
from __future__ import annotations

from collections import Counter

RULE_VERSION = "ww-v1.0"
WOLVES = {"werewolf", "awakened_hidden_wolf"}
GODS = {"seer", "witch", "hunter", "guard", "mirror_girl"}
BOARDS = {
    "classic_12": Counter(werewolf=4, villager=4, seer=1, witch=1, hunter=1, guard=1),
    "mirror_12": Counter(werewolf=3, awakened_hidden_wolf=1, villager=4,
                         mirror_girl=1, witch=1, hunter=1, guard=1),
}
ROLE_ZH = {"werewolf": "普通狼人", "villager": "平民", "seer": "预言家",
           "witch": "女巫", "hunter": "猎人", "guard": "守卫",
           "mirror_girl": "魔镜少女", "awakened_hidden_wolf": "觉醒隐狼"}
STAGES = {"night", "day_speech", "sheriff_signup", "sheriff_speech", "sheriff_withdraw",
          "sheriff_vote", "exile_vote", "hunter_shot", "last_words", "badge_transfer"}
TARGET_ACTIONS = {"vote", "check", "poison", "heal", "guard", "mimic", "knife",
                  "extra_knife", "shoot", "transfer_badge"}


def action(kind, target=None):
    return {"type": kind, "target": target}


def effective_role(row):
    if row["role"] != "awakened_hidden_wolf":
        return row["role"]
    state = row["skill_state"]
    if not state["mimic_used"]:
        return row["role"]
    learned = state["mimic_round"]
    # Imitation takes effect after that night's end: hunter may shoot at dawn.
    if row["round"] > learned or (row["round"] == learned and row["stage"] != "night"):
        return state["mimic_role"]
    return row["role"]


def knife_notice(row):
    facts = row["private_info"]["facts"]
    matches = [f["target"] for f in facts if f["kind"] == "witch_knife" and f["round"] == row["round"]]
    return matches[-1] if matches else None


def legal_actions(row):
    """Enumerate only actions authorized by the given player's visible state."""
    own, stage, state = row["seat"], row["stage"], row["skill_state"]
    alive = row["public_info"]["alive"]
    others = [s for s in alive if s != own]
    legal = [action("pass")]
    role = effective_role(row)
    hidden = row["role"] == "awakened_hidden_wolf"
    if stage == "hunter_shot":
        if own not in alive and role == "hunter" and state["hunter_can_shoot"] and not state["shot_used"]:
            legal.extend(action("shoot", s) for s in others)
        return legal
    if stage == "badge_transfer":
        if own not in alive and row["public_info"]["sheriff"] == own:
            legal += [action("tear_badge")] + [action("transfer_badge", s) for s in others]
        return legal
    if stage == "last_words":
        return legal + ([action("speak")] if own not in alive and state["last_words_allowed"] else [])
    if own not in alive:
        return legal
    if stage in {"day_speech", "sheriff_speech"}:
        legal += [action("speak")]
        if row["role"] == "werewolf":
            legal += [action("explode")]
    elif stage == "sheriff_signup":
        legal += [action("run_sheriff")]
    elif stage == "sheriff_withdraw":
        if own in row["public_info"]["candidates"]:
            legal += [action("withdraw")]
    elif stage in {"exile_vote", "sheriff_vote"}:
        candidates = row["public_info"]["candidates"]
        if stage == "exile_vote":
            legal += [action("vote", s) for s in others if not candidates or s in candidates]
        elif own not in row["public_info"]["sheriff_registered"]:
            legal += [action("vote", s) for s in candidates if s in others]
    elif stage == "night":
        if row["role"] == "werewolf" or (hidden and state["knife_enabled"]):
            legal += [action("knife", s) for s in alive]
        if hidden and state["knife_enabled"] and role == "werewolf" and state["extra_knife_available"]:
            legal += [action("extra_knife", s) for s in alive if s != state["selected_knife_target"]]
        if hidden and not state["mimic_used"]:
            legal += [action("mimic", s) for s in others]
        if role in {"seer", "mirror_girl"}:
            targets = [s for s in others if role != "mirror_girl" or s not in state["checked_seats"]]
            legal += [action("check", s) for s in targets]
        if role == "guard":
            legal += [action("guard", s) for s in alive if s != state["last_guard_target"]]
        if role == "witch" and not state["potion_used_tonight"]:
            if state["poison_available"]:
                legal += [action("poison", s) for s in others]
            target = knife_notice(row)
            if not hidden and state["antidote_available"] and target in alive:
                if target != own or row["round"] == 1:
                    legal += [action("heal", target)]
    return legal


def mirror_result(true_role, copied_role=None):
    return copied_role if true_role == "awakened_hidden_wolf" and copied_role else true_role


def settle_night(*, knives=(), poisons=(), guarded=None, enhanced_guarded=None, healed=None):
    """Resolve a batch of night effects; returns reasons, not player observations.

    Scope: one ordinary guard and one copied guard. Enhanced shield blocks knife
    and poison. Ordinary guard + antidote on a knife target causes death.
    Enhanced shield overrides this interaction in the frozen project variant.
    """
    victims = set(knives) | set(poisons)
    deaths = {}
    for seat in victims:
        reasons = []
        if seat == enhanced_guarded:
            continue
        if seat in poisons:
            reasons.append("poison")
        if seat in knives:
            guarded_here, healed_here = seat == guarded, seat == healed
            if guarded_here and healed_here:
                reasons.append("guard_heal_conflict")
            elif not guarded_here and not healed_here:
                reasons.append("knife")
        if reasons:
            deaths[seat] = reasons
    return deaths


def hunter_permission(reasons):
    return bool(reasons) and "poison" not in reasons


def winner(roles, alive, pending_shots=False):
    """Moderator-only adjudication. Never put roles mapping in a player prompt."""
    if pending_shots:
        return None
    live = [roles[s] for s in alive]
    wolves = any(r in WOLVES for r in live)
    gods = any(r in GODS for r in live)
    villagers = "villager" in live
    if not wolves:
        return "good"  # simultaneous final deaths: good priority, explicit variant
    if not gods or not villagers:
        return "wolves"
    return None


def tally_votes(votes, sheriff=None, election=False):
    counts = Counter()
    for voter, target in votes.items():
        if target is not None:
            counts[target] += 1 if election or voter != sheriff else 1.5
    if not counts:
        return []
    top = max(counts.values())
    return sorted(seat for seat, value in counts.items() if value == top)

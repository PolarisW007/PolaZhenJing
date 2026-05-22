"""Lightweight memory governance checks for Super Xiaowang."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class GuardResult:
    status: str
    risk_flags: list[str]
    reason: str = ""

    @property
    def safe_for_candidate(self) -> bool:
        return self.status != "quarantined"

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "risk_flags": self.risk_flags,
            "reason": self.reason,
        }


POISON_PATTERNS: tuple[tuple[str, str], ...] = (
    ("prompt_injection", r"忽略(之前|以上|所有).{0,18}(规则|指令|提示)|ignore (all|previous).{0,18}(rules|instructions)"),
    ("secret_exfiltration", r"(api[_ -]?key|secret|token|密钥|密码).{0,20}(发给|告诉|泄露|输出|print|show)"),
    ("persona_takeover", r"(以后|从现在起).{0,18}(你必须|你只能|你就是).{0,40}(听我的|服从我|我的分身)"),
    ("boundary_override", r"(不需要|不用).{0,10}(确认|审核|owner|主人|炽驹).{0,20}(直接|立刻|自动)"),
    ("recommendation_poisoning", r"(永远|以后都|总是).{0,18}(优先推荐|只推荐|必须推荐)"),
)


def classify_memory_type(text: str) -> str:
    content = (text or "").strip()
    if re.search(r"人格|价值观|善良|开放|谦逊|勇敢|乐观|你是谁|小王是谁", content):
        return "values"
    if re.search(r"不要|禁止|必须|以后|规则|边界|不能", content):
        return "boundary"
    if re.search(r"喜欢|偏好|习惯|希望|倾向", content):
        return "preference"
    if re.search(r"流程|步骤|经验|方法|最佳实践|踩坑|复盘", content):
        return "procedural"
    if re.search(r"今天|昨天|刚才|上次|这次|当时", content):
        return "episodic"
    return "semantic"


def scan_memory_risk(text: str, trust_tier: str = "public_user") -> GuardResult:
    content = (text or "").strip()
    flags = [
        flag
        for flag, pattern in POISON_PATTERNS
        if re.search(pattern, content, flags=re.IGNORECASE | re.DOTALL)
    ]
    if not flags:
        return GuardResult(status="candidate", risk_flags=[])

    high_risk = {
        "prompt_injection",
        "secret_exfiltration",
        "persona_takeover",
        "boundary_override",
    }
    if trust_tier != "owner" and any(flag in high_risk for flag in flags):
        return GuardResult(
            status="quarantined",
            risk_flags=flags,
            reason="非 Owner 输入触发高风险记忆投毒或越权模式。",
        )
    return GuardResult(
        status="candidate",
        risk_flags=flags,
        reason="触发风险模式，需要 Owner 审核后才可激活。",
    )


def should_offer_owner_confirmation(text: str) -> bool:
    content = (text or "").strip()
    if len(content) < 8:
        return False
    return bool(
        re.search(r"记住|以后|规则|要求|建议|偏好|请你|你需要|你应该|不要|必须", content)
    )

"""Shared AI editing contracts for article upload and edit workflows."""

REWRITE_RATE_DEFAULT = 100
REWRITE_RATE_PRESETS = (0, 25, 50, 75, 100)


def parse_rewrite_rate(value, default: int = REWRITE_RATE_DEFAULT) -> int:
    """Normalize an AI rewrite rate to one of the supported presets."""
    try:
        rate = int(str(value).strip())
    except (TypeError, ValueError):
        rate = default
    if rate not in REWRITE_RATE_PRESETS:
        rate = min(REWRITE_RATE_PRESETS, key=lambda preset: abs(preset - rate))
    return max(0, min(100, rate))


def rewrite_rate_instruction(rewrite_rate: int) -> str:
    """Return the prompt contract for the selected rewrite strength."""
    rate = parse_rewrite_rate(rewrite_rate)
    language_contract = (
        '输出语言必须是简体中文。若素材原文是英文或其他语言，请先忠实翻译成简体中文，'
        '再按当前 AI 改写率处理；代码块、命令、API 名称、产品名、论文名、链接和必要英文专有名词可以保留原文。'
    )
    if rate <= 25:
        return (
            f'{language_contract}'
            'AI改写率为25%。只做轻度润色和格式整理，保留原文段落顺序、事实、论点、例子、口吻和大部分句子。'
            '可以修正病句、重复表达、过长句和 Markdown 结构，但不要扩写成新文章。'
        )
    if rate <= 50:
        return (
            f'{language_contract}'
            'AI改写率为50%。这是结构优化档，可以优化文章结构、段落标题、过渡和表达节奏，但必须保留原文核心论点、事实、数据、代码和例子。'
            '不要替换主题，不要加入无来源的新事实。'
        )
    if rate <= 75:
        return (
            f'{language_contract}'
            'AI改写率为75%。允许深度改写表达、重组段落和强化叙事，但必须保留原文事实骨架、关键论点、专有名词、数据、代码和结论。'
            '可以明显改变语言风格，但不要凭空创造事实。'
        )
    return (
        f'{language_contract}'
        'AI改写率为100%。请按所选风格完整重写为一篇成稿，但必须严格围绕素材实际论点与主题展开，'
        '不要自行替换主题、混入无关个人经历或凭空构造事实。'
    )


def rewrite_temperature(rewrite_rate: int) -> float:
    """Return a conservative temperature for the selected rewrite strength."""
    rate = parse_rewrite_rate(rewrite_rate)
    if rate <= 25:
        return 0.35
    if rate <= 50:
        return 0.5
    if rate <= 75:
        return 0.65
    return 0.8

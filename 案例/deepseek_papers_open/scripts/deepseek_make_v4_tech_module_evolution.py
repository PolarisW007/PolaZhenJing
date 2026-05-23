from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT
OUT_DIR = BASE / "figures" / "technical_synthesis"
ASSETS = BASE / "assets"
FONT_DIR = ASSETS / "fonts"
JIAZI_LOGO = ASSETS / "jiazi_logo.png"
NOTO_SC_REGULAR = FONT_DIR / "NotoSansSC-Regular.ttf"
NOTO_SC_BOLD = FONT_DIR / "NotoSansSC-Bold.ttf"

OUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_STEM = "fig5_v4_tech_module_evolution_v2"
CSV_NAME = "deepseek_tech_evolution_modules.csv"

COLORS = {
    "main": "#6F35B6",
    "arch": "#7C3FBD",
    "attn": "#E45C9B",
    "train": "#D88A1F",
    "rl": "#2F9B72",
    "cache": "#2F6FB3",
    "multi": "#8A8798",
    "text": "#15151A",
    "body": "#2F2F36",
    "muted": "#5B5B63",
    "line": "#C8C5D1",
}

LANES = [
    ("模型架构 / MoE", "arch", 0.700),
    ("注意力与长上下文", "attn", 0.604),
    ("训练效率与稳定性", "train", 0.508),
    ("推理 / RL / 后训练", "rl", 0.412),
    ("记忆、缓存与推理系统", "cache", 0.316),
    ("多模态 / OCR 旁路探索", "multi", 0.220),
]

STAGES = {
    "DeepSeek LLM": {"x": 0.235, "date": "2024.01"},
    "DeepSeek-V2": {"x": 0.360, "date": "2024.05"},
    "DeepSeek-V3": {"x": 0.485, "date": "2024.12"},
    "DeepSeek-R1": {"x": 0.595, "date": "2025.01"},
    "DeepSeek-V3.2": {"x": 0.715, "date": "2025.12"},
    "DeepSeek-V4": {"x": 0.860, "date": "2026.05"},
}

MODULE_ROWS = [
    {
        "id": "dense_base",
        "model_or_paper": "DeepSeek LLM",
        "date": "2024-01",
        "stage": "DeepSeek LLM",
        "tech_lane": "模型架构 / MoE",
        "tech_module": "稠密基座",
        "problem_solved": "建立主线训练底座",
        "inherits_from": "",
        "feeds_into": "DeepSeek-V2",
        "confidence": "high",
        "note": "LLaMA式架构；规模律与预训练流程",
    },
    {
        "id": "ds_moe_v2",
        "model_or_paper": "DeepSeek-V2",
        "date": "2024-05",
        "stage": "DeepSeek-V2",
        "tech_lane": "模型架构 / MoE",
        "tech_module": "DeepSeekMoE",
        "problem_solved": "稀疏计算扩容",
        "inherits_from": "稠密基座",
        "feeds_into": "DeepSeek-V3; DeepSeek-V4",
        "confidence": "high",
        "note": "V2 report / DeepSeekMoE",
    },
    {
        "id": "moe_balance_v3",
        "model_or_paper": "DeepSeek-V3",
        "date": "2024-12",
        "stage": "DeepSeek-V3",
        "tech_lane": "模型架构 / MoE",
        "tech_module": "Aux-loss-free Load Balancing",
        "problem_solved": "稳住大规模 MoE",
        "inherits_from": "DeepSeekMoE",
        "feeds_into": "DeepSeek-V4",
        "confidence": "high",
        "note": "auxiliary-loss-free load balancing",
    },
    {
        "id": "moe_v4",
        "model_or_paper": "DeepSeek-V4",
        "date": "2026-05",
        "stage": "DeepSeek-V4",
        "tech_lane": "模型架构 / MoE",
        "tech_module": "DeepSeekMoE + MTP",
        "problem_solved": "主干架构继续扩展",
        "inherits_from": "DeepSeekMoE; MTP; Aux-loss-free Load Balancing",
        "feeds_into": "DeepSeek-V4",
        "confidence": "high",
        "note": "并集成 Hybrid Attention、mHC、Muon 等新模块",
    },
    {
        "id": "mla_v2",
        "model_or_paper": "DeepSeek-V2",
        "date": "2024-05",
        "stage": "DeepSeek-V2",
        "tech_lane": "注意力与长上下文",
        "tech_module": "MLA",
        "problem_solved": "压缩 KV Cache",
        "inherits_from": "",
        "feeds_into": "DeepSeek-V3; DeepSeek-V3.2; DeepSeek-V4",
        "confidence": "high",
        "note": "Multi-head Latent Attention",
    },
    {
        "id": "mla_v3",
        "model_or_paper": "DeepSeek-V3",
        "date": "2024-12",
        "stage": "DeepSeek-V3",
        "tech_lane": "注意力与长上下文",
        "tech_module": "MLA 延续",
        "problem_solved": "高效注意力底座",
        "inherits_from": "MLA",
        "feeds_into": "DeepSeek-R1; DeepSeek-V3.2; DeepSeek-V4",
        "confidence": "high",
        "note": "V3 adopts MLA validated in V2",
    },
    {
        "id": "r1_v3_base_attn",
        "model_or_paper": "DeepSeek-R1",
        "date": "2025-01",
        "stage": "DeepSeek-R1",
        "tech_lane": "注意力与长上下文",
        "tech_module": "沿用 V3 基座",
        "problem_solved": "注意力非主创新",
        "inherits_from": "MLA",
        "feeds_into": "DeepSeek-V3.2; DeepSeek-V4",
        "confidence": "medium",
        "note": "R1核心在后训练/RL，不是注意力架构升级",
    },
    {
        "id": "dsa_v32",
        "model_or_paper": "DeepSeek-V3.2",
        "date": "2025-12",
        "stage": "DeepSeek-V3.2",
        "tech_lane": "注意力与长上下文",
        "tech_module": "DSA",
        "problem_solved": "长上下文效率",
        "inherits_from": "MLA 延续; 相关 Sparse Attention 系统探索",
        "feeds_into": "DeepSeek-V4",
        "confidence": "high",
        "note": "DeepSeek Sparse Attention under MLA",
    },
    {
        "id": "csa_hca_v4",
        "model_or_paper": "DeepSeek-V4",
        "date": "2026-05",
        "stage": "DeepSeek-V4",
        "tech_lane": "注意力与长上下文",
        "tech_module": "Hybrid Attention: CSA + HCA",
        "problem_solved": "面向 1M 上下文",
        "inherits_from": "DSA; MLA 延续",
        "feeds_into": "DeepSeek-V4",
        "confidence": "high",
        "note": "CSA应用DSA；HCA做更重压缩",
    },
    {
        "id": "fp8_v2",
        "model_or_paper": "DeepSeek-V2",
        "date": "2024-05",
        "stage": "DeepSeek-V2",
        "tech_lane": "训练效率与稳定性",
        "tech_module": "FP8 / KV 量化",
        "problem_solved": "降低推理与训练成本",
        "inherits_from": "",
        "feeds_into": "DeepSeek-V3",
        "confidence": "medium",
        "note": "V2 serving optimization",
    },
    {
        "id": "fp8_v3",
        "model_or_paper": "DeepSeek-V3",
        "date": "2024-12",
        "stage": "DeepSeek-V3",
        "tech_lane": "训练效率与稳定性",
        "tech_module": "FP8 训练 + DualPipe",
        "problem_solved": "低成本大规模训练",
        "inherits_from": "FP8 / KV 量化",
        "feeds_into": "DeepSeek-V4",
        "confidence": "high",
        "note": "mixed precision training / pipeline overlap",
    },
    {
        "id": "mhc_v4",
        "model_or_paper": "DeepSeek-V4; mHC",
        "date": "2026-05",
        "stage": "DeepSeek-V4",
        "tech_lane": "训练效率与稳定性",
        "tech_module": "mHC + Muon",
        "problem_solved": "更大 MoE 稳定训练",
        "inherits_from": "FP8 训练 + DualPipe",
        "feeds_into": "DeepSeek-V4",
        "confidence": "high",
        "note": "Manifold-Constrained Hyper-Connections / Muon optimizer",
    },
    {
        "id": "sft_rl_llm",
        "model_or_paper": "DeepSeek LLM / DeepSeek-V2",
        "date": "2024-01/2024-05",
        "stage": "DeepSeek LLM",
        "tech_lane": "推理 / RL / 后训练",
        "tech_module": "SFT / RL 对齐",
        "problem_solved": "对话与基础能力释放",
        "inherits_from": "",
        "feeds_into": "DeepSeek-V3",
        "confidence": "high",
        "note": "SFT and alignment pipeline",
    },
    {
        "id": "v3_rl",
        "model_or_paper": "DeepSeek-V3",
        "date": "2024-12",
        "stage": "DeepSeek-V3",
        "tech_lane": "推理 / RL / 后训练",
        "tech_module": "SFT + RL",
        "problem_solved": "释放基座能力",
        "inherits_from": "SFT / RL 对齐",
        "feeds_into": "DeepSeek-R1",
        "confidence": "high",
        "note": "V3 post-training",
    },
    {
        "id": "r1_grpo",
        "model_or_paper": "DeepSeek-R1",
        "date": "2025-01",
        "stage": "DeepSeek-R1",
        "tech_lane": "推理 / RL / 后训练",
        "tech_module": "GRPO / 推理RL",
        "problem_solved": "强化长链推理",
        "inherits_from": "SFT + RL",
        "feeds_into": "DeepSeek-V3.2; DeepSeek-V4",
        "confidence": "high",
        "note": "R1 built on V3-Base with GRPO",
    },
    {
        "id": "v32_agent_rl",
        "model_or_paper": "DeepSeek-V3.2",
        "date": "2025-12",
        "stage": "DeepSeek-V3.2",
        "tech_lane": "推理 / RL / 后训练",
        "tech_module": "推理 + Agent 后训练",
        "problem_solved": "面向复杂任务",
        "inherits_from": "GRPO / 推理RL",
        "feeds_into": "DeepSeek-V4",
        "confidence": "high",
        "note": "mixed RL training with GRPO",
    },
    {
        "id": "v4_posttrain",
        "model_or_paper": "DeepSeek-V4",
        "date": "2026-05",
        "stage": "DeepSeek-V4",
        "tech_lane": "推理 / RL / 后训练",
        "tech_module": "综合后训练",
        "problem_solved": "推理/工具/Agent 集成",
        "inherits_from": "推理 + Agent 后训练; GRPO / 推理RL",
        "feeds_into": "DeepSeek-V4",
        "confidence": "high",
        "note": "comprehensive post-training pipeline",
    },
    {
        "id": "mtp_v3",
        "model_or_paper": "DeepSeek-V3",
        "date": "2024-12",
        "stage": "DeepSeek-V3",
        "tech_lane": "记忆、缓存与推理系统",
        "tech_module": "MTP",
        "problem_solved": "可用于推测解码",
        "inherits_from": "",
        "feeds_into": "DeepSeek-V4",
        "confidence": "high",
        "note": "Multi-Token Prediction",
    },
    {
        "id": "v32_context",
        "model_or_paper": "DeepSeek-V3.2",
        "date": "2025-12",
        "stage": "DeepSeek-V3.2",
        "tech_lane": "记忆、缓存与推理系统",
        "tech_module": "128K 长上下文工程",
        "problem_solved": "训练扩展 / 推理效率",
        "inherits_from": "MLA; DSA",
        "feeds_into": "DeepSeek-V4",
        "confidence": "high",
        "note": "128K long-context extension data",
    },
    {
        "id": "memory_systems",
        "model_or_paper": "Engram; Conditional Memory",
        "date": "2026-01/2026-02",
        "stage": "related_system_paper",
        "tech_lane": "记忆、缓存与推理系统",
        "tech_module": "Engram / Conditional Memory",
        "problem_solved": "知识查找 / 静态记忆",
        "inherits_from": "memory / lookup 系统探索",
        "feeds_into": "DeepSeek-V4",
        "confidence": "low",
        "note": "相关 memory 探索；非V4报告明确继承模块",
    },
    {
        "id": "v4_1m_context",
        "model_or_paper": "DeepSeek-V4",
        "date": "2026-05",
        "stage": "DeepSeek-V4",
        "tech_lane": "记忆、缓存与推理系统",
        "tech_module": "1M 上下文系统",
        "problem_solved": "降 FLOPs / KV Cache",
        "inherits_from": "Hybrid Attention: CSA + HCA; 128K 长上下文工程",
        "feeds_into": "DeepSeek-V4",
        "confidence": "high",
        "note": "Hybrid Attention 改善长上下文效率",
    },
    {
        "id": "janus_vl",
        "model_or_paper": "DeepSeek-VL; Janus; Janus-Pro",
        "date": "2024-03/2025-01",
        "stage": "related_multimodal_paper",
        "tech_lane": "多模态 / OCR 旁路探索",
        "tech_module": "视觉 / 多模态",
        "problem_solved": "理解与生成探索",
        "inherits_from": "",
        "feeds_into": "DeepSeek-OCR",
        "confidence": "medium",
        "note": "VL / Janus series",
    },
    {
        "id": "ocr_compress",
        "model_or_paper": "DeepSeek-OCR; DeepSeek-OCR 2",
        "date": "2025-10/2026-01",
        "stage": "related_multimodal_paper",
        "tech_lane": "多模态 / OCR 旁路探索",
        "tech_module": "OCR 信息压缩",
        "problem_solved": "复杂文档压缩理解",
        "inherits_from": "视觉 / 多模态",
        "feeds_into": "DeepSeek-V4",
        "confidence": "low",
        "note": "Contexts Optical Compression / Visual Causal Flow",
    },
    {
        "id": "v4_multimodal_note",
        "model_or_paper": "DeepSeek-V4",
        "date": "2026-05",
        "stage": "DeepSeek-V4",
        "tech_lane": "多模态 / OCR 旁路探索",
        "tech_module": "多模态 / OCR 经验",
        "problem_solved": "弱关联，非主干架构",
        "inherits_from": "OCR 信息压缩",
        "feeds_into": "DeepSeek-V4",
        "confidence": "low",
        "note": "解释性弱关联；不作为V4主干架构线",
    },
]

EDGE_SPECS = [
    ("dense_base", "ds_moe_v2", "high"),
    ("ds_moe_v2", "moe_balance_v3", "high"),
    ("moe_balance_v3", "moe_v4", "high"),
    ("mla_v2", "mla_v3", "high"),
    ("mla_v3", "r1_v3_base_attn", "medium"),
    ("mla_v3", "dsa_v32", "high"),
    ("dsa_v32", "csa_hca_v4", "high"),
    ("fp8_v2", "fp8_v3", "medium"),
    ("fp8_v3", "mhc_v4", "high"),
    ("sft_rl_llm", "v3_rl", "high"),
    ("v3_rl", "r1_grpo", "high"),
    ("r1_grpo", "v32_agent_rl", "high"),
    ("v32_agent_rl", "v4_posttrain", "high"),
    ("mtp_v3", "v32_context", "medium"),
    ("v32_context", "v4_1m_context", "high"),
    ("memory_systems", "v4_1m_context", "low"),
    ("janus_vl", "ocr_compress", "medium"),
    ("ocr_compress", "v4_multimodal_note", "low"),
]

DISPLAY_NOTES = {
    "janus_vl": "VL / Janus",
    "ocr_compress": "DeepSeek-OCR",
    "v4_multimodal_note": "弱关联",
}

DRAW_IDS = {row["id"] for row in MODULE_ROWS} - {"r1_v3_base_attn"}

DISPLAY_LABELS = {
    "moe_balance_v3": "Aux-loss-free\nLoad Balancing",
    "moe_v4": "DeepSeekMoE\n+ MTP",
    "dsa_v32": "DSA\nDeepSeek Sparse\nAttention",
    "csa_hca_v4": "Hybrid Attention\nCSA + HCA",
    "v32_agent_rl": "推理 + Agent\n后训练",
    "v4_posttrain": "综合后训练",
    "v32_context": "128K 长上下文\n工程",
    "memory_systems": "Engram /\nCond. Memory",
    "v4_1m_context": "1M 上下文系统",
    "v4_multimodal_note": "多模态 / OCR\n经验",
}

DISPLAY_PROBLEMS = {
    "dsa_v32": "长上下文效率",
    "csa_hca_v4": "CSA + HCA\n面向 1M 上下文",
    "v32_context": "训练扩展 /\n推理效率",
    "memory_systems": "知识查找 / 静态记忆",
}


def configure_font() -> None:
    for path in [
        NOTO_SC_REGULAR,
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
    ]:
        if path.exists():
            font_manager.fontManager.addfont(str(path))
            plt.rcParams["font.family"] = font_manager.FontProperties(fname=str(path)).get_name()
            break
    plt.rcParams["axes.unicode_minus"] = False


def font_prop(size: float, weight: str | None = None) -> font_manager.FontProperties:
    candidates = [
        NOTO_SC_BOLD if weight == "bold" else NOTO_SC_REGULAR,
        Path(r"C:\Windows\Fonts\msyhbd.ttc") if weight == "bold" else Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\msyh.ttc"),
        Path(r"C:\Windows\Fonts\simhei.ttf"),
    ]
    path = next((p for p in candidates if p and p.exists()), None)
    kwargs: dict[str, object] = {"size": size}
    if weight:
        kwargs["weight"] = weight
    if path:
        return font_manager.FontProperties(fname=str(path), **kwargs)
    return font_manager.FontProperties(**kwargs)


def blend(color: str, target: str = "#FFFFFF", amount: float = 0.86) -> str:
    def parse(hex_color: str) -> tuple[int, int, int]:
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

    a = parse(color)
    b = parse(target)
    mixed = tuple(round(a[i] * (1 - amount) + b[i] * amount) for i in range(3))
    return "#{:02X}{:02X}{:02X}".format(*mixed)


def lane_color(lane: str) -> str:
    key = next(k for name, k, _ in LANES if name == lane)
    return COLORS[key]


def draw_jiazi_logo(fig: plt.Figure, x: float = 0.833, y: float = 0.025, scale: float = 0.682) -> None:
    if not JIAZI_LOGO.exists():
        return
    try:
        logo_ax = fig.add_axes([x, y, 0.170 * scale, 0.060 * scale])
        logo_ax.imshow(plt.imread(JIAZI_LOGO))
        logo_ax.set_axis_off()
    except Exception:
        return


def node_geometry(row: dict[str, str]) -> tuple[float, float, float, float]:
    stage_x = {
        "DeepSeek LLM": 0.235,
        "DeepSeek-V2": 0.360,
        "DeepSeek-V3": 0.485,
        "DeepSeek-R1": 0.595,
        "DeepSeek-V3.2": 0.715,
        "DeepSeek-V4": 0.860,
        "related_system_paper": 0.642,
        "related_multimodal_paper": 0.385 if row["id"] == "janus_vl" else 0.615,
    }
    lane_y = {name: y for name, _, y in LANES}[row["tech_lane"]]
    x = stage_x[row["stage"]]
    if row["id"] == "sft_rl_llm":
        x = 0.295
    if row["id"] == "dense_base":
        x = 0.252
    if row["id"] == "ds_moe_v2":
        x = 0.386
    if row["id"] == "moe_balance_v3":
        x = 0.545
    if row["id"] == "v3_rl":
        x = 0.465
    if row["id"] == "r1_grpo":
        x = 0.590
    if row["id"] == "v32_agent_rl":
        x = 0.710
    if row["id"] == "v4_posttrain":
        x = 0.872
    if row["id"] == "fp8_v2":
        x = 0.345
    if row["id"] == "fp8_v3":
        x = 0.505
    if row["id"] == "memory_systems":
        x = 0.730
    if row["id"] == "mtp_v3":
        x = 0.505
    if row["id"] == "dsa_v32":
        x = 0.690
    if row["id"] == "v32_context":
        x = 0.642
    if row["id"] == "v4_1m_context":
        x = 0.872
    if row["stage"] == "DeepSeek-V4":
        x = 0.872
    y = lane_y
    if row["id"] in {"mtp_v3", "v32_context", "memory_systems"}:
        y = lane_y
    w = 0.110
    if row["id"] == "dense_base":
        w = 0.104
    if row["id"] == "ds_moe_v2":
        w = 0.112
    if row["stage"] == "DeepSeek-V4":
        w = 0.128
    if len(row["tech_module"]) >= 11:
        w = 0.136
    if row["id"] in {"moe_balance_v3", "moe_v4", "csa_hca_v4", "v4_posttrain"}:
        w = 0.142
    if row["id"] == "moe_balance_v3":
        w = 0.124
    if row["id"] in {"memory_systems", "v4_1m_context", "v4_multimodal_note", "dsa_v32", "v32_agent_rl"}:
        w = 0.135
    if row["id"] == "mtp_v3":
        w = 0.088
    if row["id"] == "v32_context":
        w = 0.104
    if row["id"] == "memory_systems":
        w = 0.066
    if row["id"] == "v4_1m_context":
        w = 0.124
    if row["id"] == "v3_rl":
        w = 0.104
    if row["id"] == "r1_grpo":
        w = 0.108
    if row["id"] == "v32_agent_rl":
        w = 0.104
    if row["id"] == "v4_posttrain":
        w = 0.118
    if row["stage"] == "DeepSeek-V4":
        w = 0.124
    h = 0.061
    if row["id"] in {"mtp_v3", "v32_context", "memory_systems", "v4_1m_context"}:
        h = 0.052
    if row["id"] == "memory_systems":
        h = 0.050
    if row["id"] == "v32_context":
        h = 0.058
    if row["stage"] == "DeepSeek-V4":
        h = 0.061
    return x, y, w, h


def draw_header(fig: plt.Figure) -> None:
    fig.add_artist(Rectangle((0.044, 0.922), 0.006, 0.058, transform=fig.transFigure, color=COLORS["main"], linewidth=0))
    fig.text(
        0.062,
        0.958,
        "V4 的来路：DeepSeek 两年主线技术如何收束",
        ha="left",
        va="center",
        fontproperties=font_prop(22.4, "bold"),
        color=COLORS["text"],
    )
    fig.text(
        0.062,
        0.915,
        "LLM 打底，V2/V3 把 MoE、MLA、FP8 与工程训练推向主线，R1 则把推理 / RL 拉到核心位置。",
        ha="left",
        va="center",
        fontproperties=font_prop(12.4),
        color=COLORS["body"],
    )
    fig.text(
        0.062,
        0.891,
        "到 V3.2，长上下文与系统效率问题进一步前置；V4 再把 DeepSeekMoE、MTP、Hybrid Attention、",
        ha="left",
        va="center",
        fontproperties=font_prop(12.4),
        color=COLORS["body"],
    )
    fig.text(
        0.062,
        0.868,
        "mHC、Muon 与后训练能力集中集成，形成两年路线的收束点。",
        ha="left",
        va="center",
        fontproperties=font_prop(12.4),
        color=COLORS["body"],
    )


def draw_stage_axis(ax: plt.Axes) -> None:
    y = 0.790
    ax.add_patch(
        FancyArrowPatch(
            (0.165, y),
            (0.910, y),
            arrowstyle="-|>",
            mutation_scale=18,
            linewidth=4.5,
            color=COLORS["main"],
            alpha=0.24,
            zorder=1,
        )
    )
    for stage, info in STAGES.items():
        x = info["x"]
        is_v4 = stage == "DeepSeek-V4"
        w = 0.100 if not is_v4 else 0.128
        h = 0.048 if not is_v4 else 0.058
        face = COLORS["main"] if is_v4 else "#FFFFFF"
        edge = COLORS["main"]
        text_color = "#FFFFFF" if is_v4 else COLORS["main"]
        ax.add_patch(
            FancyBboxPatch(
                (x - w / 2, y - h / 2),
                w,
                h,
                boxstyle="round,pad=0.006,rounding_size=0.020",
                linewidth=1.35 if not is_v4 else 1.9,
                edgecolor=edge,
                facecolor=face,
                zorder=4,
            )
        )
        label = stage.replace("DeepSeek-", "").replace("DeepSeek LLM", "LLM")
        if stage == "DeepSeek-V4":
            label = "DeepSeek\nV4"
        ax.text(
            x,
            y + (0.002 if is_v4 else 0.0),
            label,
            ha="center",
            va="center",
            fontproperties=font_prop(10.7 if not is_v4 else 12.4, "bold"),
            color=text_color,
            zorder=5,
            linespacing=0.85,
        )
        ax.text(
            x,
            y - 0.042 if not is_v4 else y - 0.049,
            info["date"],
            ha="center",
            va="center",
            fontproperties=font_prop(8.1),
            color="#777381",
            zorder=5,
        )


def draw_lanes(ax: plt.Axes) -> None:
    for lane, key, y in LANES:
        color = COLORS[key]
        lane_h = 0.084
        ax.add_patch(Rectangle((0.055, y - lane_h / 2), 0.895, lane_h, color=blend(color, amount=0.94), linewidth=0, alpha=0.42, zorder=0))
        ax.add_patch(Rectangle((0.055, y - lane_h / 2), 0.006, lane_h, color=color, linewidth=0, alpha=0.95, zorder=1))
        ax.text(0.071, y + 0.015, lane, ha="left", va="center", fontproperties=font_prop(9.8, "bold"), color=color, zorder=2)
    ax.add_patch(
        FancyBboxPatch(
            (0.775, 0.169),
            0.165,
            0.574,
            boxstyle="round,pad=0.006,rounding_size=0.020",
            linewidth=1.0,
            edgecolor=blend(COLORS["main"], amount=0.35),
            facecolor=blend(COLORS["main"], amount=0.94),
            alpha=0.55,
            zorder=0.5,
        )
    )


def draw_node(ax: plt.Axes, row: dict[str, str]) -> tuple[float, float, float, float]:
    x, y, w, h = node_geometry(row)
    color = lane_color(row["tech_lane"])
    is_v4 = row["stage"] == "DeepSeek-V4"
    face = blend(color, amount=0.90 if not is_v4 else 0.84)
    edge = color if not is_v4 else COLORS["main"]
    low_confidence = row["confidence"] == "low"
    lw = 1.1 if not is_v4 else 1.5
    if low_confidence:
        lw = 0.95
    ax.add_patch(
        FancyBboxPatch(
            (x - w / 2, y - h / 2),
            w,
            h,
            boxstyle="round,pad=0.005,rounding_size=0.014",
            linewidth=lw,
            edgecolor=edge,
            facecolor=face,
            linestyle="--" if low_confidence else "-",
            zorder=6,
        )
    )
    module_label = DISPLAY_LABELS.get(row["id"], row["tech_module"])
    label_size = 7.95 if len(module_label.replace("\n", "")) > 12 else 8.75
    if row["id"] == "dsa_v32":
        label_size = 6.35
    if row["id"] == "memory_systems":
        label_size = 5.25
    if row["id"] == "v32_context":
        label_size = 6.7
    ax.text(x, y + h * 0.18, module_label, ha="center", va="center", fontproperties=font_prop(label_size, "bold"), color=edge, zorder=7, linespacing=0.95)
    problem_label = DISPLAY_PROBLEMS.get(row["id"], row["problem_solved"])
    problem_size = 7.75
    if row["id"] == "memory_systems":
        problem_size = 5.25
    if row["id"] == "v32_context":
        problem_size = 6.55
    ax.text(x, y - h * 0.18, problem_label, ha="center", va="center", fontproperties=font_prop(problem_size), color=COLORS["body"], zorder=7, linespacing=1.05)
    note = DISPLAY_NOTES.get(row["id"], "")
    if note:
        ax.text(x, y - h * 0.36, note, ha="center", va="top", fontproperties=font_prop(6.65), color="#76717E", zorder=7)
    return x, y, w, h


def draw_edge(ax: plt.Axes, src: tuple[float, float, float, float], dst: tuple[float, float, float, float], color: str, confidence: str) -> None:
    sx, sy, sw, _ = src
    dx, dy, dw, _ = dst
    rad = 0.0
    if abs(dy - sy) > 0.02:
        rad = 0.10 if dy > sy else -0.10
    linestyle = "--" if confidence == "low" else "-"
    alpha = 0.30 if confidence == "low" else 0.52 if confidence == "medium" else 0.62
    linewidth = 1.05 if confidence == "low" else 1.35 if confidence == "medium" else 1.55
    ax.add_patch(
        FancyArrowPatch(
            (sx + sw / 2 + 0.004, sy),
            (dx - dw / 2 - 0.004, dy),
            arrowstyle="-|>",
            mutation_scale=10.5,
            connectionstyle=f"arc3,rad={rad}",
            linewidth=linewidth,
            linestyle=linestyle,
            color=color,
            alpha=alpha,
            zorder=3,
        )
    )


def draw_graph(ax: plt.Axes) -> None:
    draw_lanes(ax)
    geometries: dict[str, tuple[float, float, float, float]] = {}
    for row in MODULE_ROWS:
        if row["id"] not in DRAW_IDS:
            continue
        geometries[row["id"]] = draw_node(ax, row)
    row_by_id = {row["id"]: row for row in MODULE_ROWS}
    for src_id, dst_id, confidence in EDGE_SPECS:
        if src_id not in geometries or dst_id not in geometries:
            continue
        color = lane_color(row_by_id[dst_id]["tech_lane"])
        draw_edge(ax, geometries[src_id], geometries[dst_id], color, confidence)


def draw_v4_callout(ax: plt.Axes) -> None:
    x, y, w, h = 0.605, 0.842, 0.310, 0.058
    ax.add_patch(
        FancyBboxPatch(
            (x, y - h / 2),
            w,
            h,
            boxstyle="round,pad=0.007,rounding_size=0.016",
            linewidth=1.05,
            edgecolor=COLORS["main"],
            facecolor=blend(COLORS["main"], amount=0.92),
            zorder=5,
        )
    )
    ax.text(x + 0.014, y + 0.014, "V4：系统级集成点", ha="left", va="center", fontproperties=font_prop(9.5, "bold"), color=COLORS["main"], zorder=6)
    ax.text(
        x + 0.014,
        y - 0.010,
        "把架构、注意力、训练稳定性、推理、缓存等技术线\n重新组织进主线模型。",
        ha="left",
        va="center",
        fontproperties=font_prop(7.2),
        color=COLORS["body"],
        zorder=6,
        linespacing=1.15,
    )


def draw_takeaways(ax: plt.Axes) -> None:
    items = [
        (COLORS["main"], "不是线性升级", "主线模型不断复用、改造并集成多条技术线"),
        (COLORS["attn"], "底层问题变重", "V3/R1/V3.2 后，效率、长上下文、缓存更关键"),
        (COLORS["rl"], "V4 并非突变", "它是两年技术路线的系统级收束"),
    ]
    xs = [0.082, 0.376, 0.670]
    for x, (color, title, body) in zip(xs, items):
        ax.add_patch(Rectangle((x, 0.156), 0.006, 0.058, color=color, linewidth=0, zorder=4))
        ax.text(x + 0.018, 0.196, title, ha="left", va="center", fontproperties=font_prop(10.8, "bold"), color=color, zorder=4)
        ax.text(x + 0.018, 0.170, body, ha="left", va="center", fontproperties=font_prop(7.95), color=COLORS["body"], zorder=4)


def draw_footer(fig: plt.Figure) -> None:
    fig.add_artist(Rectangle((0.052, 0.112), 0.896, 0.0010, transform=fig.transFigure, color=COLORS["line"], linewidth=0))
    footer = font_prop(7.7)
    fig.text(0.052, 0.089, "数据来源：DeepSeek LLM/V2/V3/R1/V3.2/V4 技术报告，相关系统、数学/推理、多模态论文，Hugging Face Papers API。", ha="left", va="center", fontproperties=footer, color="#555555")
    fig.text(0.052, 0.069, "口径：按技术模块而非论文标题归类；时间轴标注主线报告发布时间，部分模块跨阶段累积形成。", ha="left", va="center", fontproperties=footer, color="#555555")
    fig.text(0.052, 0.051, "注：Engram / Cond. Memory、DualPath 及多模态/OCR 相关工作按跨路线经验或弱关联处理；", ha="left", va="center", fontproperties=footer, color="#555555")
    fig.text(0.052, 0.035, "图中连线用于说明技术延续与收束关系，不代表严格的一一对应。", ha="left", va="center", fontproperties=footer, color="#555555")
    fig.text(0.052, 0.018, "制图：甲子光年", ha="left", va="center", fontproperties=footer, color="#555555")
    draw_jiazi_logo(fig)


def export_modules_csv() -> Path:
    fields = [
        "model_or_paper",
        "date",
        "stage",
        "tech_lane",
        "tech_module",
        "problem_solved",
        "inherits_from",
        "feeds_into",
        "confidence",
        "note",
    ]
    csv_path = OUT_DIR / CSV_NAME
    data = pd.DataFrame([{field: row.get(field, "") for field in fields} for row in MODULE_ROWS])
    try:
        data.to_csv(csv_path, index=False, encoding="utf-8-sig")
    except PermissionError:
        fallback = OUT_DIR / "deepseek_tech_evolution_modules_latest.csv"
        data.to_csv(fallback, index=False, encoding="utf-8-sig")
        return fallback
    return csv_path


def main() -> None:
    configure_font()
    fig = plt.figure(figsize=(8.35, 11.8), dpi=240)
    fig.patch.set_facecolor("#FFFFFF")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()

    draw_header(fig)
    draw_stage_axis(ax)
    draw_graph(ax)
    draw_footer(fig)

    out_png = OUT_DIR / f"{OUTPUT_STEM}.png"
    out_svg = OUT_DIR / f"{OUTPUT_STEM}.svg"
    fig.savefig(out_png, dpi=300, facecolor=fig.get_facecolor())
    fig.savefig(out_svg, facecolor=fig.get_facecolor())
    plt.close(fig)
    csv_path = export_modules_csv()
    print(out_png)
    print(out_svg)
    print(csv_path)


if __name__ == "__main__":
    main()


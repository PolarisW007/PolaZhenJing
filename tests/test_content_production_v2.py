import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from content_production_v2 import normalize_signal_summary, render_review_markdown, review_article


def test_normalize_signal_summary_marks_missing_sources():
    summary = normalize_signal_summary(
        "AI 内容生产",
        [
            {
                "source": "X",
                "available": False,
                "summary": "抓取失败",
                "clusters": ["创作者流程"],
                "controversies": ["是否需要 token"],
                "links": [],
            },
            {
                "source": "GitHub",
                "available": True,
                "summary": "可用",
                "clusters": ["去 AI 味"],
                "controversies": ["规则库 vs prompt"],
                "links": ["https://github.com/example/repo"],
            },
        ],
    )

    assert summary["status"] == "partial"
    assert summary["missing_sources"] == ["X"]
    assert "去 AI 味" in summary["clusters"]


def test_review_article_flags_generic_structure_and_missing_evidence():
    report = review_article(
        "首先，我们可以看到这个行业正在快速发展。\n\n其次，这带来了新的可能。\n\n最后，我们应该保持关注。"
    )

    assert "首先" in "".join(report["chinese_tone"])
    assert any("模板结构" in item for item in report["structural_patterns"])
    assert report["evidence_ok"] is False


def test_render_review_markdown_includes_signal_section():
    signal_summary = normalize_signal_summary(
        "创作者内容系统",
        [
            {
                "source": "GitHub",
                "available": True,
                "summary": "发现多个去 AI 味项目",
                "clusters": ["规则库", "风格蒸馏"],
                "controversies": ["检测器是否可靠"],
                "links": ["https://github.com/example/repo"],
            }
        ],
    )
    markdown = render_review_markdown(
        "创作者内容系统",
        "昨天我在看一个创作者后台，发现它最大的毛病不是不会写，而是没有来源。",
        signal_summary=signal_summary,
    )

    assert "## 实时信号摘要" in markdown
    assert "规则库" in markdown


def test_cli_generates_capability_map_and_review(tmp_path):
    article = tmp_path / "article.md"
    article.write_text("首先，这是一篇很空泛的文章。", encoding="utf-8")
    signals = tmp_path / "signals.json"
    signals.write_text(
        json.dumps(
            [{"source": "X", "available": False, "summary": "抓取失败", "links": []}],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    review_path = tmp_path / "review.md"

    capability = subprocess.run(
        [sys.executable, "scripts/content_production_v2.py", "capability-map", "--format", "json"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    assert capability.returncode == 0
    assert "last30days-skill" in capability.stdout

    review = subprocess.run(
        [
            sys.executable,
            "scripts/content_production_v2.py",
            "review",
            "--topic",
            "测试主题",
            "--article",
            str(article),
            "--signals",
            str(signals),
            "--output",
            str(review_path),
        ],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    assert review.returncode == 0
    assert review_path.exists()
    assert "来源缺失" in review_path.read_text(encoding="utf-8")

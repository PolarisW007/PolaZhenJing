#!/usr/bin/env python3
"""Validate the Pola skill framework structure and content.

This harness intentionally checks practical authoring quality, not just YAML
frontmatter. It is conservative: failures should be fixed before treating the
framework as ready for reuse.
"""

from __future__ import annotations

import re
import stat
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

SKILLS = [
    "pola-agent-delivery-framework",
    "pola-project-context-reader",
    "pola-requirement-analyzer",
    "pola-architecture-doc-writer",
    "pola-implementation-runner",
    "pola-code-review-gate",
    "pola-test-gate",
    "pola-integration-regression-gate",
    "pola-deploy-release-gate",
    "pola-devlog-git-finalizer",
]

REQUIRED_SECTIONS = {
    "pola-agent-delivery-framework": [
        "目标",
        "输入形态",
        "产物目录约定",
        "执行模式",
        "总控流程",
        "门禁规则",
        "失败处理",
        "阶段状态记录",
        "最终汇报",
    ],
    "pola-project-context-reader": [
        "目标",
        "读取范围",
        "默认流程",
        "推荐脚本",
        "命令发现规则",
        "项目画像字段",
        "输出格式",
        "注意事项",
    ],
    "pola-requirement-analyzer": [
        "目标",
        "需求质量标准",
        "输入来源",
        "默认流程",
        "需求分类",
        "澄清问题规则",
        "验收标准写法",
        "输出模板",
        "图片处理规则",
    ],
    "pola-architecture-doc-writer": [
        "目标",
        "何时需要完整架构文档",
        "默认流程",
        "设计步骤",
        "文档结构",
        "写作规则",
        "存放规则",
        "完成标准",
    ],
    "pola-implementation-runner": [
        "目标",
        "输入",
        "开工前检查",
        "代码阅读方法",
        "编码流程",
        "改动粒度",
        "测试同步策略",
        "变更映射表",
        "遇到脏文件",
        "禁止项",
        "输出",
        "完成标准",
    ],
    "pola-code-review-gate": [
        "目标",
        "输入",
        "Review 顺序",
        "检查项",
        "专项检查矩阵",
        "Review 方法",
        "输出格式",
        "严重程度",
        "修复策略",
        "Pass 条件",
    ],
    "pola-test-gate": [
        "目标",
        "输入",
        "默认流程",
        "推荐脚本",
        "常见命令选择",
        "测试选择规则",
        "失败分类",
        "证据记录",
        "输出",
        "进入下一阶段条件",
    ],
    "pola-integration-regression-gate": [
        "目标",
        "输入",
        "默认流程",
        "验证类型",
        "真实链路设计",
        "前端浏览器验证",
        "API 验证",
        "Bugfix 回归规则",
        "部署后回归",
        "输出",
        "注意事项",
    ],
    "pola-deploy-release-gate": [
        "目标",
        "输入",
        "默认流程",
        "发布面判断",
        "发布前 checklist",
        "发布清单模板",
        "高危操作规则",
        "部署执行规则",
        "回滚方案要求",
        "输出",
        "Ready 判定",
    ],
    "pola-devlog-git-finalizer": [
        "目标",
        "输入",
        "默认流程",
        "复用建议",
        "文档更新规则",
        "Diff 卫生检查",
        "Commit 准备",
        "输出",
        "Commit 规则",
        "Commit message 模板",
        "完成标准",
    ],
}

REQUIRED_REFERENCES = {
    "pola-agent-delivery-framework": [
        "references/workflow-gates.md",
        "references/artifact-contract.md",
    ],
    "pola-architecture-doc-writer": ["references/doc-templates.md"],
    "pola-code-review-gate": ["references/review-rubric.md"],
}

ARTIFACT_TERMS = {
    "pola-project-context-reader": "project-context",
    "pola-requirement-analyzer": "requirement",
    "pola-architecture-doc-writer": "architecture-plan",
    "pola-implementation-runner": "implementation",
    "pola-code-review-gate": "review",
    "pola-test-gate": "test-evidence",
    "pola-integration-regression-gate": "regression-evidence",
    "pola-deploy-release-gate": "release-plan",
    "pola-devlog-git-finalizer": "finalization",
}


@dataclass
class Finding:
    severity: str
    path: Path
    message: str


def rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def parse_frontmatter(text: str) -> dict[str, str]:
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return {}
    data: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data


def section_present(text: str, section: str) -> bool:
    return re.search(rf"^##\s+{re.escape(section)}\s*$", text, re.M) is not None


def validate_skill(skill: str) -> list[Finding]:
    findings: list[Finding] = []
    skill_dir = ROOT / skill
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [Finding("FAIL", skill_md, "missing SKILL.md")]

    text = read(skill_md)
    fm = parse_frontmatter(text)
    if fm.get("name") != skill:
        findings.append(Finding("FAIL", skill_md, f"frontmatter name must be {skill!r}"))
    desc = fm.get("description", "")
    if not desc:
        findings.append(Finding("FAIL", skill_md, "missing description"))
    if len(desc) > 1024:
        findings.append(Finding("FAIL", skill_md, "description exceeds 1024 characters"))

    for section in REQUIRED_SECTIONS.get(skill, []):
        if not section_present(text, section):
            findings.append(Finding("FAIL", skill_md, f"missing section: {section}"))

    if len(text.splitlines()) < 70 and skill != "pola-agent-delivery-framework":
        findings.append(Finding("WARN", skill_md, "skill body may be too thin for a workflow skill"))

    for required in REQUIRED_REFERENCES.get(skill, []):
        ref_path = skill_dir / required
        if not ref_path.exists():
            findings.append(Finding("FAIL", ref_path, "missing referenced resource"))
        elif required not in text:
            findings.append(Finding("WARN", skill_md, f"does not mention {required}"))

    artifact = ARTIFACT_TERMS.get(skill)
    if artifact and artifact not in text:
        findings.append(Finding("WARN", skill_md, f"does not explicitly mention artifact: {artifact}"))

    return findings


def validate_scripts() -> list[Finding]:
    findings: list[Finding] = []
    scripts: list[Path] = []
    for skill in SKILLS:
        scripts.extend((ROOT / skill / "scripts").glob("*"))
    for script in scripts:
        if not script.is_file():
            continue
        mode = script.stat().st_mode
        if not (mode & stat.S_IXUSR):
            findings.append(Finding("FAIL", script, "script is not executable"))
        if script.suffix == ".sh":
            proc = subprocess.run(["bash", "-n", str(script)], cwd=ROOT)
            if proc.returncode != 0:
                findings.append(Finding("FAIL", script, "bash syntax check failed"))
        if script.suffix == ".py":
            proc = subprocess.run([sys.executable, "-m", "py_compile", str(script)], cwd=ROOT)
            if proc.returncode != 0:
                findings.append(Finding("FAIL", script, "python syntax check failed"))
    return findings


def validate_references() -> list[Finding]:
    findings: list[Finding] = []
    required_phrases = {
        ROOT / "pola-agent-delivery-framework/references/artifact-contract.md": [
            "artifact: project-context",
            "artifact: requirement",
            "artifact: architecture-plan",
            "artifact: implementation",
            "artifact: review",
            "artifact: test-evidence",
            "artifact: regression-evidence",
            "artifact: release-plan",
            "artifact: finalization",
        ],
        ROOT / "pola-agent-delivery-framework/references/workflow-gates.md": [
            "Phase 0",
            "Phase 1",
            "Phase 2",
            "Phase 3",
            "Phase 4",
            "Phase 5",
            "Phase 6",
            "Phase 7",
        ],
        ROOT / "pola-architecture-doc-writer/references/doc-templates.md": [
            "轻量需求开发方案",
            "ADR 模板",
            "测试计划模板",
        ],
        ROOT / "pola-code-review-gate/references/review-rubric.md": [
            "正确性",
            "安全",
            "可维护性",
            "测试",
            "发布",
        ],
    }
    for path, phrases in required_phrases.items():
        if not path.exists():
            findings.append(Finding("FAIL", path, "missing reference file"))
            continue
        text = read(path)
        for phrase in phrases:
            if phrase not in text:
                findings.append(Finding("FAIL", path, f"missing phrase: {phrase}"))
    return findings


def validate_plan() -> list[Finding]:
    findings: list[Finding] = []
    plan = ROOT / "POLA_SKILL_DEVELOPMENT_PLAN.md"
    text = read(plan)
    for skill in SKILLS:
        if skill not in text:
            findings.append(Finding("WARN", plan, f"plan does not mention {skill}"))
    return findings


def main() -> int:
    findings: list[Finding] = []
    for skill in SKILLS:
        findings.extend(validate_skill(skill))
    findings.extend(validate_scripts())
    findings.extend(validate_references())
    findings.extend(validate_plan())

    fails = [f for f in findings if f.severity == "FAIL"]
    warns = [f for f in findings if f.severity == "WARN"]

    if not findings:
        print("PASS: Pola skill harness found no issues.")
        return 0

    for finding in findings:
        print(f"{finding.severity}: {rel(finding.path)}: {finding.message}")

    print(f"\nSummary: {len(fails)} fail(s), {len(warns)} warning(s)")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())

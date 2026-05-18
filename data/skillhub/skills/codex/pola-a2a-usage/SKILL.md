---
name: pola-a2a-usage
description: Pola A2A skill framework usage guide. Use when the user asks how to use the installed Pola skills, A2A delivery workflow, end-to-end software delivery from requirement to git/deploy, or which pola-* skill to call for a project.
---

# Pola A2A Usage

Use `pola-agent-delivery-framework` as the main entrypoint for end-to-end delivery.

Installed skills:

- `pola-project-context-reader`
- `pola-requirement-analyzer`
- `pola-architecture-doc-writer`
- `pola-implementation-runner`
- `pola-code-review-gate`
- `pola-test-gate`
- `pola-integration-regression-gate`
- `pola-deploy-release-gate`
- `pola-devlog-git-finalizer`
- `pola-devlog-writer`

Usage document:

`~/.codex/skills/POLA_A2A_SKILL_USAGE.md`

Default prompt:

```text
Use pola-agent-delivery-framework to complete this project in A2A closed-loop mode: read project context, analyze requirements, write architecture plan, implement, review, test, validate integration/regression, prepare release, update devlog, and finish git handoff.
```

# PolaUUH Unified Identity Devlog

Date: 2026-06-06

## Goal

Promote the existing PolaZhenjing / AIPD account center into the shared PolaUUH identity layer and provide the first integration contract for PolaReference, PolaRead, and PolaDiting.

## Requirement / PRD / SDD

- Requirement: `docs/pola/project-knowledge/requirements/2026-06-06-polauuh-unified-identity-requirements.md`
- PRD / SPEC: `docs/pola/project-knowledge/specs/2026-06-06-polauuh-unified-identity-prd.md`
- SDD: `docs/pola/project-knowledge/architecture/2026-06-06-polauuh-unified-identity-sdd.md`

## Changes

- Extended the permission catalog with `polareference.use` and `poladiting.use`.
- Re-labeled account-center permissions from `AIPD` to `PolaUUH`.
- Kept the existing `/api/sso/check` endpoint compatible while returning `provider=PolaUUH` and the requested `app_id`.
- Added regression tests for PolaUUH permission catalog coverage.

## Verification

- `PYTHONPATH=. .venv/bin/python -m pytest tests/test_polauuh_auth.py`
- `/Users/wangchang/.agents/skills/pola-agent-delivery-framework/scripts/validate_pola_skills.py`

## Risk

- Runtime routes are still backward-compatible with current PolaZhenjing paths. Canonical `/PolaUUH` routing still needs deployment-layer aliasing before external clients can use only the new URL family.

## Commit

Pending cross-repository git handoff.

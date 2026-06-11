# Devlog: PolaUUH Permission Catalog Sync

Date: 2026-06-11

## Goal

Keep the legacy PolaZhenJing-hosted PolaUUH provider compatible with the new PolaLuna client while the standalone PolaUUH repository is being adopted.

## Changes

- Added `polaluna.use` to `app/auth.py` `PERMISSION_CATALOG`.
- Updated `tests/test_polauuh_auth.py` to assert the permission catalog covers PolaLuna.
- Updated the PolaUUH requirement, PRD/SPEC, and SDD with the 2026-06-11 all-Pola adoption matrix and the verified `/PolaUUH/admin/*` production paths.

## Verification

- `python -m pytest tests/test_polauuh_auth.py -q`: `2 passed`.
- Anonymous production smoke:
  - `GET https://aipd.me/PolaUUH/admin/login` -> 200
  - `GET https://aipd.me/PolaUUH/login` -> 404, confirming clients must use admin path
  - `POST https://aipd.me/PolaUUH/admin/api/sso/check` without cookie -> 401

## Risk

- This is an additive permission catalog change. Existing users and app permissions remain unchanged.
- Granting `polaluna.use` to non-admin users remains an admin action through the existing permission workflow.

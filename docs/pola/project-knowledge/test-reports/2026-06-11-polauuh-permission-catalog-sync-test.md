# Test Report: PolaUUH Permission Catalog Sync

Date: 2026-06-11

## Scope

Validate the provider-side permission catalog needed by the all-Pola PolaUUH rollout.

## Checks

- `python -m pytest tests/test_polauuh_auth.py -q`: `2 passed`.
- Production path smoke completed:
  - `curl -I -L https://aipd.me/PolaUUH/admin/login` returned `200 OK`.
  - `curl -I -L https://aipd.me/PolaUUH/login` returned `404 NOT FOUND`.
  - Anonymous `POST https://aipd.me/PolaUUH/admin/api/sso/check` returned `401`, expected without a session.
  - Anonymous `POST https://aipd.me/PolaUUH/api/sso/check` returned `404`, confirming the root API path is not the production default.

## Result

Passed. Production route evidence requires all clients to default to `/PolaUUH/admin/*`.

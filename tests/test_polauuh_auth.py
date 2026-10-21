from app.auth import DEFAULT_USER_PERMISSIONS, PERMISSION_CATALOG
from scripts.unified_auth_harness import preference_overlay_matches


def test_polauuh_permission_catalog_includes_initial_apps():
    assert PERMISSION_CATALOG["polareference.use"]["app"] == "PolaReference"
    assert PERMISSION_CATALOG["polaread.use"]["app"] == "PolaRead"
    assert PERMISSION_CATALOG["poladiting.use"]["app"] == "PolaDiting"
    assert PERMISSION_CATALOG["polaluna.use"]["app"] == "PolaLuna"
    assert PERMISSION_CATALOG["users.manage"]["app"] == "PolaUUH"


def test_polauuh_default_permissions_keep_existing_apps():
    assert "polaread.use" in DEFAULT_USER_PERMISSIONS
    assert "polanews.use" in DEFAULT_USER_PERMISSIONS


def test_unified_auth_harness_compares_current_preferences():
    expected = {"theme": "zhenjing", "font_family": "system"}

    assert preference_overlay_matches(
        {"data": {"theme": "zhenjing", "font_family": "system"}},
        expected,
    )
    assert not preference_overlay_matches(
        {"data": {"theme": "dream-gold", "font_family": "system"}},
        expected,
    )
    assert not preference_overlay_matches({"data": {}}, expected)

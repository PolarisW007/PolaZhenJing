from app.auth import DEFAULT_USER_PERMISSIONS, PERMISSION_CATALOG


def test_polauuh_permission_catalog_includes_initial_apps():
    assert PERMISSION_CATALOG["polareference.use"]["app"] == "PolaReference"
    assert PERMISSION_CATALOG["polaread.use"]["app"] == "PolaRead"
    assert PERMISSION_CATALOG["poladiting.use"]["app"] == "PolaDiting"
    assert PERMISSION_CATALOG["polaluna.use"]["app"] == "PolaLuna"
    assert PERMISSION_CATALOG["users.manage"]["app"] == "PolaUUH"


def test_polauuh_default_permissions_keep_existing_apps():
    assert "polaread.use" in DEFAULT_USER_PERMISSIONS
    assert "polanews.use" in DEFAULT_USER_PERMISSIONS

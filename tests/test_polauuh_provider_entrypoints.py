from app import create_app


PROVIDERS = {
    "wechat": "微信",
    "alipay": "支付宝",
    "google": "Google",
    "apple": "Apple",
    "huawei": "华为",
}


def _client():
    app = create_app()
    app.config.update(TESTING=True)
    return app.test_client()


def test_login_exposes_provider_entrypoints_with_next():
    response = _client().get(
        "/admin/login?next=%2FPolaRead%2Flogin%3Fsso%3D1%26next%3D%252F"
    )

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "快捷验证登录" in body
    for provider, label in PROVIDERS.items():
        assert label in body
        assert f"/admin/auth/{provider}/start" in body
    assert "next=/PolaRead/login?sso%3D1%26next%3D%252F" in body


def test_register_exposes_provider_entrypoints_with_next():
    response = _client().get(
        "/admin/register?next=%2FPolaRead%2Flogin%3Fsso%3D1%26next%3D%252F"
    )

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "快捷登录 / 注册" in body
    for provider, label in PROVIDERS.items():
        assert label in body
        assert f"/admin/auth/{provider}/start" in body
    assert "next=/PolaRead/login?sso%3D1%26next%3D%252F" in body


def test_provider_start_degrades_safely_without_secret_config():
    response = _client().get(
        "/admin/auth/wechat/start?next=%2FPolaRead%2Flogin%3Fsso%3D1",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/admin/login?next=/PolaRead/login?sso%3D1"
    )

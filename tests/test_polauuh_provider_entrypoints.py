from app import create_app


PROVIDERS = {
    "wechat": "微信",
    "alipay": "支付宝",
    "google": "Google",
    "apple": "Apple",
    "huawei": "华为",
}


def _client(tmp_path, *, configured=False):
    config = {
        "TESTING": True,
        "POLAUUH_DATABASE_PATH": str(tmp_path / "polauuh-entrypoints.db"),
        "POLAUUH_EMAIL_VERIFICATION_REQUIRED": False,
    }
    if configured:
        config.update(
            {
                "POLAUUH_GOOGLE_ENABLED": True,
                "POLAUUH_GOOGLE_CLIENT_ID": "google-client",
                "POLAUUH_GOOGLE_CLIENT_SECRET": "google-secret",
                "POLAUUH_APPLE_ENABLED": True,
                "POLAUUH_APPLE_CLIENT_ID": "apple-client",
                "POLAUUH_APPLE_TEAM_ID": "team",
                "POLAUUH_APPLE_KEY_ID": "key",
                "POLAUUH_APPLE_PRIVATE_KEY_PATH": "/tmp/apple-test-key.p8",
                "POLAUUH_WECHAT_ENABLED": True,
                "POLAUUH_WECHAT_APP_ID": "wechat-app",
                "POLAUUH_WECHAT_APP_SECRET": "wechat-secret",
                "POLAUUH_ALIPAY_ENABLED": True,
                "POLAUUH_ALIPAY_APP_ID": "alipay-app",
                "POLAUUH_ALIPAY_PRIVATE_KEY_PATH": "/tmp/alipay-private.pem",
                "POLAUUH_ALIPAY_PUBLIC_KEY_PATH": "/tmp/alipay-public.pem",
                "POLAUUH_HUAWEI_ENABLED": True,
                "POLAUUH_HUAWEI_CLIENT_ID": "huawei-client",
                "POLAUUH_HUAWEI_CLIENT_SECRET": "huawei-secret",
            }
        )
    return create_app(config).test_client()


def test_login_exposes_configured_provider_entrypoints_with_next(tmp_path):
    response = _client(tmp_path, configured=True).get(
        "/admin/login?next=%2FPolaRead%2Flogin%3Fsso%3D1%26next%3D%252F"
    )

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "第三方快捷登录" in body
    for provider, label in PROVIDERS.items():
        assert label in body
        assert f"/admin/auth/{provider}/start" in body
    assert "next=/PolaRead/login?sso%3D1%26next%3D%252F" in body


def test_register_exposes_provider_labels_but_disables_unconfigured_entries(tmp_path):
    response = _client(tmp_path).get("/admin/register")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "验证码登录 / 注册" in body
    for provider, label in PROVIDERS.items():
        assert label in body
        assert f"/admin/auth/{provider}/start" not in body
    assert body.count("平台参数待配置") == len(PROVIDERS)


def test_provider_start_degrades_safely_without_secret_config(tmp_path):
    response = _client(tmp_path).get(
        "/admin/auth/wechat/start?next=%2FPolaRead%2Flogin%3Fsso%3D1",
        follow_redirects=False,
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith(
        "/admin/login?next=/PolaRead/login?sso%3D1"
    )

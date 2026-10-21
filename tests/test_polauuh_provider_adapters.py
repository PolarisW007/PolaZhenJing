import base64
import json

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

from app import create_app
from app.identity.providers.base import (
    AlipayAdapter,
    AppleAdapter,
    GoogleAdapter,
    HuaweiAdapter,
    ProviderError,
    WeChatAdapter,
)


@pytest.fixture
def provider_app(tmp_path):
    return create_app(
        {
            "TESTING": True,
            "POLAUUH_DATABASE_PATH": str(tmp_path / "providers.db"),
            "POLAUUH_EMAIL_VERIFICATION_REQUIRED": False,
        }
    )


def test_google_exchange_maps_verified_oidc_claims(provider_app, monkeypatch):
    adapter = GoogleAdapter()
    provider_app.config.update(
        POLAUUH_GOOGLE_CLIENT_ID="google-client",
        POLAUUH_GOOGLE_CLIENT_SECRET="google-secret",
    )
    captured = {}
    monkeypatch.setattr(
        adapter,
        "_post_form",
        lambda url, data: captured.update(url=url, data=data) or {"id_token": "token"},
    )
    monkeypatch.setattr(
        adapter,
        "_verify_id_token",
        lambda token, audience, nonce=None: {
            "iss": "https://accounts.google.com",
            "sub": "google-sub",
            "email": "google@example.com",
            "email_verified": True,
            "name": "Google User",
            "picture": "https://example.com/google.png",
        },
    )

    with provider_app.app_context():
        identity = adapter.exchange_callback({"code": "code"}, "https://aipd.me/callback", nonce="nonce")

    assert captured["data"]["client_secret"] == "google-secret"
    assert identity.subject == "google-sub"
    assert identity.email_verified is True


def test_apple_exchange_uses_client_secret_and_first_returned_name(provider_app, monkeypatch):
    adapter = AppleAdapter()
    provider_app.config.update(
        POLAUUH_APPLE_CLIENT_ID="apple-service-id",
        POLAUUH_APPLE_TEAM_ID="team",
        POLAUUH_APPLE_KEY_ID="key",
        POLAUUH_APPLE_PRIVATE_KEY_PATH="/tmp/not-used.p8",
    )
    monkeypatch.setattr(adapter, "_client_secret", lambda config: "client-secret")
    monkeypatch.setattr(adapter, "_post_form", lambda url, data: {"id_token": "token"})
    monkeypatch.setattr(
        adapter,
        "_verify_id_token",
        lambda token, audience, nonce=None: {
            "sub": "apple-sub",
            "email": "relay@example.com",
            "email_verified": "true",
            "is_private_email": "true",
        },
    )

    with provider_app.app_context():
        identity = adapter.exchange_callback(
            {
                "code": "code",
                "user": json.dumps({"name": {"firstName": "Ada", "lastName": "Lovelace"}}),
            },
            "https://aipd.me/callback",
            nonce="nonce",
        )

    assert identity.display_name == "Ada Lovelace"
    assert identity.email_verified is True


def test_wechat_exchange_maps_openid_unionid_and_profile(provider_app, monkeypatch):
    adapter = WeChatAdapter()
    provider_app.config.update(
        POLAUUH_WECHAT_APP_ID="wechat-app",
        POLAUUH_WECHAT_APP_SECRET="wechat-secret",
    )

    def fake_get(url, params=None):
        if "access_token" in url:
            return {"access_token": "token", "openid": "openid-1", "unionid": "union-1"}
        return {
            "openid": "openid-1",
            "unionid": "union-1",
            "nickname": "微信用户",
            "headimgurl": "https://example.com/wx.png",
        }

    monkeypatch.setattr(adapter, "_get_json", fake_get)
    with provider_app.app_context():
        identity = adapter.exchange_callback({"code": "code"}, "https://aipd.me/callback")

    assert identity.subject == "openid-1"
    assert identity.union_id == "union-1"
    assert identity.display_name == "微信用户"


def test_huawei_exchange_maps_oidc_claims(provider_app, monkeypatch):
    adapter = HuaweiAdapter()
    provider_app.config.update(
        POLAUUH_HUAWEI_CLIENT_ID="huawei-client",
        POLAUUH_HUAWEI_CLIENT_SECRET="huawei-secret",
    )
    monkeypatch.setattr(adapter, "_post_form", lambda url, data: {"id_token": "token"})
    monkeypatch.setattr(
        adapter,
        "_verify_id_token",
        lambda token, audience, nonce=None: {
            "sub": "huawei-sub",
            "email": "huawei@example.com",
            "email_verified": True,
            "name": "Huawei User",
        },
    )

    with provider_app.app_context():
        identity = adapter.exchange_callback({"code": "code"}, "https://aipd.me/callback", nonce="nonce")

    assert identity.subject == "huawei-sub"
    assert identity.email == "huawei@example.com"


def test_alipay_gateway_verifies_exact_raw_response_signature(provider_app, tmp_path, monkeypatch):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key_path = tmp_path / "alipay-public.pem"
    public_key_path.write_bytes(
        private_key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    adapter = AlipayAdapter()
    provider_app.config.update(
        POLAUUH_ALIPAY_APP_ID="alipay-app",
        POLAUUH_ALIPAY_PRIVATE_KEY_PATH=str(tmp_path / "unused-private.pem"),
        POLAUUH_ALIPAY_PUBLIC_KEY_PATH=str(public_key_path),
    )
    response_text = '{"code":"10000","user_id":"2088","msg":"Success"}'
    signature = base64.b64encode(
        private_key.sign(response_text.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256())
    ).decode("ascii")
    raw = '{"alipay_system_oauth_token_response":' + response_text + ',"sign":' + json.dumps(signature) + '}'
    payload = json.loads(raw)
    monkeypatch.setattr(adapter, "_sign", lambda config, params: "request-signature")
    monkeypatch.setattr(adapter, "_post_form_raw", lambda url, data: (payload, raw))

    with provider_app.app_context():
        result = adapter._gateway_call(
            provider_app.config,
            "alipay.system.oauth.token",
            {"grant_type": "authorization_code", "code": "code"},
        )

    assert result["alipay_system_oauth_token_response"]["user_id"] == "2088"


def test_alipay_gateway_rejects_invalid_response_signature(provider_app, tmp_path, monkeypatch):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key_path = tmp_path / "alipay-public.pem"
    public_key_path.write_bytes(
        private_key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    adapter = AlipayAdapter()
    provider_app.config.update(
        POLAUUH_ALIPAY_APP_ID="alipay-app",
        POLAUUH_ALIPAY_PRIVATE_KEY_PATH=str(tmp_path / "unused-private.pem"),
        POLAUUH_ALIPAY_PUBLIC_KEY_PATH=str(public_key_path),
    )
    raw = '{"alipay_system_oauth_token_response":{"code":"10000"},"sign":"aW52YWxpZA=="}'
    monkeypatch.setattr(adapter, "_sign", lambda config, params: "request-signature")
    monkeypatch.setattr(adapter, "_post_form_raw", lambda url, data: (json.loads(raw), raw))

    with provider_app.app_context(), pytest.raises(ProviderError) as error:
        adapter._gateway_call(provider_app.config, "alipay.system.oauth.token", {})

    assert error.value.code == "provider_callback_invalid"

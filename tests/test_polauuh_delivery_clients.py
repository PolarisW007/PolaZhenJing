from urllib.parse import parse_qs

from app.mailer import _aliyun_dm_params, _send_aliyun_direct_mail
from app.sms import _aliyun_sms_params, _send_aliyun_sms


def _aliyun_env(monkeypatch):
    monkeypatch.setenv("POLAUUH_ALIYUN_ACCESS_KEY_ID", "test-key-id")
    monkeypatch.setenv("POLAUUH_ALIYUN_ACCESS_KEY_SECRET", "test-key-secret")


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self, _limit=None):
        return self.payload


def test_aliyun_direct_mail_signature_does_not_expose_secret(monkeypatch):
    _aliyun_env(monkeypatch)
    monkeypatch.setenv("POLAUUH_ALIYUN_DM_ACCOUNT_NAME", "noreply@example.com")

    params = _aliyun_dm_params("demo@example.com", "123456")

    assert params["Action"] == "SingleSendMail"
    assert params["ToAddress"] == "demo@example.com"
    assert params["Signature"]
    assert "test-key-secret" not in str(params)


def test_aliyun_direct_mail_posts_expected_form(monkeypatch):
    _aliyun_env(monkeypatch)
    monkeypatch.setenv("POLAUUH_ALIYUN_DM_ACCOUNT_NAME", "noreply@example.com")
    captured = {}

    def fake_urlopen(request, timeout=10):
        captured["url"] = request.full_url
        captured["body"] = parse_qs(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return FakeResponse(b'{"RequestId":"request-id"}')

    monkeypatch.setattr("app.mailer.urlopen", fake_urlopen)
    assert _send_aliyun_direct_mail("demo@example.com", "123456") is True
    assert captured["url"] == "https://dm.aliyuncs.com/"
    assert captured["body"]["Action"] == ["SingleSendMail"]
    assert captured["timeout"] == 10


def test_aliyun_sms_signature_normalizes_mainland_phone(monkeypatch):
    _aliyun_env(monkeypatch)
    monkeypatch.setenv("POLAUUH_ALIYUN_SMS_SIGN_NAME", "Pola")
    monkeypatch.setenv("POLAUUH_ALIYUN_SMS_TEMPLATE_CODE", "SMS_123")

    params = _aliyun_sms_params("+8613800138000", "654321")

    assert params["Action"] == "SendSms"
    assert params["PhoneNumbers"] == "13800138000"
    assert params["TemplateParam"] == '{"code":"654321"}'
    assert params["Signature"]
    assert "test-key-secret" not in str(params)


def test_aliyun_sms_requires_ok_response(monkeypatch):
    _aliyun_env(monkeypatch)
    monkeypatch.setenv("POLAUUH_ALIYUN_SMS_SIGN_NAME", "Pola")
    monkeypatch.setenv("POLAUUH_ALIYUN_SMS_TEMPLATE_CODE", "SMS_123")
    monkeypatch.setattr(
        "app.sms.urlopen",
        lambda request, timeout=10: FakeResponse(b'{"Code":"OK","RequestId":"request-id"}'),
    )

    assert _send_aliyun_sms("+8613800138000", "654321") is True

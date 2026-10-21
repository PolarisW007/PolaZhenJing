import base64
import hashlib
import hmac
import json
import logging
import os
import smtplib
import time
import uuid
from email.message import EmailMessage
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from flask import current_app


LOGGER = logging.getLogger(__name__)
ALIYUN_DM_ENDPOINT = "https://dm.aliyuncs.com/"


def _percent_encode(value: str) -> str:
    return quote(str(value), safe="").replace("+", "%20").replace("*", "%2A").replace("%7E", "~")


def _aliyun_signature(params: dict, access_key_secret: str) -> str:
    canonicalized = "&".join(
        f"{_percent_encode(key)}={_percent_encode(params[key])}" for key in sorted(params)
    )
    string_to_sign = f"POST&%2F&{_percent_encode(canonicalized)}"
    digest = hmac.new(
        f"{access_key_secret}&".encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha1,
    ).digest()
    return base64.b64encode(digest).decode("ascii")


def _aliyun_dm_params(email: str, code: str) -> dict | None:
    access_key_id = os.getenv("POLAUUH_ALIYUN_ACCESS_KEY_ID", "")
    access_key_secret = os.getenv("POLAUUH_ALIYUN_ACCESS_KEY_SECRET", "")
    account_name = os.getenv("POLAUUH_ALIYUN_DM_ACCOUNT_NAME", "")
    from_alias = os.getenv("POLAUUH_ALIYUN_DM_FROM_ALIAS", "PolaUUH")
    if not all([access_key_id, access_key_secret, account_name]):
        LOGGER.warning("Aliyun DirectMail configuration is incomplete.")
        return None
    params = {
        "Action": "SingleSendMail",
        "AccountName": account_name,
        "AddressType": "1",
        "Format": "JSON",
        "FromAlias": from_alias,
        "HtmlBody": f"<p>您的 PolaUUH 验证码是：<strong>{code}</strong>，5 分钟内有效。</p>",
        "ReplyToAddress": "true",
        "SignatureMethod": "HMAC-SHA1",
        "SignatureNonce": str(uuid.uuid4()),
        "SignatureVersion": "1.0",
        "Subject": "PolaUUH 邮箱验证码",
        "TagName": os.getenv("POLAUUH_ALIYUN_DM_TAG_NAME", ""),
        "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ToAddress": email,
        "Version": "2015-11-23",
    }
    params = {key: value for key, value in params.items() if value != ""}
    params["AccessKeyId"] = access_key_id
    params["Signature"] = _aliyun_signature(params, access_key_secret)
    return params


def _send_aliyun_direct_mail(email: str, code: str) -> bool:
    params = _aliyun_dm_params(email, code)
    if params is None:
        return False
    request = Request(
        ALIYUN_DM_ENDPOINT,
        data=urlencode(params).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read(1024 * 1024).decode("utf-8") or "{}")
    except (HTTPError, URLError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        LOGGER.warning("Aliyun DirectMail request failed: %s", type(exc).__name__)
        return False
    if payload.get("Code"):
        LOGGER.warning("Aliyun DirectMail rejected the verification message: %s", payload.get("Code"))
        return False
    return True


def _send_smtp(email: str, code: str, *, legacy_qq: bool = False) -> bool:
    if legacy_qq:
        host = "smtp.qq.com"
        port = 465
        username = os.getenv("QQ_EMAIL", "")
        password = os.getenv("QQ_EMAIL_AUTH_CODE", "")
        sender = username
    else:
        host = os.getenv("POLAUUH_SMTP_HOST", "")
        port = int(os.getenv("POLAUUH_SMTP_PORT", "465"))
        username = os.getenv("POLAUUH_SMTP_USERNAME", "")
        password = os.getenv("POLAUUH_SMTP_PASSWORD", "")
        sender = os.getenv("POLAUUH_SMTP_FROM", username)
    if not all([host, username, password, sender]):
        LOGGER.warning("SMTP configuration is incomplete.")
        return False

    message = EmailMessage()
    message["Subject"] = "PolaUUH 邮箱验证码"
    message["From"] = sender
    message["To"] = email
    message.set_content(f"您的 PolaUUH 验证码是：{code}，5 分钟内有效。")
    try:
        with smtplib.SMTP_SSL(host, port, timeout=10) as server:
            server.login(username, password)
            server.send_message(message)
        return True
    except (OSError, smtplib.SMTPException) as exc:
        LOGGER.warning("Verification email delivery failed: %s", type(exc).__name__)
        return False


def send_verification_code(email: str, code: str) -> bool:
    """Send a verification code without logging its target or value."""

    if not current_app.config.get("POLAUUH_MAIL_ENABLED"):
        LOGGER.info("Mail delivery is disabled.")
        return False
    provider = os.getenv("POLAUUH_MAIL_PROVIDER", "").strip().lower()
    if not provider:
        provider = "qq" if os.getenv("QQ_EMAIL") and os.getenv("QQ_EMAIL_AUTH_CODE") else "smtp"
    if provider == "aliyun_dm":
        return _send_aliyun_direct_mail(email, code)
    if provider == "qq":
        return _send_smtp(email, code, legacy_qq=True)
    if provider == "smtp":
        return _send_smtp(email, code)
    LOGGER.warning("Unsupported mail provider: %s", provider)
    return False

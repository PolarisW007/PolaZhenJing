import base64
import hashlib
import hmac
import json
import logging
import os
import time
import uuid
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from flask import current_app


LOGGER = logging.getLogger(__name__)
ALIYUN_DYSMS_ENDPOINT = "https://dysmsapi.aliyuncs.com/"


def _percent_encode(value: str) -> str:
    return quote(str(value), safe="").replace("+", "%20").replace("*", "%2A").replace("%7E", "~")


def _signature(params: dict, secret: str) -> str:
    canonicalized = "&".join(
        f"{_percent_encode(key)}={_percent_encode(params[key])}" for key in sorted(params)
    )
    string_to_sign = f"POST&%2F&{_percent_encode(canonicalized)}"
    digest = hmac.new(
        f"{secret}&".encode("utf-8"),
        string_to_sign.encode("utf-8"),
        hashlib.sha1,
    ).digest()
    return base64.b64encode(digest).decode("ascii")


def _aliyun_sms_params(phone: str, code: str) -> dict | None:
    access_key_id = os.getenv("POLAUUH_ALIYUN_ACCESS_KEY_ID", "")
    access_key_secret = os.getenv("POLAUUH_ALIYUN_ACCESS_KEY_SECRET", "")
    sign_name = os.getenv("POLAUUH_ALIYUN_SMS_SIGN_NAME", "")
    template_code = os.getenv("POLAUUH_ALIYUN_SMS_TEMPLATE_CODE", "")
    if not all([access_key_id, access_key_secret, sign_name, template_code]):
        LOGGER.warning("Aliyun SMS configuration is incomplete.")
        return None
    normalized_phone = phone[3:] if phone.startswith("+86") else phone.lstrip("+")
    params = {
        "AccessKeyId": access_key_id,
        "Action": "SendSms",
        "Format": "JSON",
        "PhoneNumbers": normalized_phone,
        "RegionId": os.getenv("POLAUUH_ALIYUN_SMS_REGION", "cn-hangzhou"),
        "SignName": sign_name,
        "SignatureMethod": "HMAC-SHA1",
        "SignatureNonce": str(uuid.uuid4()),
        "SignatureVersion": "1.0",
        "TemplateCode": template_code,
        "TemplateParam": json.dumps({"code": code}, ensure_ascii=False, separators=(",", ":")),
        "Timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "Version": "2017-05-25",
    }
    params["Signature"] = _signature(params, access_key_secret)
    return params


def _send_aliyun_sms(phone: str, code: str) -> bool:
    params = _aliyun_sms_params(phone, code)
    if params is None:
        return False
    request = Request(
        ALIYUN_DYSMS_ENDPOINT,
        data=urlencode(params).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urlopen(request, timeout=10) as response:
            payload = json.loads(response.read(1024 * 1024).decode("utf-8") or "{}")
    except (HTTPError, URLError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        LOGGER.warning("Aliyun SMS request failed: %s", type(exc).__name__)
        return False
    if payload.get("Code") != "OK":
        LOGGER.warning("Aliyun SMS rejected the verification message: %s", payload.get("Code", "unknown"))
        return False
    return True


def send_sms_verification_code(phone: str, code: str) -> bool:
    if not current_app.config.get("POLAUUH_SMS_ENABLED"):
        LOGGER.info("SMS delivery is disabled.")
        return False
    provider = os.getenv("POLAUUH_SMS_PROVIDER", "aliyun_dysms").strip().lower()
    if provider == "aliyun_dysms":
        return _send_aliyun_sms(phone, code)
    LOGGER.warning("Unsupported SMS provider: %s", provider)
    return False

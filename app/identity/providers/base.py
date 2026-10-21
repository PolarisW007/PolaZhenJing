import json
import time
import base64
import binascii
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import jwt
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import padding


@dataclass(frozen=True)
class ProviderIdentity:
    provider: str
    subject: str
    union_id: str | None = None
    email: str | None = None
    email_verified: bool = False
    phone: str | None = None
    display_name: str | None = None
    avatar_url: str | None = None
    raw_profile: dict | None = None


class ProviderError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


class ProviderAdapter:
    provider = ""
    first_batch = False
    authorize_url = ""
    scope = ""
    client_id_key = ""
    client_secret_key = ""
    redirect_uri_key = ""
    token_url = ""
    jwks_url = ""
    issuer = ""
    required_config_keys: tuple[str, ...] = ()
    allowed_id_token_algorithms: tuple[str, ...] = ("RS256",)

    def is_enabled(self, config) -> bool:
        return bool(config.get(f"POLAUUH_{self.provider.upper()}_ENABLED"))

    def is_configured(self, config) -> bool:
        return all(str(config.get(key) or "").strip() for key in self.required_config_keys)

    def client_id(self, config) -> str:
        return str(config.get(self.client_id_key) or "")

    def client_secret(self, config) -> str:
        return str(config.get(self.client_secret_key) or "")

    def configured_redirect_uri(self, config, fallback: str) -> str:
        return str(config.get(self.redirect_uri_key) or "") or fallback

    def build_authorization_url(self, config, state: str, nonce: str, redirect_uri: str, next_url: str) -> str:
        client_id = self.client_id(config)
        redirect_uri = self.configured_redirect_uri(config, redirect_uri)
        if not self.is_configured(config) or not client_id or not self.authorize_url:
            raise ProviderError("provider_not_configured", "第三方登录尚未配置。")
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": self.scope,
            "state": state,
        }
        if nonce:
            params["nonce"] = nonce
        return f"{self.authorize_url}?{urlencode(params)}"

    def exchange_callback(self, request_args: dict, redirect_uri: str, nonce: str | None = None) -> ProviderIdentity:
        raise ProviderError("provider_callback_invalid", "当前 provider 需要真实平台回调配置。")

    def _post_form_raw(self, url: str, data: dict) -> tuple[dict, str]:
        encoded = urlencode(data).encode("utf-8")
        request = Request(
            url,
            data=encoded,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "PolaUUH/1.0",
            },
        )
        try:
            with urlopen(request, timeout=10) as response:
                raw = response.read(1024 * 1024).decode("utf-8")
                payload = json.loads(raw)
        except (HTTPError, URLError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProviderError("provider_network_error", "第三方登录服务暂时不可用。") from exc
        if not isinstance(payload, dict):
            raise ProviderError("provider_callback_invalid", "第三方返回格式无效。")
        return payload, raw

    def _post_form(self, url: str, data: dict) -> dict:
        payload, _raw = self._post_form_raw(url, data)
        return payload

    def _get_json(self, url: str, params: dict | None = None) -> dict:
        full_url = f"{url}?{urlencode(params)}" if params else url
        try:
            with urlopen(full_url, timeout=10) as response:
                payload = json.loads(response.read(1024 * 1024).decode("utf-8"))
        except (HTTPError, URLError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProviderError("provider_network_error", "第三方登录服务暂时不可用。") from exc
        if not isinstance(payload, dict):
            raise ProviderError("provider_callback_invalid", "第三方返回格式无效。")
        return payload

    def _verify_id_token(self, id_token: str, audience: str, nonce: str | None = None) -> dict:
        if not id_token:
            raise ProviderError("provider_callback_invalid", "第三方身份令牌为空。")
        try:
            key = jwt.PyJWKClient(self.jwks_url).get_signing_key_from_jwt(id_token).key
            claims = jwt.decode(
                id_token,
                key=key,
                algorithms=list(self.allowed_id_token_algorithms),
                audience=audience,
                issuer=self.issuer,
            )
        except (jwt.PyJWTError, ValueError) as exc:
            raise ProviderError("provider_callback_invalid", "第三方身份令牌校验失败。") from exc
        if nonce and claims.get("nonce") != nonce:
            raise ProviderError("provider_callback_invalid", "第三方登录 nonce 校验失败。")
        return claims


class GoogleAdapter(ProviderAdapter):
    provider = "google"
    first_batch = True
    authorize_url = "https://accounts.google.com/o/oauth2/v2/auth"
    scope = "openid email profile"
    client_id_key = "POLAUUH_GOOGLE_CLIENT_ID"
    client_secret_key = "POLAUUH_GOOGLE_CLIENT_SECRET"
    redirect_uri_key = "POLAUUH_GOOGLE_REDIRECT_URI"
    token_url = "https://oauth2.googleapis.com/token"
    jwks_url = "https://www.googleapis.com/oauth2/v3/certs"
    issuer = ("accounts.google.com", "https://accounts.google.com")
    required_config_keys = (
        "POLAUUH_GOOGLE_CLIENT_ID",
        "POLAUUH_GOOGLE_CLIENT_SECRET",
    )

    def exchange_callback(self, request_args: dict, redirect_uri: str, nonce: str | None = None) -> ProviderIdentity:
        from flask import current_app

        code = (request_args.get("code") or "").strip()
        if not code:
            raise ProviderError("provider_callback_invalid", "缺少 Google 授权码。")
        redirect_uri = self.configured_redirect_uri(current_app.config, redirect_uri)
        token = self._post_form(
            self.token_url,
            {
                "code": code,
                "client_id": self.client_id(current_app.config),
                "client_secret": self.client_secret(current_app.config),
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if "error" in token:
            raise ProviderError("provider_callback_invalid", str(token.get("error_description") or token["error"]))
        claims = self._verify_id_token(token.get("id_token", ""), self.client_id(current_app.config), nonce)
        return ProviderIdentity(
            provider=self.provider,
            subject=str(claims.get("sub") or ""),
            email=claims.get("email"),
            email_verified=bool(claims.get("email_verified")),
            display_name=claims.get("name"),
            avatar_url=claims.get("picture"),
            raw_profile={
                "iss": claims.get("iss"),
                "email_verified": claims.get("email_verified"),
                "locale": claims.get("locale"),
            },
        )


class AppleAdapter(ProviderAdapter):
    provider = "apple"
    first_batch = True
    authorize_url = "https://appleid.apple.com/auth/authorize"
    scope = "name email"
    client_id_key = "POLAUUH_APPLE_CLIENT_ID"
    redirect_uri_key = "POLAUUH_APPLE_REDIRECT_URI"
    token_url = "https://appleid.apple.com/auth/token"
    jwks_url = "https://appleid.apple.com/auth/keys"
    issuer = "https://appleid.apple.com"
    required_config_keys = (
        "POLAUUH_APPLE_CLIENT_ID",
        "POLAUUH_APPLE_TEAM_ID",
        "POLAUUH_APPLE_KEY_ID",
        "POLAUUH_APPLE_PRIVATE_KEY_PATH",
    )

    def build_authorization_url(self, config, state: str, nonce: str, redirect_uri: str, next_url: str) -> str:
        url = super().build_authorization_url(config, state, nonce, redirect_uri, next_url)
        return f"{url}&response_mode=form_post"

    def _client_secret(self, config) -> str:
        team_id = str(config.get("POLAUUH_APPLE_TEAM_ID") or "")
        key_id = str(config.get("POLAUUH_APPLE_KEY_ID") or "")
        key_path = str(config.get("POLAUUH_APPLE_PRIVATE_KEY_PATH") or "")
        client_id = self.client_id(config)
        if not all([team_id, key_id, key_path, client_id]):
            raise ProviderError("provider_not_configured", "Apple 登录缺少 Team ID、Key ID、Service ID 或私钥路径。")
        try:
            private_key = Path(key_path).read_text(encoding="utf-8")
        except OSError as exc:
            raise ProviderError("provider_not_configured", "Apple 登录私钥不可读取。") from exc
        now = int(time.time())
        try:
            return jwt.encode(
                {
                    "iss": team_id,
                    "iat": now,
                    "exp": now + 3600,
                    "aud": self.issuer,
                    "sub": client_id,
                },
                private_key,
                algorithm="ES256",
                headers={"kid": key_id},
            )
        except (jwt.PyJWTError, ValueError) as exc:
            raise ProviderError("provider_not_configured", "Apple 登录私钥无效。") from exc

    def exchange_callback(self, request_args: dict, redirect_uri: str, nonce: str | None = None) -> ProviderIdentity:
        from flask import current_app

        code = (request_args.get("code") or "").strip()
        if not code:
            raise ProviderError("provider_callback_invalid", "缺少 Apple 授权码。")
        redirect_uri = self.configured_redirect_uri(current_app.config, redirect_uri)
        token = self._post_form(
            self.token_url,
            {
                "code": code,
                "client_id": self.client_id(current_app.config),
                "client_secret": self._client_secret(current_app.config),
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if "error" in token:
            raise ProviderError("provider_callback_invalid", str(token.get("error_description") or token["error"]))
        claims = self._verify_id_token(token.get("id_token", ""), self.client_id(current_app.config), nonce)
        name = None
        if request_args.get("user"):
            try:
                user_info = json.loads(request_args.get("user") or "{}")
                name_info = user_info.get("name") or {}
                name = " ".join(part for part in [name_info.get("firstName"), name_info.get("lastName")] if part)
            except json.JSONDecodeError:
                name = None
        return ProviderIdentity(
            provider=self.provider,
            subject=str(claims.get("sub") or ""),
            email=claims.get("email"),
            email_verified=str(claims.get("email_verified")).lower() in {"true", "1"},
            display_name=name,
            raw_profile={
                "iss": claims.get("iss"),
                "email_verified": claims.get("email_verified"),
                "is_private_email": claims.get("is_private_email"),
            },
        )


class WeChatAdapter(ProviderAdapter):
    provider = "wechat"
    first_batch = True
    authorize_url = "https://open.weixin.qq.com/connect/qrconnect"
    scope = "snsapi_login"
    client_id_key = "POLAUUH_WECHAT_APP_ID"
    client_secret_key = "POLAUUH_WECHAT_APP_SECRET"
    redirect_uri_key = "POLAUUH_WECHAT_REDIRECT_URI"
    token_url = "https://api.weixin.qq.com/sns/oauth2/access_token"
    userinfo_url = "https://api.weixin.qq.com/sns/userinfo"
    required_config_keys = (
        "POLAUUH_WECHAT_APP_ID",
        "POLAUUH_WECHAT_APP_SECRET",
    )

    def build_authorization_url(self, config, state: str, nonce: str, redirect_uri: str, next_url: str) -> str:
        app_id = self.client_id(config)
        redirect_uri = self.configured_redirect_uri(config, redirect_uri)
        if not self.is_configured(config) or not app_id:
            raise ProviderError("provider_not_configured", "微信登录尚未配置。")
        params = {
            "appid": app_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": self.scope,
            "state": state,
        }
        return f"{self.authorize_url}?{urlencode(params)}#wechat_redirect"

    def exchange_callback(self, request_args: dict, redirect_uri: str, nonce: str | None = None) -> ProviderIdentity:
        from flask import current_app

        code = (request_args.get("code") or "").strip()
        if not code:
            raise ProviderError("provider_callback_invalid", "缺少微信授权码。")
        token = self._get_json(
            self.token_url,
            {
                "appid": self.client_id(current_app.config),
                "secret": self.client_secret(current_app.config),
                "code": code,
                "grant_type": "authorization_code",
            },
        )
        if token.get("errcode"):
            raise ProviderError("provider_callback_invalid", str(token.get("errmsg") or token["errcode"]))
        access_token = token.get("access_token")
        openid = token.get("openid")
        if not access_token or not openid:
            raise ProviderError("provider_callback_invalid", "微信 token 响应缺少 openid。")
        profile = self._get_json(
            self.userinfo_url,
            {"access_token": access_token, "openid": openid, "lang": "zh_CN"},
        )
        if profile.get("errcode"):
            raise ProviderError("provider_callback_invalid", str(profile.get("errmsg") or profile["errcode"]))
        return ProviderIdentity(
            provider=self.provider,
            subject=str(openid),
            union_id=profile.get("unionid") or token.get("unionid"),
            display_name=profile.get("nickname"),
            avatar_url=profile.get("headimgurl"),
            raw_profile={
                "openid": openid,
                "unionid_present": bool(profile.get("unionid") or token.get("unionid")),
                "country": profile.get("country"),
                "province": profile.get("province"),
                "city": profile.get("city"),
            },
        )


class AlipayAdapter(ProviderAdapter):
    provider = "alipay"
    authorize_url = "https://openauth.alipay.com/oauth2/publicAppAuthorize.htm"
    scope = "auth_user"
    client_id_key = "POLAUUH_ALIPAY_APP_ID"
    redirect_uri_key = "POLAUUH_ALIPAY_REDIRECT_URI"
    gateway_url = "https://openapi.alipay.com/gateway.do"
    required_config_keys = (
        "POLAUUH_ALIPAY_APP_ID",
        "POLAUUH_ALIPAY_PRIVATE_KEY_PATH",
        "POLAUUH_ALIPAY_PUBLIC_KEY_PATH",
    )

    def build_authorization_url(self, config, state: str, nonce: str, redirect_uri: str, next_url: str) -> str:
        app_id = self.client_id(config)
        redirect_uri = self.configured_redirect_uri(config, redirect_uri)
        if not self.is_configured(config) or not app_id:
            raise ProviderError("provider_not_configured", "支付宝登录尚未配置。")
        params = {
            "app_id": app_id,
            "scope": self.scope,
            "redirect_uri": redirect_uri,
            "state": state,
        }
        return f"{self.authorize_url}?{urlencode(params)}"

    def _private_key(self, config):
        key_path = str(config.get("POLAUUH_ALIPAY_PRIVATE_KEY_PATH") or "")
        if not key_path:
            raise ProviderError("provider_not_configured", "支付宝登录缺少应用私钥路径。")
        try:
            return serialization.load_pem_private_key(Path(key_path).read_bytes(), password=None)
        except (OSError, ValueError, TypeError) as exc:
            raise ProviderError("provider_not_configured", "支付宝应用私钥不可读取或格式无效。") from exc

    def _public_key(self, config):
        key_path = str(config.get("POLAUUH_ALIPAY_PUBLIC_KEY_PATH") or "")
        if not key_path:
            raise ProviderError("provider_not_configured", "支付宝登录缺少支付宝公钥路径。")
        try:
            return serialization.load_pem_public_key(Path(key_path).read_bytes())
        except (OSError, ValueError, TypeError) as exc:
            raise ProviderError("provider_not_configured", "支付宝公钥不可读取或格式无效。") from exc

    def _sign(self, config, params: dict) -> str:
        sign_text = "&".join(f"{key}={params[key]}" for key in sorted(params) if params[key] not in {None, ""})
        signature = self._private_key(config).sign(sign_text.encode("utf-8"), padding.PKCS1v15(), hashes.SHA256())
        import base64

        return base64.b64encode(signature).decode("ascii")

    def _gateway_call(self, config, method: str, extra: dict, auth_token: str | None = None) -> dict:
        params = {
            "app_id": self.client_id(config),
            "method": method,
            "format": "JSON",
            "charset": "utf-8",
            "sign_type": "RSA2",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": "1.0",
        }
        if auth_token:
            params["auth_token"] = auth_token
        params.update(extra)
        params["sign"] = self._sign(config, params)
        payload, raw = self._post_form_raw(self.gateway_url, params)
        response_key = f"{method.replace('.', '_')}_response"
        response = payload.get(response_key)
        signature = payload.get("sign")
        if not isinstance(response, dict) or not signature:
            raise ProviderError("provider_callback_invalid", "支付宝返回缺少签名响应。")
        signed_content = self._signed_response_text(raw, response_key)
        try:
            self._public_key(config).verify(
                base64.b64decode(signature, validate=True),
                signed_content.encode("utf-8"),
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
        except (InvalidSignature, ValueError, TypeError, binascii.Error) as exc:
            raise ProviderError("provider_callback_invalid", "支付宝响应签名校验失败。") from exc
        return payload

    @staticmethod
    def _signed_response_text(raw: str, response_key: str) -> str:
        encoded_key = json.dumps(response_key, ensure_ascii=False)
        key_index = raw.find(encoded_key)
        if key_index < 0:
            raise ProviderError("provider_callback_invalid", "支付宝响应格式无效。")
        colon_index = raw.find(":", key_index + len(encoded_key))
        if colon_index < 0:
            raise ProviderError("provider_callback_invalid", "支付宝响应格式无效。")
        value_start = colon_index + 1
        while value_start < len(raw) and raw[value_start].isspace():
            value_start += 1
        try:
            _value, value_end = json.JSONDecoder().raw_decode(raw, value_start)
        except json.JSONDecodeError as exc:
            raise ProviderError("provider_callback_invalid", "支付宝响应格式无效。") from exc
        return raw[value_start:value_end]

    def exchange_callback(self, request_args: dict, redirect_uri: str, nonce: str | None = None) -> ProviderIdentity:
        from flask import current_app

        auth_code = (request_args.get("auth_code") or request_args.get("code") or "").strip()
        if not auth_code:
            raise ProviderError("provider_callback_invalid", "缺少支付宝授权码。")
        token_payload = self._gateway_call(
            current_app.config,
            "alipay.system.oauth.token",
            {"grant_type": "authorization_code", "code": auth_code},
        )
        token_response = token_payload.get("alipay_system_oauth_token_response") or {}
        if token_response.get("code") and token_response.get("code") != "10000":
            raise ProviderError("provider_callback_invalid", str(token_response.get("sub_msg") or token_response.get("msg")))
        access_token = token_response.get("access_token")
        user_id = token_response.get("user_id") or token_response.get("alipay_user_id")
        if not access_token or not user_id:
            raise ProviderError("provider_callback_invalid", "支付宝 token 响应缺少 user_id。")
        profile_payload = self._gateway_call(
            current_app.config,
            "alipay.user.info.share",
            {},
            auth_token=access_token,
        )
        profile = profile_payload.get("alipay_user_info_share_response") or {}
        if profile.get("code") and profile.get("code") != "10000":
            raise ProviderError("provider_callback_invalid", str(profile.get("sub_msg") or profile.get("msg")))
        return ProviderIdentity(
            provider=self.provider,
            subject=str(user_id),
            display_name=profile.get("nick_name") or profile.get("user_name"),
            avatar_url=profile.get("avatar"),
            raw_profile={
                "user_id": user_id,
                "province": profile.get("province"),
                "city": profile.get("city"),
                "gender": profile.get("gender"),
            },
        )


class HuaweiAdapter(ProviderAdapter):
    provider = "huawei"
    authorize_url = "https://oauth-login.cloud.huawei.com/oauth2/v3/authorize"
    scope = "openid email profile"
    client_id_key = "POLAUUH_HUAWEI_CLIENT_ID"
    client_secret_key = "POLAUUH_HUAWEI_CLIENT_SECRET"
    redirect_uri_key = "POLAUUH_HUAWEI_REDIRECT_URI"
    token_url = "https://oauth-login.cloud.huawei.com/oauth2/v3/token"
    jwks_url = "https://oauth-login.cloud.huawei.com/oauth2/v3/certs"
    issuer = "https://accounts.huawei.com"
    required_config_keys = (
        "POLAUUH_HUAWEI_CLIENT_ID",
        "POLAUUH_HUAWEI_CLIENT_SECRET",
    )

    def exchange_callback(self, request_args: dict, redirect_uri: str, nonce: str | None = None) -> ProviderIdentity:
        from flask import current_app

        code = (request_args.get("code") or "").strip()
        if not code:
            raise ProviderError("provider_callback_invalid", "缺少华为授权码。")
        redirect_uri = self.configured_redirect_uri(current_app.config, redirect_uri)
        token = self._post_form(
            self.token_url,
            {
                "code": code,
                "client_id": self.client_id(current_app.config),
                "client_secret": self.client_secret(current_app.config),
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if "error" in token:
            raise ProviderError("provider_callback_invalid", str(token.get("error_description") or token["error"]))
        claims = self._verify_id_token(token.get("id_token", ""), self.client_id(current_app.config), nonce)
        return ProviderIdentity(
            provider=self.provider,
            subject=str(claims.get("sub") or ""),
            email=claims.get("email"),
            email_verified=bool(claims.get("email_verified")),
            display_name=claims.get("name") or claims.get("display_name"),
            avatar_url=claims.get("picture"),
            raw_profile={
                "iss": claims.get("iss"),
                "email_verified": claims.get("email_verified"),
            },
        )

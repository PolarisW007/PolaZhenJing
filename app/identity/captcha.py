import logging
import os
from dataclasses import dataclass

from flask import current_app


LOGGER = logging.getLogger(__name__)


class CaptchaError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


@dataclass(frozen=True)
class CaptchaSettings:
    access_key_id: str
    access_key_secret: str
    scene_id: str
    region: str
    enabled: bool

    @classmethod
    def from_app(cls) -> "CaptchaSettings":
        return cls(
            access_key_id=os.getenv("POLAUUH_ALIYUN_ACCESS_KEY_ID", ""),
            access_key_secret=os.getenv("POLAUUH_ALIYUN_ACCESS_KEY_SECRET", ""),
            scene_id=current_app.config.get("POLAUUH_ALIYUN_CAPTCHA_SCENE_ID", ""),
            region=current_app.config.get("POLAUUH_ALIYUN_CAPTCHA_REGION", "") or "cn-shanghai",
            enabled=bool(current_app.config.get("POLAUUH_ALIYUN_CAPTCHA_ENABLED")),
        )


class AliyunCaptchaVerifier:
    def __init__(self, settings: CaptchaSettings | None = None):
        self.settings = settings or CaptchaSettings.from_app()
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        if not self.settings.access_key_id or not self.settings.access_key_secret:
            raise CaptchaError("captcha_not_configured", "真人验证缺少 AccessKey 配置。")
        if not self.settings.scene_id:
            raise CaptchaError("captcha_not_configured", "真人验证缺少 Scene ID。")
        try:
            from alibabacloud_captcha20230305.client import Client as CaptchaClient
            from alibabacloud_tea_openapi import models as open_api_models
        except ImportError as exc:
            raise CaptchaError("captcha_not_configured", "真人验证 SDK 未安装。") from exc
        config = open_api_models.Config(
            access_key_id=self.settings.access_key_id,
            access_key_secret=self.settings.access_key_secret,
        )
        config.endpoint = f"captcha.{self.settings.region}.aliyuncs.com"
        config.connect_timeout = 5000
        config.read_timeout = 5000
        self._client = CaptchaClient(config)
        return self._client

    def verify(self, captcha_verify_param: str) -> None:
        if not self.settings.enabled:
            return
        if not captcha_verify_param:
            raise CaptchaError("captcha_required", "请先完成人机验证。")
        try:
            from alibabacloud_captcha20230305 import models as captcha_models

            request = captcha_models.VerifyIntelligentCaptchaRequest(
                scene_id=self.settings.scene_id,
                captcha_verify_param=captcha_verify_param,
            )
            response = self._get_client().verify_intelligent_captcha(request)
            result = response.body.result
        except CaptchaError:
            raise
        except Exception as exc:
            LOGGER.warning("Aliyun captcha verification failed: %s", exc)
            raise CaptchaError("captcha_verify_failed", "真人验证服务暂时不可用。") from exc
        if not result or not bool(result.verify_result):
            verify_code = getattr(result, "verify_code", "") if result else ""
            raise CaptchaError("captcha_verify_failed", f"真人验证失败。{verify_code}".strip())


def verify_sms_captcha(captcha_verify_param: str) -> None:
    AliyunCaptchaVerifier().verify(captcha_verify_param)

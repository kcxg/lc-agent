"""Delivery of automation run outcomes to configured group bots."""

import asyncio
import base64
import hashlib
import hmac
import re
from dataclasses import dataclass
from time import time
from typing import Any
from urllib.parse import parse_qs, urlencode, urlsplit, urlunsplit

import httpx


PLATFORM_LABELS = {
    "wecom": "企业微信",
    "feishu": "飞书",
    "dingtalk": "钉钉",
}

_PLATFORM_HOSTS = {
    "wecom": "qyapi.weixin.qq.com",
    "feishu": "open.feishu.cn",
    "dingtalk": "oapi.dingtalk.com",
}
_PLATFORM_PATH_PREFIXES = {
    "wecom": "/cgi-bin/webhook/send",
    "feishu": "/open-apis/bot/v2/hook/",
    "dingtalk": "/robot/send",
}
_THINKING_BLOCK = re.compile(r"<!--THINK_START-->.*?(?:<!--THINK_END-->|$)", re.DOTALL)
_INTERNAL_MARKER = re.compile(r"<!--(?:TOOL|HTTP):\d+-->")
_FEISHU_MENTION = re.compile(r"</?at(?:\s+[^>]*)?>", re.IGNORECASE)
_WECOM_MAX_MESSAGE_BYTES = 3_500
_OTHER_PLATFORM_MAX_MESSAGE_BYTES = 12_000


class NotificationConfigurationError(ValueError):
    """Raised when a notification target is not a supported group webhook."""


class NotificationPlatformError(ValueError):
    """Raised when a platform accepts HTTP but rejects the message payload."""


@dataclass(slots=True)
class NotificationDelivery:
    target_name: str
    sent: bool
    error: str | None = None


@dataclass(slots=True)
class NotificationDeliverySummary:
    status: str
    error: str | None = None


def validate_notification_target(target: dict[str, Any]) -> dict[str, str]:
    """Normalize and validate one task-owned group notification target."""
    platform = str(target.get("platform", "")).strip().lower()
    if platform not in PLATFORM_LABELS:
        raise NotificationConfigurationError("通知平台仅支持企业微信、飞书或钉钉")

    name = str(target.get("name", "")).strip()
    if not name:
        raise NotificationConfigurationError("通知群名称不能为空")

    webhook = str(target.get("webhook", "")).strip()
    try:
        parsed = urlsplit(webhook)
        hostname = (parsed.hostname or "").lower()
        port = parsed.port
    except ValueError as exc:
        raise NotificationConfigurationError("Webhook 地址格式无效") from exc
    if (
        parsed.scheme != "https"
        or hostname != _PLATFORM_HOSTS[platform]
        or parsed.username
        or parsed.password
        or port is not None
        or not parsed.path.startswith(_PLATFORM_PATH_PREFIXES[platform])
    ):
        raise NotificationConfigurationError(f"请填写 {PLATFORM_LABELS[platform]} 官方 HTTPS Webhook 地址")

    query = parse_qs(parsed.query)
    required_key = "key" if platform == "wecom" else "access_token" if platform == "dingtalk" else None
    if required_key and not query.get(required_key, [""])[0].strip():
        raise NotificationConfigurationError("Webhook 地址缺少必要的访问凭证")

    normalized = {"platform": platform, "name": name, "webhook": webhook}
    secret = str(target.get("dingtalk_secret") or "").strip()
    if secret:
        if platform != "dingtalk":
            raise NotificationConfigurationError("签名密钥仅适用于钉钉机器人")
        normalized["dingtalk_secret"] = secret
    return normalized


def _strip_internal_content(content: str) -> str:
    content = _THINKING_BLOCK.sub("", content)
    content = _INTERNAL_MARKER.sub("", content)
    content = _FEISHU_MENTION.sub("", content)
    content = content.replace("@all", "＠all").replace("@所有人", "＠所有人")
    return content.strip()


def _safe_failure_message(app_name: str) -> str:
    return f"自动化任务执行失败，请在 {app_name} 中查看执行记录。"


def _success_message(app_name: str, task_name: str, final_output: str) -> str:
    body = _strip_internal_content(final_output)
    if not body:
        body = "任务已完成，但没有可推送的结果内容。"
    return f"## {app_name} · {task_name}\n\n{body}"


def _failure_message(app_name: str, task_name: str) -> str:
    return f"## {app_name} · {task_name}\n\n> 执行失败\n\n{_safe_failure_message(app_name)}"


def _prefix_fitting_bytes(content: str, max_bytes: int) -> int:
    low = 1
    high = min(len(content), max_bytes)
    while low < high:
        middle = (low + high + 1) // 2
        if len(content[:middle].encode("utf-8")) <= max_bytes:
            low = middle
        else:
            high = middle - 1
    return low


def _split_message(content: str, max_bytes: int = _OTHER_PLATFORM_MAX_MESSAGE_BYTES) -> list[str]:
    if len(content.encode("utf-8")) <= max_bytes:
        return [content]

    chunks: list[str] = []
    remaining = content
    while len(remaining.encode("utf-8")) > max_bytes:
        fitting_chars = _prefix_fitting_bytes(remaining, max_bytes)
        split_at = remaining.rfind("\n", 0, fitting_chars + 1)
        if split_at < fitting_chars // 2:
            split_at = fitting_chars
        if split_at <= 0:
            split_at = fitting_chars
        chunks.append(remaining[:split_at].rstrip())
        remaining = remaining[split_at:].lstrip()
    if remaining:
        chunks.append(remaining)
    return chunks


def _signed_dingtalk_webhook(webhook: str, secret: str) -> str:
    timestamp = str(int(time() * 1000))
    string_to_sign = f"{timestamp}\n{secret}"
    signature = base64.b64encode(
        hmac.new(secret.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha256).digest()
    ).decode("utf-8")
    parsed = urlsplit(webhook)
    query = parse_qs(parsed.query, keep_blank_values=True)
    query["timestamp"] = [timestamp]
    query["sign"] = [signature]
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query, doseq=True), parsed.fragment))


class AutomationNotificationService:
    """Posts a run result to each of the task's independently configured groups."""

    def __init__(self, *, app_name: str = "lc-agent", timeout: float = 10.0):
        self.app_name = str(app_name).strip() or "lc-agent"
        self.timeout = timeout

    async def deliver_run(
        self,
        targets: list[dict[str, Any]],
        *,
        task_name: str,
        run_status: str,
        final_output: str = "",
    ) -> NotificationDeliverySummary:
        if not targets:
            return NotificationDeliverySummary(status="not_configured")

        content = (
            _success_message(self.app_name, task_name, final_output)
            if run_status == "success"
            else _failure_message(self.app_name, task_name)
        )
        deliveries = await asyncio.gather(
            *(self._deliver_target(target, content, task_name) for target in targets),
        )
        failed = [delivery for delivery in deliveries if not delivery.sent]
        if not failed:
            return NotificationDeliverySummary(status="sent")
        error = "；".join(f"{delivery.target_name}: {delivery.error}" for delivery in failed)
        if len(failed) == len(deliveries):
            return NotificationDeliverySummary(status="failed", error=error)
        return NotificationDeliverySummary(status="partial_failed", error=error)

    async def send_test(self, target: dict[str, Any]) -> NotificationDelivery:
        normalized = validate_notification_target(target)
        content = f"## {self.app_name} 通知测试\n\n通知目标：{normalized['name']}\n\n测试发送成功。"
        return await self._deliver_target(normalized, content, f"{self.app_name} 通知测试")

    async def _deliver_target(
        self,
        target: dict[str, Any],
        content: str,
        title: str,
    ) -> NotificationDelivery:
        try:
            normalized = validate_notification_target(target)
        except NotificationConfigurationError as exc:
            return NotificationDelivery(target_name=str(target.get("name") or "未命名群"), sent=False, error=str(exc))

        max_bytes = (
            _WECOM_MAX_MESSAGE_BYTES
            if normalized["platform"] == "wecom"
            else _OTHER_PLATFORM_MAX_MESSAGE_BYTES
        )
        chunks = _split_message(content, max_bytes=max_bytes)
        for index, chunk in enumerate(chunks, start=1):
            chunk_title = title if len(chunks) == 1 else f"{title}（{index}/{len(chunks)}）"
            try:
                await self._post(normalized, chunk, chunk_title)
            except httpx.TimeoutException:
                return NotificationDelivery(normalized["name"], sent=False, error="请求超时")
            except httpx.HTTPError:
                return NotificationDelivery(normalized["name"], sent=False, error="网络请求失败")
            except NotificationPlatformError as exc:
                return NotificationDelivery(normalized["name"], sent=False, error=f"平台拒绝请求（{exc}）")
            except ValueError:
                return NotificationDelivery(normalized["name"], sent=False, error="平台拒绝请求")
        return NotificationDelivery(normalized["name"], sent=True)

    async def _post(self, target: dict[str, str], content: str, title: str) -> None:
        platform = target["platform"]
        webhook = target["webhook"]
        if platform == "wecom":
            payload = {"msgtype": "markdown", "markdown": {"content": content}}
        elif platform == "feishu":
            payload = {
                "msg_type": "interactive",
                "card": {"elements": [{"tag": "markdown", "content": content}]},
            }
        else:
            payload = {"msgtype": "markdown", "markdown": {"title": title, "text": content}}
            if target.get("dingtalk_secret"):
                webhook = _signed_dingtalk_webhook(webhook, target["dingtalk_secret"])

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(webhook, json=payload)
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError as exc:
            raise ValueError("invalid response") from exc
        if not isinstance(data, dict):
            raise ValueError("invalid response")

        code = data.get("errcode", data.get("code", data.get("StatusCode", 0)))
        if str(code) != "0":
            platform_message = data.get("errmsg") or data.get("msg") or "业务错误"
            raise NotificationPlatformError(str(platform_message)[:160])

from urllib.parse import parse_qs, urlsplit

import pytest

from lc_agent.server.automation_notifications import (
    AutomationNotificationService,
    NotificationConfigurationError,
    NotificationPlatformError,
    _split_message,
    _strip_internal_content,
    validate_notification_target,
)


def test_notification_target_accepts_only_matching_official_webhooks():
    target = validate_notification_target({
        "platform": "wecom",
        "name": "研发群",
        "webhook": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test-key",
    })
    assert target["name"] == "研发群"

    with pytest.raises(NotificationConfigurationError):
        validate_notification_target({
            "platform": "wecom",
            "name": "研发群",
            "webhook": "https://example.com/cgi-bin/webhook/send?key=test-key",
        })

    with pytest.raises(NotificationConfigurationError):
        validate_notification_target({
            "platform": "dingtalk",
            "name": "研发群",
            "webhook": "https://oapi.dingtalk.com/robot/send",
        })


def test_notification_content_removes_internal_markers_and_mentions():
    content = _strip_internal_content(
        "<!--THINK_START-->internal<!--THINK_END-->\n"
        "<!--TOOL:2-->\n<!--HTTP:1-->\n"
        "<at user_id=\"all\">所有人</at> @all @所有人\n结果正文"
    )
    assert "internal" not in content
    assert "<!--" not in content
    assert "<at" not in content
    assert "@all" not in content
    assert content.endswith("结果正文")


def test_notification_message_splits_at_newlines_when_possible():
    content = "中文内容" * 1_500 + "\n第二段"
    chunks = _split_message(content, max_bytes=3_500)
    assert len(chunks) > 1
    assert len(chunks[0].encode("utf-8")) <= 3_500
    assert "".join(chunks).replace("\n", "") == content.replace("\n", "")
    assert chunks[-1].endswith("第二段")


def test_notification_message_does_not_split_short_ascii_content():
    content = "x" * 3_500
    assert _split_message(content, max_bytes=3_500) == [content]


@pytest.mark.asyncio
async def test_delivery_uses_platform_specific_payloads_and_summarizes_partial_failure(monkeypatch):
    sent: list[tuple[dict[str, str], str, str]] = []

    async def fake_post(self, target, content, title):
        sent.append((target, content, title))
        if target["name"] == "失败群":
            raise NotificationPlatformError("业务错误")

    monkeypatch.setattr(AutomationNotificationService, "_post", fake_post)
    service = AutomationNotificationService()
    summary = await service.deliver_run(
        [
            {
                "platform": "feishu",
                "name": "飞书群",
                "webhook": "https://open.feishu.cn/open-apis/bot/v2/hook/test-token",
            },
            {
                "platform": "dingtalk",
                "name": "失败群",
                "webhook": "https://oapi.dingtalk.com/robot/send?access_token=test-token",
            },
        ],
        task_name="每日摘要",
        run_status="success",
        final_output="<!--THINK_START-->不发送<!--THINK_END-->\n正文",
    )

    assert summary.status == "partial_failed"
    assert "失败群: 平台拒绝请求（业务错误）" in (summary.error or "")
    assert len(sent) == 2
    assert all("不发送" not in content for _, content, _ in sent)


@pytest.mark.asyncio
async def test_wecom_delivery_splits_chinese_news_digest_by_utf8_bytes(monkeypatch):
    sent: list[str] = []

    async def fake_post(self, target, content, title):
        sent.append(content)

    monkeypatch.setattr(AutomationNotificationService, "_post", fake_post)
    summary = await AutomationNotificationService().deliver_run(
        [{
            "platform": "wecom",
            "name": "新闻群",
            "webhook": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test-key",
        }],
        task_name="每日 AI 新闻简报",
        run_status="success",
        final_output="新闻内容" * 1_500,
    )

    assert summary.status == "sent"
    assert len(sent) > 1
    assert all(len(chunk.encode("utf-8")) <= 3_500 for chunk in sent)


@pytest.mark.asyncio
async def test_notification_uses_configured_application_name(monkeypatch):
    sent: list[str] = []

    async def fake_post(self, target, content, title):
        sent.append(content)

    monkeypatch.setattr(AutomationNotificationService, "_post", fake_post)
    delivery = await AutomationNotificationService(app_name="心有灵犀").send_test({
        "platform": "wecom",
        "name": "研发群",
        "webhook": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=test-key",
    })

    assert delivery.sent is True
    assert sent[0].startswith("## 心有灵犀 通知测试")


def test_dingtalk_signature_preserves_access_token():
    from lc_agent.server.automation_notifications import _signed_dingtalk_webhook

    signed = _signed_dingtalk_webhook(
        "https://oapi.dingtalk.com/robot/send?access_token=test-token",
        "SEC-test",
    )
    query = parse_qs(urlsplit(signed).query)
    assert query["access_token"] == ["test-token"]
    assert query["timestamp"]
    assert query["sign"]

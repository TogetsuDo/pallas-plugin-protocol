from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from pallas_plugin_protocol.snowluma_webui_client import (
    generate_snowluma_managed_webui_password,
    snowluma_ensure_webui_session,
)


def test_generate_snowluma_managed_webui_password_strength() -> None:
    pwd = generate_snowluma_managed_webui_password()
    assert len(pwd) >= 10
    assert any(c.isupper() for c in pwd)
    assert any(c.islower() for c in pwd)
    assert any(not c.isalnum() for c in pwd)
    assert " " not in pwd


@pytest.mark.asyncio
async def test_snowluma_ensure_webui_session_rotates_password() -> None:
    calls: list[tuple[str, str]] = []
    consented = {"ok": False}

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/api/login":
            body = json.loads(request.content.decode())
            calls.append(("login", body.get("password", "")))
            pwd = str(body.get("password") or "")
            if pwd == "af7c7aaa85693d30":
                return httpx.Response(
                    200,
                    json={
                        "success": True,
                        "token": "tok-bootstrap",
                        "mustChangePassword": True,
                    },
                )
            if pwd.startswith("Pa!"):
                return httpx.Response(
                    200,
                    json={"success": True, "token": "tok-managed"},
                )
            return httpx.Response(401, json={"success": False, "message": "bad"})
        if path == "/api/agreements":
            calls.append(("agreements", request.headers.get("Authorization", "")))
            if consented["ok"]:
                return httpx.Response(200, json={"consentRequired": False})
            return httpx.Response(
                200,
                json={"consentRequired": True, "version": "eula-test"},
            )
        if path == "/api/agreements/record-consent":
            calls.append(("consent", "ok"))
            consented["ok"] = True
            return httpx.Response(200, json={"success": True})
        if path == "/api/auth/change-password":
            calls.append(("change-password", "ok"))
            if not consented["ok"]:
                return httpx.Response(
                    403,
                    json={
                        "status": "failed",
                        "message": "请先阅读并同意用户协议与隐私政策",
                        "consentRequired": True,
                    },
                )
            return httpx.Response(200, json={"success": True, "requireRelogin": True})
        if path == "/api/processes":
            auth = request.headers.get("Authorization", "")
            if auth == "Bearer tok-managed":
                return httpx.Response(200, json={"list": [{"pid": 1, "uin": "12345"}]})
            return httpx.Response(
                403,
                json={
                    "status": "failed",
                    "message": "请先修改密码",
                    "mustChangePassword": True,
                },
            )
        return httpx.Response(404)

    transport = httpx.MockTransport(handler)
    account: dict[str, Any] = {}
    async with httpx.AsyncClient(
        transport=transport, base_url="http://sl.test"
    ) as client:
        headers, dirty = await snowluma_ensure_webui_session(
            client,
            "http://sl.test",
            account,
            ["initial credentials: user=admin password=af7c7aaa85693d30"],
        )

    assert dirty is True
    assert headers["Authorization"] == "Bearer tok-managed"
    assert str(account.get("snowluma_managed_webui_password", "")).startswith("Pa!")
    assert ("login", "af7c7aaa85693d30") in calls
    assert ("consent", "ok") in calls
    assert ("change-password", "ok") in calls
    # 必须先同意协议再改密
    assert calls.index(("consent", "ok")) < calls.index(("change-password", "ok"))

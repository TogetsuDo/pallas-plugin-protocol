"""重新上号风险设备问答的纯逻辑测试。"""

from __future__ import annotations

import asyncio
import importlib.util
import sys
import types
from dataclasses import dataclass, field
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1] / "src" / "pallas_plugin_relogin_bot"


def load_module(qualified: str, filename: str):
    spec = importlib.util.spec_from_file_location(qualified, _ROOT / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[qualified] = module
    spec.loader.exec_module(module)
    return module


nonebot = types.ModuleType("nonebot")
nonebot.get_driver = lambda: types.SimpleNamespace(
    config=types.SimpleNamespace(superusers=set())
)
sys.modules.setdefault("nonebot", nonebot)

config = types.ModuleType("pallas.api.config")
config.user_is_bot_admin = None
sys.modules.setdefault("pallas.api.config", config)

db = types.ModuleType("pallas.core.foundation.db")
db.make_bot_config_repository = lambda: None
sys.modules.setdefault("pallas.core.foundation.db", db)


@dataclass
class ReplyItem:
    kind: str
    content: str


@dataclass
class ReloginHandleResult:
    replies: list[ReplyItem] = field(default_factory=list)
    session_active: bool = False
    reject_hint: str | None = None


payload = types.ModuleType("pallas.core.platform.shard.coord.relogin_payload")
payload.ReplyItem = ReplyItem
payload.ReloginHandleResult = ReloginHandleResult
sys.modules.setdefault("pallas.core.platform.shard.coord.relogin_payload", payload)

pkg = types.ModuleType("pallas_plugin_relogin_bot")
pkg.__path__ = [str(_ROOT)]
sys.modules.setdefault("pallas_plugin_relogin_bot", pkg)

service = load_module("pallas_plugin_relogin_bot.service_risk_test", "service.py")


def test_parse_risk_device_answer() -> None:
    assert service.parse_risk_device_answer("是") is True
    assert service.parse_risk_device_answer("否") is False
    assert service.parse_risk_device_answer("不确定") is None


def test_existing_snowluma_account_waits_for_risk_answer(monkeypatch) -> None:
    protocol = types.ModuleType("pallas_plugin_protocol")
    protocol.manager = types.SimpleNamespace(
        has_account=lambda _qq: True,
        get_account=lambda _qq: {
            "protocol_backend": "snowluma",
            "snowluma_linux_docker": True,
        },
    )
    sys.modules["pallas_plugin_protocol"] = protocol
    capture = types.ModuleType("pallas_plugin_protocol.snowluma_qr_capture")
    capture.account_uses_snowluma_docker = lambda _account: True
    sys.modules["pallas_plugin_protocol.snowluma_qr_capture"] = capture

    async def is_admin(_qq: int, _user_id: int) -> bool:
        return True

    monkeypatch.setattr(service, "user_is_bot_admin", is_admin)
    session = service.ReloginSession(
        kind="relogin", step="validate_qq", data={"qq": "123456"}
    )
    result = ReloginHandleResult()

    asyncio.run(
        service.handle_relogin_session(
            session, "10001", "牛牛重新上号 123456", False, result, "key"
        )
    )

    assert session.step == "await_risk_device"
    assert result.session_active
    assert [item.content for item in result.replies] == [
        "是否提示“风险/外挂设备”？（是/否）"
    ]

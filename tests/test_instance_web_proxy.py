from types import SimpleNamespace

import nonebot
import pytest

nonebot.init()

from pallas_plugin_protocol.instance_web_proxy import resolve_instance_proxy_target  # noqa: E402


def test_resolve_webui_targets_the_registered_loopback_port() -> None:
    target = resolve_instance_proxy_target(
        {
            "protocol_backend": "napcat",
            "webui_port": 16099,
        },
        surface="webui",
        config=SimpleNamespace(),
    )

    assert target.origin == "http://127.0.0.1:16099"
    assert target.base_path == "/webui/"


def test_resolve_snowluma_novnc_requires_the_registered_docker_port() -> None:
    target = resolve_instance_proxy_target(
        {
            "protocol_backend": "snowluma",
            "snowluma_linux_docker": True,
            "snowluma_docker_host_novnc_port": 16081,
        },
        surface="novnc",
        config=SimpleNamespace(),
    )

    assert target.origin == "http://127.0.0.1:16081"
    assert target.base_path == "/"


def test_resolve_novnc_rejects_non_snowluma_accounts() -> None:
    with pytest.raises(ValueError, match="仅支持 SnowLuma"):
        resolve_instance_proxy_target(
            {"protocol_backend": "napcat", "webui_port": 16099},
            surface="novnc",
            config=SimpleNamespace(),
        )

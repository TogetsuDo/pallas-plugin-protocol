"""SnowLuma Docker 内存限额与资源参数。"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace

_ROOT = Path(__file__).resolve().parents[1] / "src" / "pallas_plugin_protocol"
_PKG = "pallas_plugin_protocol_docker_prod_test"


def load_module(qualified: str, filename: str):
    path = _ROOT / filename
    spec = importlib.util.spec_from_file_location(qualified, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[qualified] = mod
    spec.loader.exec_module(mod)
    return mod


if _PKG not in sys.modules:
    pkg = types.ModuleType(_PKG)
    pkg.__path__ = [str(_ROOT)]
    sys.modules[_PKG] = pkg

for name, file in (
    ("docker_cli", "docker_cli.py"),
    ("docker_onebot_host", "docker_onebot_host.py"),
    ("linux_docker", "linux_docker.py"),
):
    load_module(f"{_PKG}.{name}", file)

snowluma_docker = load_module(f"{_PKG}.snowluma_docker", "snowluma_docker.py")
append_snowluma_docker_resource_limits = (
    snowluma_docker.append_snowluma_docker_resource_limits
)
build_snowluma_docker_run_argv = snowluma_docker.build_snowluma_docker_run_argv


def test_append_snowluma_docker_resource_limits() -> None:
    cfg = SimpleNamespace(
        pallas_protocol_snowluma_docker_memory_limit="1g",
        pallas_protocol_snowluma_docker_memory_swap="1536m",
    )
    argv: list[str] = ["run", "-d"]
    append_snowluma_docker_resource_limits(argv, cfg)
    assert "--memory" in argv
    assert "1g" in argv
    assert "--memory-swap" in argv
    assert "1536m" in argv


def test_build_snowluma_docker_run_argv_includes_memory_limits() -> None:
    cfg = SimpleNamespace(
        pallas_protocol_snowluma_docker_image="motricseven7/snowluma:latest",
        pallas_protocol_snowluma_docker_internal_webui_port=5099,
        pallas_protocol_snowluma_docker_internal_onebot_http_port=3000,
        pallas_protocol_snowluma_docker_internal_onebot_ws_port=3001,
        pallas_protocol_snowluma_docker_shm_size="1g",
        pallas_protocol_snowluma_docker_memory_limit="1g",
        pallas_protocol_snowluma_docker_memory_swap="1536m",
        pallas_protocol_snowluma_docker_vnc_passwd="",
        pallas_protocol_snowluma_docker_host_novnc_port=0,
        pallas_protocol_snowluma_docker_host_vnc_port=0,
        pallas_protocol_snowluma_docker_internal_novnc_port=6081,
        pallas_protocol_snowluma_docker_internal_vnc_port=5900,
    )
    account = {
        "id": "123",
        "webui_port": 6100,
        "snowluma_docker_host_onebot_http": 17100,
        "snowluma_docker_host_onebot_ws": 17101,
        "account_data_dir": "/tmp/sl-test",
    }

    def resolve_qq(acc: dict) -> str:
        return str(acc.get("id", ""))

    argv = build_snowluma_docker_run_argv(account, cfg, resolve_qq)
    assert "--memory" in argv
    assert "--cap-add" in argv
    assert "SYS_PTRACE" in argv
    assert "SNOWLUMA_ACCEPT_EULA=1" in argv
    assert "SNOWLUMA_ACCEPT_PRIVACY=1" in argv

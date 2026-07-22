"""SnowLuma Runtime 注册表与 Docker 命名单测。"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1] / "src" / "pallas_plugin_protocol"


def load_module(qualified: str, filename: str):
    path = _ROOT / filename
    spec = importlib.util.spec_from_file_location(qualified, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[qualified] = mod
    spec.loader.exec_module(mod)
    return mod


if "pallas_plugin_protocol" not in sys.modules:
    pkg = types.ModuleType("pallas_plugin_protocol")
    pkg.__path__ = [str(_ROOT)]
    sys.modules["pallas_plugin_protocol"] = pkg

load_module("pallas_plugin_protocol.contract", "contract.py")
load_module("pallas_plugin_protocol.docker_cli", "docker_cli.py")
load_module("pallas_plugin_protocol.docker_onebot_host", "docker_onebot_host.py")
load_module("pallas_plugin_protocol.linux_docker", "linux_docker.py")
snowluma_docker = load_module(
    "pallas_plugin_protocol.snowluma_docker", "snowluma_docker.py"
)
registry = load_module(
    "pallas_plugin_protocol.snowluma_runtime_registry",
    "snowluma_runtime_registry.py",
)

SnowLumaRuntimeRegistry = registry.SnowLumaRuntimeRegistry
SNOWLUMA_PROTOCOL_BACKEND = registry.SNOWLUMA_PROTOCOL_BACKEND
SNOWLUMA_RUNTIME_ID_KEY = registry.SNOWLUMA_RUNTIME_ID_KEY
snowluma_docker_container_name_for_runtime = (
    snowluma_docker.snowluma_docker_container_name_for_runtime
)
clear_snowluma_login_state_for_uin = snowluma_docker.clear_snowluma_login_state_for_uin


def test_migrate_legacy_accounts_creates_one_runtime_each(tmp_path: Path) -> None:
    data_dir = tmp_path / "plugin"
    instances = tmp_path / "instances"
    data_dir.mkdir()
    instances.mkdir()
    reg = SnowLumaRuntimeRegistry(data_dir, instances)
    accounts = {
        "10001": {
            "id": "10001",
            "qq": "10001",
            "protocol_backend": SNOWLUMA_PROTOCOL_BACKEND,
            "account_data_dir": str(instances / "10001" / "snowluma"),
            "webui_port": 6100,
        },
        "10002": {
            "id": "10002",
            "qq": "10002",
            "protocol_backend": SNOWLUMA_PROTOCOL_BACKEND,
            "account_data_dir": str(instances / "10002" / "snowluma"),
            "webui_port": 6101,
        },
    }
    assert reg.migrate_legacy_accounts(accounts) is True
    assert len(reg.list_runtimes()) == 2
    assert accounts["10001"][SNOWLUMA_RUNTIME_ID_KEY]
    assert accounts["10002"][SNOWLUMA_RUNTIME_ID_KEY]
    assert (
        accounts["10001"][SNOWLUMA_RUNTIME_ID_KEY]
        != accounts["10002"][SNOWLUMA_RUNTIME_ID_KEY]
    )
    rt1 = reg.get(accounts["10001"][SNOWLUMA_RUNTIME_ID_KEY])
    assert rt1 is not None
    assert rt1["legacy_container_account_id"] == "10001"
    assert rt1["data_dir"] == accounts["10001"]["account_data_dir"]
    assert reg.migrate_legacy_accounts(accounts) is False


def test_two_accounts_can_share_runtime_data_dir(tmp_path: Path) -> None:
    data_dir = tmp_path / "plugin"
    instances = tmp_path / "instances"
    data_dir.mkdir()
    instances.mkdir()
    reg = SnowLumaRuntimeRegistry(data_dir, instances)
    runtime = reg.create({"display_name": "pool", "webui_port": 6200})
    shared = runtime["data_dir"]
    cfg = Path(shared) / "config"
    cfg.mkdir(parents=True, exist_ok=True)
    (cfg / "onebot_20001.json").write_text("{}", encoding="utf-8")
    (cfg / "onebot_20002.json").write_text("{}", encoding="utf-8")
    assert (cfg / "onebot_20001.json").is_file()
    assert (cfg / "onebot_20002.json").is_file()


def test_docker_container_name_runtime_vs_legacy() -> None:
    assert (
        snowluma_docker_container_name_for_runtime({"id": "sl-rt-abc"})
        == "pallas-proto-sl-rt-sl-rt-abc"
    )
    assert (
        snowluma_docker_container_name_for_runtime(
            {"id": "sl-rt-abc", "legacy_container_account_id": "10001"}
        )
        == "pallas-proto-sl-10001"
    )


def test_clear_login_state_for_uin_does_not_wipe_volume(tmp_path: Path) -> None:
    root = tmp_path / "rt"
    cache = root / "cache"
    cache.mkdir(parents=True)
    (cache / "qrcode_30001.png").write_bytes(b"x")
    (cache / "qrcode.png").write_bytes(b"y")
    cfg = root / "docker" / "snowluma" / "dot-config" / "30001"
    cfg.mkdir(parents=True)
    (cfg / "x").write_text("1", encoding="utf-8")
    other = root / "docker" / "snowluma" / "dot-config" / "30002"
    other.mkdir(parents=True)
    (other / "y").write_text("2", encoding="utf-8")
    n = clear_snowluma_login_state_for_uin(root, "30001")
    assert n >= 1
    assert not (cache / "qrcode_30001.png").exists()
    assert other.is_dir()


def test_build_docker_argv_uses_runtime_id_not_legacy_when_bound(tmp_path: Path) -> None:
    class Cfg:
        pallas_protocol_snowluma_docker_internal_webui_port = 5099
        pallas_protocol_snowluma_docker_internal_onebot_http_port = 3000
        pallas_protocol_snowluma_docker_internal_onebot_ws_port = 3001
        pallas_protocol_snowluma_docker_shm_size = "1g"
        pallas_protocol_snowluma_docker_vnc_passwd = "vnc"
        pallas_protocol_snowluma_docker_host_novnc_port = 0
        pallas_protocol_snowluma_docker_host_vnc_port = 0
        pallas_protocol_snowluma_docker_internal_novnc_port = 6081
        pallas_protocol_snowluma_docker_internal_vnc_port = 5900
        pallas_protocol_snowluma_docker_memory_limit = ""
        pallas_protocol_snowluma_docker_memory_swap = ""
        pallas_protocol_snowluma_docker_cpus = ""

    data = tmp_path / "rt-data"
    data.mkdir()
    account = {
        "id": "40001",
        "snowluma_runtime_id": "sl-rt-shared",
        "account_data_dir": str(data),
        "webui_port": 6200,
        "snowluma_docker_host_onebot_http": 13000,
        "snowluma_docker_host_onebot_ws": 13001,
        "snowluma_docker_host_novnc_port": 16080,
        "snowluma_docker_host_vnc_port": 15900,
    }
    argv = snowluma_docker.build_snowluma_docker_run_argv(
        account, Cfg(), lambda a: str(a.get("id", ""))
    )
    assert "--name" in argv
    name = argv[argv.index("--name") + 1]
    assert name == "pallas-proto-sl-rt-sl-rt-shared"
    assert "pallas-proto-sl-40001" not in argv
    assert any(a.startswith("pallas.runtime_id=") for a in argv)


def test_process_track_key_is_runtime_scoped() -> None:
    ops = load_module(
        "pallas_plugin_protocol.snowluma_runtime_ops",
        "snowluma_runtime_ops.py",
    )
    assert ops.snowluma_process_track_key("sl-rt-abc") == "slrt:sl-rt-abc"


def test_shared_runtime_members_and_onebot_paths(tmp_path: Path) -> None:
    data_dir = tmp_path / "plugin"
    instances = tmp_path / "instances"
    data_dir.mkdir()
    instances.mkdir()
    reg = SnowLumaRuntimeRegistry(data_dir, instances)
    runtime = reg.create({"display_name": "pool", "webui_port": 6300})
    rid = runtime["id"]
    shared = Path(runtime["data_dir"])
    cfg = shared / "config"
    cfg.mkdir(parents=True, exist_ok=True)
    accounts = {
        "50001": {
            "id": "50001",
            "qq": "50001",
            "protocol_backend": SNOWLUMA_PROTOCOL_BACKEND,
            SNOWLUMA_RUNTIME_ID_KEY: rid,
            "account_data_dir": str(shared),
        },
        "50002": {
            "id": "50002",
            "qq": "50002",
            "protocol_backend": SNOWLUMA_PROTOCOL_BACKEND,
            SNOWLUMA_RUNTIME_ID_KEY: rid,
            "account_data_dir": str(shared),
        },
    }
    members = [
        aid
        for aid, acc in accounts.items()
        if str(acc.get(SNOWLUMA_RUNTIME_ID_KEY, "")).strip() == rid
    ]
    assert sorted(members) == ["50001", "50002"]
    # 同 Runtime 下两个 QQ 各有独立 onebot 文件，互不覆盖
    (cfg / "onebot_50001.json").write_text('{"qq":"50001"}', encoding="utf-8")
    (cfg / "onebot_50002.json").write_text('{"qq":"50002"}', encoding="utf-8")
    assert (cfg / "onebot_50001.json").read_text(encoding="utf-8") == '{"qq":"50001"}'
    assert (cfg / "onebot_50002.json").read_text(encoding="utf-8") == '{"qq":"50002"}'
    # 启停 QQ 语义：共享 Runtime 时不应因单号清理而删邻号登录态
    clear_snowluma_login_state_for_uin(shared, "50001")
    assert (cfg / "onebot_50002.json").is_file()
    other_cfg = shared / "docker" / "snowluma" / "dot-config" / "50002"
    other_cfg.mkdir(parents=True, exist_ok=True)
    (other_cfg / "keep").write_text("1", encoding="utf-8")
    clear_snowluma_login_state_for_uin(shared, "50001")
    assert (other_cfg / "keep").is_file()

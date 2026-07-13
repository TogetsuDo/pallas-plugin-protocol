"""SnowLuma 健康态与迁移逻辑单元测试。"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1] / "src" / "pallas_plugin_protocol"
_PKG = "pallas_plugin_protocol_prod_test"


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

contract = load_module(f"{_PKG}.contract", "contract.py")
migration = load_module(f"{_PKG}.account_migration", "account_migration.py")
health = load_module(f"{_PKG}.snowluma_health", "snowluma_health.py")

ACCOUNT_PROTOCOL_BACKEND_KEY = contract.ACCOUNT_PROTOCOL_BACKEND_KEY
SNOWLUMA_PROTOCOL_BACKEND = contract.SNOWLUMA_PROTOCOL_BACKEND
migrate_account_dict_to_snowluma = migration.migrate_account_dict_to_snowluma
prepare_account_for_snowluma_migration = (
    migration.prepare_account_for_snowluma_migration
)
assess_snowluma_account_health = health.assess_snowluma_account_health
snowluma_config = load_module(f"{_PKG}.snowluma_config", "snowluma_config.py")


class FakeLaunch:
    def apply_defaults(self, account, resolve_qq) -> None:
        account["snowluma_linux_docker"] = True
        account["command"] = "docker"
        account["args"] = ["run"]
        _ = resolve_qq(account)


def test_assess_snowluma_needs_login() -> None:
    result = assess_snowluma_account_health(
        {"protocol_backend": "snowluma"},
        container_running=True,
        bot_connected=False,
    )
    assert result["login_required"] is True
    assert result["health_status"] == "needs_login"


def test_migrate_account_dict_to_snowluma_fresh_dir(tmp_path: Path) -> None:
    account = {
        "id": "999",
        "protocol_backend": "napcat",
        "napcat_linux_docker": True,
        "account_data_dir": str(tmp_path / "legacy"),
        "command": "docker",
        "args": ["run"],
    }
    instances = tmp_path / "instances"
    migrate_account_dict_to_snowluma(
        account,
        launch=FakeLaunch(),
        resolve_qq=lambda a: str(a.get("id", "")),
        instances_root=instances,
        preserve_napcat_data=False,
    )
    assert account[ACCOUNT_PROTOCOL_BACKEND_KEY] == SNOWLUMA_PROTOCOL_BACKEND
    assert account["account_data_dir"].endswith("/instances/999/snowluma")
    assert account.get("napcat_linux_docker") is None


def test_prepare_account_preserve_data_keeps_dir(tmp_path: Path) -> None:
    account = {
        "id": "1",
        "protocol_backend": "napcat",
        "account_data_dir": str(tmp_path / "legacy"),
    }
    prepare_account_for_snowluma_migration(
        account,
        instances_root=tmp_path / "instances",
        preserve_napcat_data=True,
    )
    assert account["account_data_dir"] == str(tmp_path / "legacy")
    assert account[ACCOUNT_PROTOCOL_BACKEND_KEY] == SNOWLUMA_PROTOCOL_BACKEND


def test_snowluma_webui_password_from_webui_log_line() -> None:
    lines = [
        "22:39:16 INFO [WebUI] initial credentials: user=admin password=Ce39287f8d0a2581",
    ]
    assert (
        snowluma_config.extract_snowluma_webui_temp_password_from_log_lines(lines)
        == "ce39287f8d0a2581"
    )


def test_snowluma_webui_password_from_docker_log_files(tmp_path: Path) -> None:
    account = {
        "qq": "3879348674",
        "account_data_dir": str(tmp_path),
        "snowluma_linux_docker": True,
    }
    log_dir = tmp_path / "docker" / "snowluma" / "snowluma-data" / "logs"
    log_dir.mkdir(parents=True)
    (log_dir / "snowluma-2026-07-13.log").write_text(
        "21:00:00 INFO [WebUI] initial credentials: user=admin password=abc12345deadbeef\n",
        encoding="utf-8",
    )
    merged = snowluma_config.collect_snowluma_webui_log_lines(account, [])
    assert (
        snowluma_config.resolve_snowluma_webui_temp_password(account, merged)
        == "abc12345deadbeef"
    )


def test_snowluma_webui_password_prefers_newest_log_file(tmp_path: Path) -> None:
    account = {
        "qq": "923722427",
        "account_data_dir": str(tmp_path),
        "snowluma_linux_docker": True,
    }
    log_dir = tmp_path / "docker" / "snowluma" / "snowluma-data" / "logs"
    log_dir.mkdir(parents=True)
    (log_dir / "snowluma-2026-07-14.log").write_text(
        "00:16:09 INFO [WebUI] initial credentials: user=admin password=a3f9754ffd9d9b1a\n",
        encoding="utf-8",
    )
    (log_dir / "snowluma-2026-07-13.log").write_text(
        "21:00:00 INFO [WebUI] initial credentials: user=admin password=33b634ed0f95647a\n",
        encoding="utf-8",
    )
    assert (
        snowluma_config.resolve_snowluma_webui_temp_password(account, [])
        == "a3f9754ffd9d9b1a"
    )

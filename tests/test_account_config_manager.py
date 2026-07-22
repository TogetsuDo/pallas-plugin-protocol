"""账号配置更新的兼容性测试。"""

import json

import nonebot
import pytest

nonebot.init()

from pallas_plugin_protocol.config_manager import AccountConfigManager  # noqa: E402


@pytest.mark.parametrize("enabled", [True, False])
def test_update_napcat_bypass_enabled_sets_all_bypass_switches(
    tmp_path, enabled: bool
) -> None:
    account = {"account_data_dir": str(tmp_path), "qq": "10001"}
    manager = AccountConfigManager()

    manager.update_account_configs(
        account,
        {"napcat": {"bypass_enabled": enabled}},
        lambda item: item["qq"],
    )

    napcat = json.loads((tmp_path / "config" / "napcat.json").read_text())
    assert napcat["bypass"] == {
        "hook": enabled,
        "window": enabled,
        "module": enabled,
        "process": enabled,
        "container": enabled,
        "js": enabled,
    }
    assert "bypass_enabled" not in napcat


def test_update_napcat_keeps_direct_bypass_object_compatibility(tmp_path) -> None:
    account = {"account_data_dir": str(tmp_path), "qq": "10001"}
    manager = AccountConfigManager()
    bypass = {"hook": True, "window": False}

    manager.update_account_configs(
        account,
        {"napcat": {"bypass": bypass}},
        lambda item: item["qq"],
    )

    napcat = json.loads((tmp_path / "config" / "napcat.json").read_text())
    assert napcat["bypass"] == bypass


def test_sync_napcat_core_enables_bypass_by_default(tmp_path) -> None:
    account = {"account_data_dir": str(tmp_path), "qq": "10001"}

    AccountConfigManager().sync_napcat_core(account, lambda item: item["qq"])

    napcat = json.loads((tmp_path / "config" / "napcat.json").read_text())
    assert all(napcat["bypass"].values())


def test_update_napcat_removes_legacy_bypass_enabled_from_current_config(
    tmp_path,
) -> None:
    account = {"account_data_dir": str(tmp_path), "qq": "10001"}
    config_path = tmp_path / "config" / "napcat.json"
    config_path.parent.mkdir()
    config_path.write_text(
        json.dumps({"bypass_enabled": True, "keep": "value"}), encoding="utf-8"
    )

    AccountConfigManager().update_account_configs(
        account,
        {"napcat": {"new": "value"}},
        lambda item: item["qq"],
    )

    napcat = json.loads(config_path.read_text())
    assert napcat == {"keep": "value", "new": "value"}

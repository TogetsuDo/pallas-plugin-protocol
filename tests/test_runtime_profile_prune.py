"""全局 runtime 资产保存时的容器清理范围。"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from types import MethodType, SimpleNamespace

import pytest

_ROOT = Path(__file__).resolve().parents[1] / "src" / "pallas_plugin_protocol"
_PACKAGE = types.ModuleType("pallas_plugin_protocol")
_PACKAGE.__path__ = [str(_ROOT)]
sys.modules["pallas_plugin_protocol"] = _PACKAGE

_PALLAS = types.ModuleType("pallas")
_PALLAS.__path__ = []
_PALLAS_API = types.ModuleType("pallas.api")
_PALLAS_API.__path__ = []
_PALLAS_PATHS = types.ModuleType("pallas.api.paths")
_PALLAS_PATHS.resource_dir = lambda: Path("/tmp")
_PALLAS_CONFIG = types.ModuleType("pallas.api.config")
_PALLAS_CONFIG.field_help = lambda title, detail: f"{title}: {detail}"
_PALLAS_CONFIG.install_hot_reload_config = lambda *args, **kwargs: (
    SimpleNamespace(get=lambda: None)
)
_PALLAS_CONFIG.plugin_config_proxy = lambda *args, **kwargs: None
_PALLAS_UTILS = types.ModuleType("pallas.api.utils")
_PALLAS_UTILS.fetch_github_releases = lambda *args, **kwargs: []
_PALLAS_UTILS.github_auth_headers = lambda *args, **kwargs: {}
_PALLAS_UTILS.github_release_api_url = lambda *args, **kwargs: ""
_PALLAS_UTILS.github_release_asset_url = lambda *args, **kwargs: ""
_PALLAS_UTILS.StreamDownloadProgress = dict
_PALLAS_UTILS.format_download_byte_size = lambda value: str(value)
_PALLAS_UTILS.sync_stream_download_to_file = lambda *args, **kwargs: None
sys.modules.update(
    {
        "pallas": _PALLAS,
        "pallas.api": _PALLAS_API,
        "pallas.api.paths": _PALLAS_PATHS,
        "pallas.api.config": _PALLAS_CONFIG,
        "pallas.api.utils": _PALLAS_UTILS,
    }
)

from pallas_plugin_protocol.service import PallasProtocolService  # noqa: E402


class LaunchStub:
    def apply_defaults(self, account: dict, resolve_qq: object) -> None:
        account["_defaults"] = True


class BackendStub:
    def prepare_dirs(self, account: dict) -> None:
        account["_prepare"] = True

    def sync_all_configs(self, account: dict, resolve_qq: object) -> None:
        account["_sync"] = True


def make_profile_service(tmp_path: Path) -> PallasProtocolService:
    napcat = {
        "id": "nc-1",
        "qq": "10001",
        "napcat_linux_docker": True,
        "snowluma_linux_docker": False,
    }
    snow = {
        "id": "sl-1",
        "qq": "20002",
        "napcat_linux_docker": False,
        "snowluma_linux_docker": True,
    }
    profile_path = tmp_path / "runtime_profile.json"
    profile_path.write_text(
        json.dumps(
            {
                "runtime_mode": "docker",
                "napcat_runtime_mode": "docker",
                "snowluma_runtime_mode": "docker",
                "target_platform": "auto",
                "docker_image": "mlikiowa/napcat-docker:v4.8.100",
                "follow_bot_lifecycle": False,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    service = PallasProtocolService.__new__(PallasProtocolService)
    service._accounts = {"nc-1": napcat, "sl-1": snow}
    service._runtime_profile_path = profile_path
    service._config = SimpleNamespace(
        pallas_protocol_linux_use_docker=True,
        pallas_protocol_docker_image="mlikiowa/napcat-docker:v4.8.100",
        pallas_protocol_snowluma_linux_use_docker=True,
        pallas_protocol_follow_bot_lifecycle=False,
    )
    service._launch = LaunchStub()
    service._resolve_qq = lambda item: str(item["qq"])
    service._protocol_runtime_backend = lambda item: BackendStub()
    service._refresh_linux_docker_run_argv = lambda item: item.__setitem__(
        "_argv", True
    )
    service._save_accounts = MethodType(lambda self: None, service)
    service._default_runtime_mode = MethodType(
        lambda self: "docker", service
    )
    service.runtime_profile = MethodType(PallasProtocolService.runtime_profile, service)
    service._apply_runtime_profile_to_config = MethodType(
        PallasProtocolService._apply_runtime_profile_to_config, service
    )
    service._reapply_runtime_profile_launch_settings = MethodType(
        PallasProtocolService._reapply_runtime_profile_launch_settings, service
    )
    service.update_runtime_profile = MethodType(
        PallasProtocolService.update_runtime_profile, service
    )
    service._prune_all_protocol_docker_containers_after_runtime_profile_change = (
        MethodType(
            PallasProtocolService._prune_all_protocol_docker_containers_after_runtime_profile_change,
            service,
        )
    )
    service.stopped = []
    service.removed = []

    async def stop_account(self: PallasProtocolService, account_id: str) -> None:
        self.stopped.append(account_id)

    async def remove_both(self: PallasProtocolService, account: dict) -> None:
        self.removed.append(f"both:{account['id']}")

    async def remove_napcat(self: PallasProtocolService, account: dict) -> None:
        self.removed.append(f"napcat:{account['id']}")

    async def remove_snowluma(self: PallasProtocolService, account: dict) -> None:
        self.removed.append(f"snowluma:{account['id']}")

    service.stop_account = MethodType(stop_account, service)
    service._remove_both_linux_docker_container_names_for_account = MethodType(
        remove_both, service
    )
    service._remove_napcat_linux_docker_container_for_account = MethodType(
        remove_napcat, service
    )
    service._remove_snowluma_linux_docker_container_for_account = MethodType(
        remove_snowluma, service
    )
    return service


@pytest.mark.asyncio
async def test_saving_image_only_does_not_stop_snowluma(tmp_path: Path) -> None:
    service = make_profile_service(tmp_path)

    updated = await service.update_runtime_profile(
        {"docker_image": "mlikiowa/napcat-docker:v4.8.124"}
    )

    assert updated["docker_image"] == "mlikiowa/napcat-docker:v4.8.124"
    assert service.stopped == []
    assert service.removed == []
    assert service._accounts["nc-1"].get("_argv") is True
    assert service._accounts["sl-1"].get("_argv") is True


@pytest.mark.asyncio
async def test_napcat_mode_flip_only_prunes_napcat(tmp_path: Path) -> None:
    service = make_profile_service(tmp_path)

    await service.update_runtime_profile(
        {
            "napcat_runtime_mode": "shell",
            "snowluma_runtime_mode": "docker",
        }
    )

    assert service.stopped == ["nc-1"]
    assert service.removed == ["napcat:nc-1"]

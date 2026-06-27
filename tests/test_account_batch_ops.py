import importlib.util
import sys
import types
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1] / "src" / "pallas_plugin_protocol"
_PKG = "pallas_plugin_protocol_isolated_test"


def load_module(qualified: str, filename: str):
    path = _ROOT / filename
    spec = importlib.util.spec_from_file_location(qualified, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[qualified] = mod
    spec.loader.exec_module(mod)
    return mod


if _PKG not in sys.modules:
    sys.modules[_PKG] = types.ModuleType(_PKG)

batch_mod = load_module(f"{_PKG}.account_batch", "account_batch.py")
batch_ops = load_module(f"{_PKG}.account_batch_ops", "account_batch_ops.py")
BatchMode = batch_mod.BatchMode


def test_resolve_batch_account_ids_deduplicates_and_validates():
    accounts = {"a": {"enabled": True}, "b": {"enabled": False}}
    assert batch_ops.resolve_batch_account_ids(accounts, ["a", "a"]) == ["a"]
    with pytest.raises(KeyError):
        batch_ops.resolve_batch_account_ids(accounts, ["missing"])
    with pytest.raises(ValueError, match="account_ids 为空"):
        batch_ops.resolve_batch_account_ids(accounts, ["", "  "])


def test_resolve_batch_account_ids_defaults_to_enabled():
    accounts = {
        "on": {"enabled": True},
        "off": {"enabled": False},
        "default": {},
    }
    assert batch_ops.resolve_batch_account_ids(accounts, None) == ["on", "default"]
    with pytest.raises(ValueError):
        batch_ops.resolve_batch_account_ids({"x": {"enabled": False}}, None)


def test_batch_defaults_from_config():
    class Cfg:
        pallas_protocol_restart_max_concurrency = 3
        pallas_protocol_restart_stagger_s = 2.5

    defaults = batch_ops.batch_defaults_from_config(Cfg())
    assert defaults["max_concurrency"] == 3
    assert defaults["stagger_ms"] == 2500
    assert defaults["mode"] == BatchMode.ROLLING.value

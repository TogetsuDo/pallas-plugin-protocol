#!/usr/bin/env python3
"""SnowLuma QR capture 本地 E2E 探测（不依赖 Pallas-Bot 启动）。"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace

_ROOT = Path(__file__).resolve().parents[1]
_PKG_ROOT = _ROOT / "src" / "pallas_plugin_protocol"


def load_isolated():
    if "pallas_plugin_protocol" not in sys.modules:
        pkg = types.ModuleType("pallas_plugin_protocol")
        pkg.__path__ = [str(_ROOT / "src" / "pallas_plugin_protocol")]
        sys.modules["pallas_plugin_protocol"] = pkg

    for name, file in (
        ("pallas_plugin_protocol.contract", "contract.py"),
        ("pallas_plugin_protocol.snowluma_docker", "snowluma_docker.py"),
    ):
        if name in sys.modules:
            continue
        spec = importlib.util.spec_from_file_location(name, _PKG_ROOT / file)
        assert spec and spec.loader
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)

    spec = importlib.util.spec_from_file_location(
        "pallas_plugin_protocol.snowluma_qr_capture",
        _PKG_ROOT / "snowluma_qr_capture.py",
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


qr_capture = load_isolated()


def main() -> int:
    parser = argparse.ArgumentParser(description="SnowLuma QR capture E2E probe")
    parser.add_argument("--account-id", default="qrtest")
    parser.add_argument("--account-data-dir", required=True)
    parser.add_argument("--screen-only", action="store_true", help="只测截屏，不识别")
    args = parser.parse_args()

    account_data_dir = Path(args.account_data_dir).resolve()
    account = {
        "id": args.account_id,
        "protocol_backend": "snowluma",
        "snowluma_linux_docker": True,
        "account_data_dir": str(account_data_dir),
    }
    config = SimpleNamespace(
        pallas_protocol_snowluma_qr_capture_display=":1",
        pallas_protocol_snowluma_qr_capture_initial_delay_s=8.0,
    )

    print(
        "account_uses_snowluma_docker:",
        qr_capture.account_uses_snowluma_docker(account),
    )
    print("container:", qr_capture.snowluma_docker_container_name(account))

    screen = qr_capture.capture_screen_png_from_container(
        qr_capture.snowluma_docker_container_name(account),
        display=config.pallas_protocol_snowluma_qr_capture_display,
    )
    if screen is None:
        print("RESULT: screen_capture=FAIL (import/scrot/xwd 均未产出 PNG)")
        return 2

    out_screen = account_data_dir / "cache" / "e2e-screen.png"
    out_screen.parent.mkdir(parents=True, exist_ok=True)
    out_screen.write_bytes(screen)
    print(f"RESULT: screen_capture=OK bytes={len(screen)} path={out_screen}")

    if args.screen_only:
        return 0

    qr = qr_capture.extract_qr_png_from_screen(screen)
    if qr is None:
        print("RESULT: qr_decode=FAIL (截屏成功但未识别到 QR)")
        return 3

    out_qr = account_data_dir / "cache" / "qrcode.png"
    out_qr.write_bytes(qr)
    print(f"RESULT: qr_decode=OK bytes={len(qr)} path={out_qr}")

    captured = qr_capture.capture_snowluma_qrcode_once(account, config=config)
    print(
        "capture_snowluma_qrcode_once:",
        json.dumps(
            {
                "ok": captured is not None,
                "path": str(captured) if captured else None,
            },
            ensure_ascii=False,
        ),
    )
    return 0 if captured else 4


if __name__ == "__main__":
    raise SystemExit(main())

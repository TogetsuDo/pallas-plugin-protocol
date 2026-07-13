"""SnowLuma QR 截屏识别单元测试。"""

from __future__ import annotations

import importlib.util
import io
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from PIL import Image

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

snowluma_docker_stub = types.ModuleType("pallas_plugin_protocol.snowluma_docker")
snowluma_docker_stub.snowluma_docker_container_name = lambda account: (
    f"pallas-proto-sl-{account.get('id', 'x')}"
)
sys.modules["pallas_plugin_protocol.snowluma_docker"] = snowluma_docker_stub

qr_capture = load_module(
    "pallas_plugin_protocol.snowluma_qr_capture", "snowluma_qr_capture.py"
)
account_uses_snowluma_docker = qr_capture.account_uses_snowluma_docker
capture_snowluma_qrcode_once = qr_capture.capture_snowluma_qrcode_once
extract_qr_png_from_screen = qr_capture.extract_qr_png_from_screen
write_qrcode_cache = qr_capture.write_qrcode_cache


def test_account_uses_snowluma_docker() -> None:
    assert account_uses_snowluma_docker(
        {"protocol_backend": "snowluma", "snowluma_linux_docker": True}
    )
    assert not account_uses_snowluma_docker(
        {"protocol_backend": "napcat", "snowluma_linux_docker": True}
    )
    assert not account_uses_snowluma_docker(
        {"protocol_backend": "snowluma", "snowluma_linux_docker": False}
    )


def test_extract_qr_png_from_screen_with_mock_decode() -> None:
    base = Image.new("RGB", (400, 300), color=(30, 30, 30))
    buf = io.BytesIO()
    base.save(buf, format="PNG")
    screen = buf.getvalue()

    class FakeCode:
        rect = SimpleNamespace(left=100, top=80, width=120, height=120)

    fake_pyzbar_inner = types.ModuleType("pyzbar.pyzbar")
    fake_pyzbar_inner.decode = lambda img: [FakeCode()]
    fake_pyzbar = types.ModuleType("pyzbar")
    fake_pyzbar.pyzbar = fake_pyzbar_inner

    with patch.dict(
        sys.modules,
        {"pyzbar": fake_pyzbar, "pyzbar.pyzbar": fake_pyzbar_inner},
    ):
        out = extract_qr_png_from_screen(screen)
    assert out is not None
    img = Image.open(io.BytesIO(out))
    assert img.width >= 120
    assert img.height >= 120


def test_capture_snowluma_qrcode_once_writes_cache(tmp_path: Path) -> None:
    ad = tmp_path / "inst" / "snowluma"
    ad.mkdir(parents=True)
    account = {
        "id": "acc1",
        "protocol_backend": "snowluma",
        "snowluma_linux_docker": True,
        "account_data_dir": str(ad),
    }
    fake_screen = io.BytesIO()
    Image.new("RGB", (640, 480), color=(20, 20, 20)).save(fake_screen, format="PNG")
    fake_qr = b"fake-qr-png"

    def fake_exec(container: str, cmd_tail: list[str], *, display: str) -> int:
        assert container == "pallas-proto-sl-acc1"
        assert display == ":1"
        assert cmd_tail[0] == "import"
        return 0

    def fake_cp(container: str, remote: str) -> bytes | None:
        return fake_screen.getvalue()

    with patch.object(qr_capture, "extract_qr_png_from_screen", return_value=fake_qr):
        out = capture_snowluma_qrcode_once(
            account,
            run_exec=fake_exec,
            run_cp=fake_cp,
        )
    assert out is not None
    assert out == ad / "cache" / "qrcode.png"
    assert out.read_bytes() == fake_qr


def test_write_qrcode_cache(tmp_path: Path) -> None:
    ad = tmp_path / "data"
    path = write_qrcode_cache(ad, b"\x89PNG")
    assert path.is_file()
    assert path.parent.name == "cache"


def test_capture_screen_png_from_xwd_fallback() -> None:
    fake_png = b"\x89PNG-xwd-fallback"

    def fake_exec(container: str, cmd_tail: list[str], *, display: str) -> int:
        assert container == "pallas-proto-sl-acc2"
        if cmd_tail[0] in {"import", "scrot"}:
            return 1
        assert cmd_tail[:3] == ["xwd", "-root", "-silent"]
        return 0

    def fake_cp(container: str, remote: str) -> bytes | None:
        assert remote.endswith(".xwd")
        return b"fake-xwd"

    def fake_convert(xwd: bytes) -> bytes | None:
        assert xwd == b"fake-xwd"
        return fake_png

    out = qr_capture.capture_screen_png_from_container(
        "pallas-proto-sl-acc2",
        run_exec=fake_exec,
        run_cp=fake_cp,
        xwd_to_png=fake_convert,
    )
    assert out == fake_png

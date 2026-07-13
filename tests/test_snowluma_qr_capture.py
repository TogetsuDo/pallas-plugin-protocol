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
find_qq_login_window = qr_capture.find_qq_login_window
is_valid_qq_login_qr_payload = qr_capture.is_valid_qq_login_qr_payload
write_qrcode_cache = qr_capture.write_qrcode_cache
qrcode_cache_looks_valid = qr_capture.qrcode_cache_looks_valid


def test_is_valid_qq_login_qr_payload() -> None:
    assert is_valid_qq_login_qr_payload(b"https://txz.qq.com/p?k=abc&f=1600001615")
    assert not is_valid_qq_login_qr_payload(b"https://example.com/")
    assert not is_valid_qq_login_qr_payload(b"not-a-url")


def test_find_qq_login_window() -> None:
    tree = """
     0xa00001 "qq": ("qq" "Qq")  10x10+10+10  +10+10
        0x800003 "QQ": ("qq" "QQ")  320x460+0+0  +800+300
        0x600032 "xmessage": ("xmessage" "Xmessage")  578x96+0+19  +671+500
    """
    found = find_qq_login_window(tree)
    assert found == ("0x800003", 320, 460)


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
        data = b"https://txz.qq.com/p?k=test&f=1"

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

    def fake_window_tree(*_a, **_k) -> str:
        return '     0x800003 "QQ": ("qq" "QQ")  320x460+0+0  +800+300'

    with (
        patch.object(
            qr_capture,
            "capture_screen_png_from_container",
            return_value=fake_screen.getvalue(),
        ),
        patch.object(qr_capture, "extract_qr_png_from_screen", return_value=fake_qr),
        patch.object(qr_capture, "click_qq_login_window", return_value=True),
    ):
        out = capture_snowluma_qrcode_once(
            account,
            run_exec_text=fake_window_tree,
        )
    assert out is not None
    assert out == ad / "cache" / "qrcode.png"
    assert out.read_bytes() == fake_qr


def test_capture_snowluma_qrcode_once_skips_invalid_screen(tmp_path: Path) -> None:
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

    def fake_window_tree(*_a, **_k) -> str:
        return '     0x800003 "QQ": ("qq" "QQ")  320x460+0+0  +800+300'

    with (
        patch.object(
            qr_capture,
            "capture_screen_png_from_container",
            return_value=fake_screen.getvalue(),
        ),
        patch.object(qr_capture, "extract_qr_png_from_screen", return_value=None),
        patch.object(qr_capture, "click_qq_login_window", return_value=True),
    ):
        out = capture_snowluma_qrcode_once(
            account,
            run_exec_text=fake_window_tree,
        )
    assert out is None
    assert not (ad / "cache" / "qrcode.png").exists()


def test_restore_snowluma_qq_login_quick_login(tmp_path: Path) -> None:
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
    click_calls: list[str] = []

    def fake_exec(container: str, cmd_tail: list[str], *, display: str) -> int:
        if cmd_tail[:2] == ["sh", "-c"] and "click 1" in cmd_tail[2]:
            click_calls.append(cmd_tail[2])
        return 0

    def fake_cp(container: str, remote: str) -> bytes | None:
        return fake_screen.getvalue()

    def fake_window_tree(container: str, cmd_tail: list[str], *, display: str) -> str:
        if cmd_tail[0] == "sh":
            return "/usr/bin/xdotool"
        return '     0x800003 "QQ": ("qq" "QQ")  320x460+0+0  +800+300'

    with (
        patch.object(
            qr_capture,
            "capture_screen_png_from_container",
            return_value=fake_screen.getvalue(),
        ),
        patch.object(qr_capture, "extract_qr_png_from_screen", return_value=None),
        patch.object(qr_capture, "ensure_container_xdotool", return_value=True),
        patch.object(qr_capture, "_command_available_in_container", return_value=True),
    ):
        out = qr_capture.restore_snowluma_qq_login(
            account,
            run_exec=fake_exec,
            run_exec_text=fake_window_tree,
            run_exec_root=lambda *a, **k: 0,
        )
    assert out["mode"] == "quick_login"
    assert click_calls
    assert "mousemove" in click_calls[-1]
    assert "click 1" in click_calls[-1]


def test_write_qrcode_cache(tmp_path: Path) -> None:
    ad = tmp_path / "data"
    path = write_qrcode_cache(ad, b"\x89PNG")
    assert path.is_file()
    assert path.parent.name == "cache"


def test_capture_screen_png_from_window_id() -> None:
    fake_png = b"\x89PNG-window"

    def fake_exec(container: str, cmd_tail: list[str], *, display: str) -> int:
        assert container == "pallas-proto-sl-acc3"
        if cmd_tail[:3] == ["xwd", "-id", "0x800003"]:
            return 0
        return 1

    def fake_cp(container: str, remote: str) -> bytes | None:
        return b"fake-xwd"

    def fake_convert(xwd: bytes) -> bytes | None:
        return fake_png

    out = qr_capture.capture_screen_png_from_container(
        "pallas-proto-sl-acc3",
        window_id="0x800003",
        run_exec=fake_exec,
        run_cp=fake_cp,
        xwd_to_png=fake_convert,
    )
    assert out == fake_png


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

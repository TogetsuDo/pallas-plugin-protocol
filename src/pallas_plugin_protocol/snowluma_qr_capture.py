"""SnowLuma Docker：从容器 X11 桌面截屏并识别 QQ 登录二维码。"""

from __future__ import annotations

import asyncio
import io
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from .contract import ACCOUNT_PROTOCOL_BACKEND_KEY, SNOWLUMA_PROTOCOL_BACKEND
from .snowluma_docker import snowluma_docker_container_name

logger = logging.getLogger(__name__)

DEFAULT_DISPLAY = ":1"
REMOTE_CAPTURE_PATH = "/tmp/pallas-qr-capture.png"
REMOTE_XWD_PATH = "/tmp/pallas-qr-capture.xwd"
INITIAL_DELAY_SEC = 8.0
POLL_INTERVAL_SEC = 2.0


def account_qrcode_cache_path(account_data_dir: Path) -> Path:
    return account_data_dir / "cache" / "qrcode.png"


def account_uses_snowluma_docker(account: dict) -> bool:
    bk = str(account.get(ACCOUNT_PROTOCOL_BACKEND_KEY) or "napcat").strip().lower()
    return bk == SNOWLUMA_PROTOCOL_BACKEND and bool(
        account.get("snowluma_linux_docker")
    )


def snowluma_qr_capture_display(config: Any | None) -> str:
    raw = str(
        getattr(config, "pallas_protocol_snowluma_qr_capture_display", DEFAULT_DISPLAY)
        or DEFAULT_DISPLAY
    ).strip()
    return raw or DEFAULT_DISPLAY


def snowluma_qr_capture_initial_delay(config: Any | None) -> float:
    if config is None:
        return INITIAL_DELAY_SEC
    try:
        raw = getattr(
            config, "pallas_protocol_snowluma_qr_capture_initial_delay_s", None
        )
        if raw is None:
            return INITIAL_DELAY_SEC
        return float(raw)
    except (TypeError, ValueError):
        return INITIAL_DELAY_SEC


def capture_screen_png_from_container(
    container_name: str,
    *,
    display: str = DEFAULT_DISPLAY,
    run_exec: Any | None = None,
    run_cp: Any | None = None,
    xwd_to_png: Any | None = None,
) -> bytes | None:
    """在 SnowLuma 容器内截屏，返回 PNG 字节。"""
    exec_runner = run_exec or _docker_exec
    cp_runner = run_cp or _docker_cp_out
    convert_runner = xwd_to_png or _xwd_bytes_to_png
    capture_cmds = (
        ["import", "-window", "root", REMOTE_CAPTURE_PATH],
        ["scrot", REMOTE_CAPTURE_PATH],
    )
    for tail in capture_cmds:
        rc = exec_runner(
            container_name,
            tail,
            display=display,
        )
        if rc != 0:
            continue
        data = cp_runner(container_name, REMOTE_CAPTURE_PATH)
        if data:
            return data

    rc = exec_runner(
        container_name,
        ["xwd", "-root", "-silent", "-out", REMOTE_XWD_PATH],
        display=display,
    )
    if rc != 0:
        return None
    xwd_data = cp_runner(container_name, REMOTE_XWD_PATH)
    if not xwd_data:
        return None
    return convert_runner(xwd_data)


def _xwd_bytes_to_png(xwd_bytes: bytes) -> bytes | None:
    """宿主机 ImageMagick 将 XWD 转为 PNG（SnowLuma 镜像通常仅有 xwd）。"""
    for argv in (
        ["convert", "xwd:-", "png:-"],
        ["magick", "xwd:-", "png:-"],
    ):
        try:
            proc = subprocess.run(
                argv,
                input=xwd_bytes,
                capture_output=True,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as err:
            logger.debug("SnowLuma XWD 转 PNG 失败 {}: {}", argv[0], err)
            continue
        if proc.returncode == 0 and proc.stdout:
            return proc.stdout
        stderr = (proc.stderr or b"").decode("utf-8", errors="replace").strip()
        if stderr:
            logger.debug("SnowLuma XWD 转 PNG {}: {}", argv[0], stderr)
    return None


def extract_qr_png_from_screen(png_bytes: bytes) -> bytes | None:
    """从整屏截图中检测 QR 并裁切为 PNG。"""
    try:
        from PIL import Image
    except ImportError:
        logger.warning(
            "SnowLuma QR capture 需要 pillow，请安装 pallas-plugin-protocol 依赖"
        )
        return None

    try:
        from pyzbar.pyzbar import decode as pyzbar_decode
    except ImportError:
        logger.warning(
            "SnowLuma QR capture 需要 pyzbar（及系统 libzbar），无法识别二维码"
        )
        return None

    img = Image.open(io.BytesIO(png_bytes))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    codes = pyzbar_decode(img)
    if not codes:
        gray = img.convert("L")
        codes = pyzbar_decode(gray)
    if not codes:
        return None

    code = codes[0]
    rect = code.rect
    pad = max(8, min(rect.width, rect.height) // 8)
    left = max(0, rect.left - pad)
    top = max(0, rect.top - pad)
    right = min(img.width, rect.left + rect.width + pad)
    bottom = min(img.height, rect.top + rect.height + pad)
    crop = img.crop((left, top, right, bottom))
    buf = io.BytesIO()
    crop.save(buf, format="PNG")
    return buf.getvalue()


def write_qrcode_cache(account_data_dir: Path, png_bytes: bytes) -> Path:
    cache_dir = account_data_dir / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    out = account_qrcode_cache_path(account_data_dir)
    out.write_bytes(png_bytes)
    return out


def capture_snowluma_qrcode_once(
    account: dict,
    *,
    config: Any | None = None,
    run_exec: Any | None = None,
    run_cp: Any | None = None,
) -> Path | None:
    if not account_uses_snowluma_docker(account):
        return None
    account_data_dir = Path(str(account.get("account_data_dir", "")).strip())
    if not account_data_dir:
        return None

    container = snowluma_docker_container_name(account)
    display = snowluma_qr_capture_display(config)
    screen = capture_screen_png_from_container(
        container,
        display=display,
        run_exec=run_exec,
        run_cp=run_cp,
    )
    if not screen:
        return None

    qr_png = extract_qr_png_from_screen(screen)
    if not qr_png:
        logger.debug("SnowLuma 截屏未识别到 QR: container={}", container)
        return None
    return write_qrcode_cache(account_data_dir, qr_png)


async def wait_and_capture_snowluma_qrcode(
    account: dict,
    since: datetime,
    *,
    config: Any | None = None,
    timeout_sec: int = 60,
    initial_delay_sec: float | None = None,
    poll_interval_sec: float = POLL_INTERVAL_SEC,
) -> Path | None:
    """重启后轮询截屏，直到写出新的 cache/qrcode.png 或超时。"""
    account_data_dir = Path(str(account.get("account_data_dir", "")).strip())
    if not account_data_dir:
        return None

    delay = (
        initial_delay_sec
        if initial_delay_sec is not None
        else snowluma_qr_capture_initial_delay(config)
    )
    if delay > 0:
        await asyncio.sleep(delay)

    deadline = asyncio.get_running_loop().time() + timeout_sec
    last_payload: bytes | None = None
    while asyncio.get_running_loop().time() < deadline:
        captured = await asyncio.to_thread(
            capture_snowluma_qrcode_once,
            account,
            config=config,
        )
        if captured is not None and captured.is_file():
            try:
                mtime = datetime.fromtimestamp(
                    captured.stat().st_mtime, tz=since.tzinfo
                )
                payload = captured.read_bytes()
                if mtime >= since and payload and payload != last_payload:
                    return captured
                last_payload = payload
            except OSError:
                pass
        await asyncio.sleep(poll_interval_sec)
    return None


def _docker_exec(container_name: str, cmd_tail: list[str], *, display: str) -> int:
    argv = [
        "docker",
        "exec",
        "-u",
        "snowluma",
        "-e",
        f"DISPLAY={display}",
        container_name,
        *cmd_tail,
    ]
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as err:
        logger.debug("SnowLuma docker exec 截屏失败: {}", err)
        return 1
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        if stderr:
            logger.debug("SnowLuma docker exec {}: {}", cmd_tail[0], stderr)
        return int(proc.returncode)
    return 0


def _docker_cp_out(container_name: str, remote_path: str) -> bytes | None:
    """读取容器内文件字节。不用 ``docker cp … -``（stdout 为 tar 包）。"""
    try:
        proc = subprocess.run(
            ["docker", "exec", container_name, "cat", remote_path],
            capture_output=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as err:
        logger.debug("SnowLuma docker exec cat 失败: {}", err)
        return None
    if proc.returncode != 0 or not proc.stdout:
        stderr = (proc.stderr or b"").decode("utf-8", errors="replace").strip()
        if stderr:
            logger.debug("SnowLuma docker exec cat {}: {}", remote_path, stderr)
        return None
    return proc.stdout

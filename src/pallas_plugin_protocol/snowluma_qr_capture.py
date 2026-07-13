"""SnowLuma Docker：从容器 X11 桌面截屏并识别 QQ 登录二维码。"""

from __future__ import annotations

import asyncio
import io
import logging
import re
import subprocess
import time
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
REFRESH_SETTLE_SEC = 3.5

QQ_LOGIN_WINDOW_RE = re.compile(
    r'\s+(0x[0-9a-f]+)\s+"QQ":\s+\([^)]+\)\s+(\d+)x(\d+)\+',
    re.IGNORECASE,
)
XMESSAGE_WINDOW_RE = re.compile(
    r'\s+(0x[0-9a-f]+)\s+"xmessage":',
    re.IGNORECASE,
)
QQ_LOGIN_QR_HOST_MARKERS = ("qq.com", "q.qq.com", "txz.qq.com")


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


def is_valid_qq_login_qr_payload(data: bytes) -> bool:
    try:
        text = data.decode("utf-8", errors="ignore").strip().lower()
    except (TypeError, ValueError, AttributeError):
        return False
    if not text.startswith("http"):
        return False
    return any(marker in text for marker in QQ_LOGIN_QR_HOST_MARKERS)


def find_qq_login_window(
    tree_text: str,
) -> tuple[str, int, int] | None:
    """从 ``xwininfo -root -tree`` 输出中定位 QQ 扫码登录窗（约 320×460）。"""
    best: tuple[str, int, int, int] | None = None
    for match in QQ_LOGIN_WINDOW_RE.finditer(tree_text):
        window_id = match.group(1)
        width = int(match.group(2))
        height = int(match.group(3))
        if width < 200 or width > 520 or height < 300 or height > 620:
            continue
        area = width * height
        if best is None or area < best[3]:
            best = (window_id, width, height, area)
    if best is None:
        return None
    return best[0], best[1], best[2]


def list_xmessage_window_ids(tree_text: str) -> list[str]:
    return [match.group(1) for match in XMESSAGE_WINDOW_RE.finditer(tree_text)]


def prepare_qq_login_for_capture(
    container_name: str,
    *,
    display: str = DEFAULT_DISPLAY,
    run_exec: Any | None = None,
    run_exec_text: Any | None = None,
    run_exec_root: Any | None = None,
) -> tuple[str, int, int] | None:
    """关闭 xmessage 遮挡并尝试刷新 QQ 登录二维码。"""
    exec_runner = run_exec or _docker_exec
    text_runner = run_exec_text or _docker_exec_text
    root_runner = run_exec_root or _docker_exec_root
    tree = text_runner(
        container_name,
        ["xwininfo", "-root", "-tree"],
        display=display,
    )
    if not tree:
        return None

    for window_id in list_xmessage_window_ids(tree):
        exec_runner(container_name, ["xkill", "-id", window_id], display=display)

    login = find_qq_login_window(tree)
    if login is None:
        return None

    window_id, width, height = login
    if not _command_available_in_container(
        container_name, "xdotool", display=display, run_exec_text=text_runner
    ):
        ensure_container_xdotool(
            container_name,
            display=display,
            run_exec_text=text_runner,
            run_exec_root=root_runner,
        )
    if _command_available_in_container(
        container_name, "xdotool", display=display, run_exec_text=text_runner
    ):
        click_x = max(1, int(width * 0.5))
        click_y = max(1, int(height * 0.62))
        script = (
            f"xdotool windowactivate --sync {window_id} && "
            f"xdotool mousemove --window {window_id} {click_x} {click_y} click 1 && "
            f"sleep 1.5 && "
            f"xdotool mousemove --window {window_id} {click_x} {click_y} click 1"
        )
        exec_runner(container_name, ["sh", "-c", script], display=display)
        time.sleep(REFRESH_SETTLE_SEC)
    else:
        logger.info(
            "SnowLuma 容器 {} 未安装 xdotool，无法自动点击「刷新」；"
            "若二维码已过期请重启账号或在镜像中预装 xdotool",
            container_name,
        )
    return login


def ensure_container_xdotool(
    container_name: str,
    *,
    display: str,
    run_exec_text: Any,
    run_exec_root: Any,
) -> bool:
    """容器内一次性安装 xdotool（SnowLuma 默认镜像未带，过期二维码需点「刷新」）。"""
    marker = "/tmp/.pallas-xdotool-ready"
    if run_exec_root(container_name, ["test", "-f", marker]) == 0:
        return _command_available_in_container(
            container_name, "xdotool", display=display, run_exec_text=run_exec_text
        )
    logger.info("SnowLuma 容器 {} 正在安装 xdotool（一次性）…", container_name)
    install_rc = run_exec_root(
        container_name,
        [
            "sh",
            "-c",
            "export DEBIAN_FRONTEND=noninteractive && "
            "apt-get update -qq && apt-get install -y -qq xdotool && "
            f"touch {marker}",
        ],
    )
    if install_rc != 0:
        logger.warning("SnowLuma 容器 {} 安装 xdotool 失败", container_name)
        return False
    return _command_available_in_container(
        container_name, "xdotool", display=display, run_exec_text=run_exec_text
    )


def capture_screen_png_from_container(
    container_name: str,
    *,
    display: str = DEFAULT_DISPLAY,
    window_id: str | None = None,
    run_exec: Any | None = None,
    run_cp: Any | None = None,
    xwd_to_png: Any | None = None,
) -> bytes | None:
    """在 SnowLuma 容器内截屏，返回 PNG 字节。优先截取 QQ 登录窗。"""
    exec_runner = run_exec or _docker_exec
    cp_runner = run_cp or _docker_cp_out
    convert_runner = xwd_to_png or _xwd_bytes_to_png

    if window_id:
        rc = exec_runner(
            container_name,
            ["xwd", "-id", window_id, "-silent", "-out", REMOTE_XWD_PATH],
            display=display,
        )
        if rc == 0:
            xwd_data = cp_runner(container_name, REMOTE_XWD_PATH)
            if xwd_data:
                png = convert_runner(xwd_data)
                if png:
                    return png

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


def decode_qr_codes_from_image(img: Any) -> list[tuple[Any, int]]:
    """pyzbar 解码；小图（QQ 登录窗 ~320px）放大后再试。返回 (code, scale)。"""
    from PIL import Image
    from pyzbar.pyzbar import decode as pyzbar_decode

    attempts: list[tuple[Any, int]] = [(img, 1), (img.convert("L"), 1)]
    if max(img.width, img.height) < 640:
        scale = 3
        enlarged = img.resize(
            (img.width * scale, img.height * scale),
            Image.Resampling.LANCZOS,
        )
        attempts.extend(((enlarged, scale), (enlarged.convert("L"), scale)))
    for candidate, scale in attempts:
        codes = pyzbar_decode(candidate)
        if codes:
            return [(code, scale) for code in codes]
    return []


def extract_qr_png_from_screen(png_bytes: bytes) -> bytes | None:
    """从截图中检测 QQ 登录 QR 并裁切为 PNG（须为可扫码的 txz.qq.com 链接）。"""
    try:
        from PIL import Image
    except ImportError:
        logger.warning(
            "SnowLuma QR capture 需要 pillow，请安装 pallas-plugin-protocol 依赖"
        )
        return None

    try:
        from pyzbar.pyzbar import decode as pyzbar_decode  # noqa: F401
    except ImportError:
        logger.warning(
            "SnowLuma QR capture 需要 pyzbar（及系统 libzbar），无法识别二维码"
        )
        return None

    img = Image.open(io.BytesIO(png_bytes))
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    codes = decode_qr_codes_from_image(img)
    if not codes:
        return None

    for code, scale in codes:
        if not is_valid_qq_login_qr_payload(code.data):
            continue
        rect = code.rect
        if scale > 1:
            rect = rect.__class__(
                left=rect.left // scale,
                top=rect.top // scale,
                width=max(1, rect.width // scale),
                height=max(1, rect.height // scale),
            )
        pad = max(8, min(rect.width, rect.height) // 8)
        left = max(0, rect.left - pad)
        top = max(0, rect.top - pad)
        right = min(img.width, rect.left + rect.width + pad)
        bottom = min(img.height, rect.top + rect.height + pad)
        crop = img.crop((left, top, right, bottom))
        buf = io.BytesIO()
        crop.save(buf, format="PNG")
        return buf.getvalue()
    return None


def qrcode_cache_looks_valid(path: Path) -> bool:
    """已有 cache/qrcode.png 是否仍可扫码（过滤历史整屏回退）。"""
    try:
        payload = path.read_bytes()
    except OSError:
        return False
    if not payload:
        return False
    return extract_qr_png_from_screen(payload) is not None


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
    run_exec_text: Any | None = None,
) -> Path | None:
    if not account_uses_snowluma_docker(account):
        return None
    account_data_dir = Path(str(account.get("account_data_dir", "")).strip())
    if not account_data_dir:
        return None

    container = snowluma_docker_container_name(account)
    display = snowluma_qr_capture_display(config)
    login = prepare_qq_login_for_capture(
        container,
        display=display,
        run_exec=run_exec,
        run_exec_text=run_exec_text,
    )
    window_id = login[0] if login else None
    screen = capture_screen_png_from_container(
        container,
        display=display,
        window_id=window_id,
        run_exec=run_exec,
        run_cp=run_cp,
    )
    if not screen:
        return None

    qr_png = extract_qr_png_from_screen(screen)
    if not qr_png:
        logger.debug(
            "SnowLuma 截屏未识别到有效 QQ 登录二维码（可能仍在加载或已过期）: container={}",
            container,
        )
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


def _command_available_in_container(
    container_name: str,
    command: str,
    *,
    display: str,
    run_exec_text: Any,
) -> bool:
    path = run_exec_text(
        container_name,
        ["sh", "-c", f"command -v {command}"],
        display=display,
    )
    return bool(path and path.strip())


def _docker_exec_root(container_name: str, cmd_tail: list[str]) -> int:
    argv = ["docker", "exec", "-u", "root", container_name, *cmd_tail]
    try:
        proc = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as err:
        logger.debug("SnowLuma docker exec(root) 失败: {}", err)
        return 1
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        if stderr:
            logger.debug("SnowLuma docker exec(root) {}: {}", cmd_tail[0], stderr)
        return int(proc.returncode)
    return 0


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


def _docker_exec_text(container_name: str, cmd_tail: list[str], *, display: str) -> str:
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
        logger.debug("SnowLuma docker exec 失败: {}", err)
        return ""
    if proc.returncode != 0:
        stderr = (proc.stderr or "").strip()
        if stderr:
            logger.debug("SnowLuma docker exec {}: {}", cmd_tail[0], stderr)
        return ""
    return proc.stdout or ""


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

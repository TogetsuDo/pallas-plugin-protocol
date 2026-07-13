"""SnowLuma 生产环境宿主机依赖探测（QR 截屏链路等）。"""

from __future__ import annotations

import importlib.util
import logging
import shutil
import subprocess
from typing import Any

logger = logging.getLogger(__name__)

_HOST_DEPS_LOGGED = False


def imagemagick_convert_available() -> bool:
    for name in ("convert", "magick"):
        if not shutil.which(name):
            continue
        try:
            proc = subprocess.run(
                [name, "-version"],
                capture_output=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            continue
        if proc.returncode == 0:
            return True
    return False


def libzbar_shared_library_available() -> bool:
    spec = importlib.util.find_spec("pyzbar.pyzbar")
    if spec is None:
        return False
    try:
        from pyzbar.pyzbar import zbar_version
    except ImportError:
        return False
    try:
        zbar_version()
    except (ImportError, OSError, FileNotFoundError):
        return False
    return True


def pillow_available() -> bool:
    return importlib.util.find_spec("PIL") is not None


def pyzbar_available() -> bool:
    return importlib.util.find_spec("pyzbar") is not None


def audit_snowluma_qr_capture_host_deps() -> list[str]:
    """返回缺失或不可用的宿主机依赖说明（空列表表示 QR 截屏链路可用）。"""
    issues: list[str] = []
    if not pillow_available():
        issues.append("Python 包 pillow 未安装")
    if not pyzbar_available():
        issues.append("Python 包 pyzbar 未安装")
    elif not libzbar_shared_library_available():
        issues.append("系统库 libzbar 不可用（pyzbar 无法加载）")
    if not imagemagick_convert_available():
        issues.append(
            "宿主机未找到 ImageMagick convert/magick（SnowLuma 镜像无 import/scrot 时 QR 截屏依赖 xwd→convert）"
        )
    return issues


def snowluma_qr_capture_host_ready() -> bool:
    return not audit_snowluma_qr_capture_host_deps()


def log_snowluma_host_deps_once(config: Any | None = None) -> list[str]:
    """Hub 启动时记录一次宿主机依赖审计结果。"""
    global _HOST_DEPS_LOGGED
    _ = config
    issues = audit_snowluma_qr_capture_host_deps()
    if _HOST_DEPS_LOGGED:
        return issues
    _HOST_DEPS_LOGGED = True
    if issues:
        logger.warning(
            "SnowLuma QR 截屏宿主机依赖未就绪：{}",
            "；".join(issues),
        )
    else:
        logger.info("SnowLuma QR 截屏宿主机依赖检查通过")
    return issues


def host_deps_report() -> dict[str, object]:
    issues = audit_snowluma_qr_capture_host_deps()
    return {
        "qr_capture_ready": not issues,
        "issues": issues,
        "pillow": pillow_available(),
        "pyzbar": pyzbar_available(),
        "libzbar": libzbar_shared_library_available(),
        "imagemagick": imagemagick_convert_available(),
    }

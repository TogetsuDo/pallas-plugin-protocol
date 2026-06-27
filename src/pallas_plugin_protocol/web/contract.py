"""web 层约定 re-export（pages_pkg 通过 ``..contract`` 引用包级 contract）。"""

from __future__ import annotations

from ..contract import resolve_public_mount_path

__all__ = ["resolve_public_mount_path"]

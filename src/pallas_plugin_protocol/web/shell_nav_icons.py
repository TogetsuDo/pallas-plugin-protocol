"""控制台侧栏 SVG 图标（与 Pallas-Bot-WebUI consoleNavIcons 对齐）。"""

from __future__ import annotations

from html import escape as html_escape
from typing import Literal, TypedDict

IconKind = Literal["path", "rect", "circle", "line", "polyline"]


class IconNode(TypedDict, total=False):
    kind: IconKind
    d: str
    x: float
    y: float
    width: float
    height: float
    rx: float
    cx: float
    cy: float
    r: float
    x1: float
    y1: float
    x2: float
    y2: float
    points: str


ConsoleNavIconId = Literal[
    "dashboard",
    "account",
    "download",
    "blocks",
    "settings",
    "globe",
    "default",
]

_NAV_ICON_NODES: dict[ConsoleNavIconId, list[IconNode]] = {
    "dashboard": [
        {"kind": "rect", "x": 3, "y": 3, "width": 7, "height": 9, "rx": 1},
        {"kind": "rect", "x": 14, "y": 3, "width": 7, "height": 5, "rx": 1},
        {"kind": "rect", "x": 14, "y": 12, "width": 7, "height": 9, "rx": 1},
        {"kind": "rect", "x": 3, "y": 16, "width": 7, "height": 5, "rx": 1},
    ],
    "account": [
        {"kind": "circle", "cx": 12, "cy": 12, "r": 10},
        {"kind": "circle", "cx": 12, "cy": 10, "r": 3},
        {"kind": "path", "d": "M7 20.662V19a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v1.662"},
    ],
    "download": [
        {"kind": "path", "d": "M12 15V3"},
        {"kind": "path", "d": "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"},
        {"kind": "path", "d": "m7 10 5 5 5-5"},
    ],
    "blocks": [
        {"kind": "rect", "x": 3, "y": 3, "width": 7, "height": 7, "rx": 1},
        {"kind": "rect", "x": 14, "y": 3, "width": 7, "height": 7, "rx": 1},
        {"kind": "rect", "x": 3, "y": 14, "width": 7, "height": 7, "rx": 1},
        {"kind": "path", "d": "M14 14h.01"},
        {"kind": "path", "d": "M17 14h.01"},
        {"kind": "path", "d": "M14 17h.01"},
        {"kind": "path", "d": "M17 17h.01"},
    ],
    "settings": [
        {
            "kind": "path",
            "d": "M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915",
        },
        {"kind": "circle", "cx": 12, "cy": 12, "r": 3},
    ],
    "globe": [
        {"kind": "circle", "cx": 12, "cy": 12, "r": 10},
        {"kind": "path", "d": "M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20"},
        {"kind": "path", "d": "M2 12h20"},
    ],
    "default": [
        {"kind": "circle", "cx": 12, "cy": 12, "r": 10},
    ],
}


def render_console_nav_icon(icon_id: str, *, size: int = 16) -> str:
    """输出与 WebUI ``ConsoleNavIcon`` 一致的 inline SVG。"""
    nodes = _NAV_ICON_NODES.get(icon_id, _NAV_ICON_NODES["default"])  # type: ignore[arg-type]
    parts: list[str] = []
    for node in nodes:
        kind = node["kind"]
        if kind == "path":
            parts.append(f'<path d="{html_escape(node["d"], quote=True)}" />')
        elif kind == "rect":
            rx = f' rx="{node["rx"]}"' if "rx" in node else ""
            parts.append(
                f'<rect x="{node["x"]}" y="{node["y"]}" width="{node["width"]}" '
                f'height="{node["height"]}"{rx} />'
            )
        elif kind == "circle":
            parts.append(
                f'<circle cx="{node["cx"]}" cy="{node["cy"]}" r="{node["r"]}" />'
            )
        elif kind == "line":
            parts.append(
                f'<line x1="{node["x1"]}" y1="{node["y1"]}" x2="{node["x2"]}" y2="{node["y2"]}" />'
            )
        elif kind == "polyline":
            parts.append(
                f'<polyline points="{html_escape(node["points"], quote=True)}" />'
            )
    inner = "".join(parts)
    return (
        f'<span class="shell__nav-ico console-nav-icon" aria-hidden="true">'
        f'<svg class="console-nav-icon__svg" width="{size}" height="{size}" viewBox="0 0 24 24" '
        f'fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" '
        f'stroke-linejoin="round">{inner}</svg></span>'
    )

"""协议端登录页用到的少量 HTML 片段（管理 UI 已迁入 Bot WebUI）。"""

from __future__ import annotations

from html import escape as html_escape


def shell_font_stylesheet_link(public_base_path: str) -> str:
    """与 WebUI main.ts @fontsource 一致：Poppins + Noto Sans SC + JetBrains Mono。"""
    _ = public_base_path
    gfont = (
        "https://fonts.googleapis.com/css2?"
        "family=JetBrains+Mono:wght@400;500;700"
        "&family=Noto+Sans+SC:wght@400;500;600;700"
        "&family=Poppins:wght@400;500;600;700"
        "&display=swap"
    )
    return (
        '  <link rel="preconnect" href="https://fonts.googleapis.com" />\n'
        '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />\n'
        f'  <link rel="stylesheet" href="{html_escape(gfont, quote=True)}" />\n'
    )

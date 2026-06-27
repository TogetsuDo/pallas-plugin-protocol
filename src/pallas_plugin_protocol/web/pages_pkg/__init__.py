"""协议 Web 页模块聚合导出。"""

from .page_account import render_account_workspace
from .page_assets import render_protocol_assets_page
from .page_dashboard import render_dashboard
from .page_import import render_import_page
from .page_new import render_new_account_page
from .page_settings import render_settings_page
from .shell_layout import (
    render_protocol_shell_close,
    render_protocol_shell_open,
    shell_font_stylesheet_link,
    shell_head_assets,
)

__all__ = [
    "render_account_workspace",
    "render_dashboard",
    "render_import_page",
    "render_new_account_page",
    "render_protocol_assets_page",
    "render_protocol_shell_close",
    "render_protocol_shell_open",
    "render_settings_page",
    "shell_font_stylesheet_link",
    "shell_head_assets",
]

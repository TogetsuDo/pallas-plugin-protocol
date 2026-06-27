# ruff: noqa: E501
"""创建账号页。"""

from __future__ import annotations

import json
from html import escape as html_escape

from ..contract import resolve_public_mount_path

from .shell_layout import (
    render_protocol_shell_close,
    render_protocol_shell_open,
    shell_head_assets,
)
from .shell_js import _render_common_api_js, _render_hidden_token_sync_js


def render_new_account_page(
    base_path: str, pallas_console_http_base: str = "/pallas"
) -> str:
    path = base_path.rstrip("/") or resolve_public_mount_path(
        path_override="", implementation_slug=""
    )
    p = json.dumps(path)
    common_api_js = _render_common_api_js()
    token_sync_js = _render_hidden_token_sync_js("backDash")
    shell_open = render_protocol_shell_open(
        path,
        pallas_console_http_base,
        active="new",
        page_title="创建账号",
        page_desc="新建协议实例",
    )
    shell_close = render_protocol_shell_close(
        path, active="new", pallas_console_http_base=pallas_console_http_base
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
{shell_head_assets(path)}  <title>新建账号 · 协议端</title>
</head>
<body data-base-path="{html_escape(path, quote=True)}">
  <input type="hidden" id="token" value="" autocomplete="off" />
  {shell_open}
    <div class="proto-form-page proto-form-page--full">
    <div class="card">
      <div class="field"><label>QQ 号</label>
        <input id="qq" inputmode="numeric" autocomplete="off" />
      </div>
      <div class="field"><label>显示昵称</label>
        <input id="display_name" autocomplete="off" placeholder="可选" />
      </div>
      <div class="field"><label>协议端类型</label>
        <select id="protocol_backend" class="shell-pretty-select">
          <option value="napcat">NapCat（默认）</option>
          <option value="snowluma">SnowLuma</option>
        </select>
      </div>
      <div class="field"><label>内置 WebUI 端口（可选）</label>
        <input id="webui_port" type="number" placeholder="留空则自动分配" />
      </div>
      <div class="field" id="rowNewWebuiToken"><label>内置 WebUI token（可选）</label>
        <input id="webui_token" type="password" autocomplete="off" placeholder="留空则随机生成" />
      </div>
      <hr style="border:none;border-top:1px solid var(--bd);margin:6px 0 14px" />
      <h4 style="margin:0 0 12px;font-size:0.9rem;color:var(--muted);font-weight:700">WS 连接（协议端 → Bot，可选）</h4>
      <p class="muted" style="margin:0 0 12px">正向 WS：协议端主动连接 Bot。跨机部署时填写 Bot 地址；留空则按环境变量自动解析（示例：ws://127.0.0.1:8088/onebot/v11/ws）。</p>
      <div class="field"><label>WS 连接地址</label>
        <input id="ws_url" placeholder="ws://bot-host:8088/onebot/v11/ws" autocomplete="off" />
      </div>
      <div class="field"><label>连接名（协议端侧显示）</label>
        <input id="ws_name" placeholder="pallas" autocomplete="off" />
      </div>
      <div class="field"><label>WS Token（与 Bot 侧 access_token 一致）</label>
        <input id="ws_token" type="password" autocomplete="off" placeholder="留空则不鉴权" />
      </div>
      <div class="row" style="margin-top:4px">
        <button class="btn" type="button" onclick="createAccount()">创建</button>
      </div>
    </div>
    </div>
{shell_close}
  <script>
    const basePath = {p};
{token_sync_js}
{common_api_js}
    initPallasShellThemeFromStorage();
    function applyNewAccountWebuiTokenRow() {{
      const isSl = (document.getElementById("protocol_backend").value || "napcat").trim().toLowerCase() === "snowluma";
      const row = document.getElementById("rowNewWebuiToken");
      if (row) row.style.display = isSl ? "none" : "";
    }}
    document.getElementById("protocol_backend").addEventListener("change", applyNewAccountWebuiTokenRow);
    applyNewAccountWebuiTokenRow();
    async function createAccount() {{
      try {{
        const wport = document.getElementById("webui_port").value.trim();
        const pb = (document.getElementById("protocol_backend").value || "napcat").trim().toLowerCase();
        const wtok = pb === "snowluma" ? "" : document.getElementById("webui_token").value.trim();
        const wn = parseInt(wport, 10);
        const disp = document.getElementById("display_name").value.trim();
        const qq = document.getElementById("qq").value.trim();
        const wsUrl = document.getElementById("ws_url").value.trim();
        const wsName = document.getElementById("ws_name").value.trim();
        const wsTok = document.getElementById("ws_token").value;
        const body = {{
          id: qq,
          qq,
          display_name: disp,
          enabled: true,
          protocol_backend: pb === "snowluma" ? "snowluma" : "napcat",
          ...(wport && !Number.isNaN(wn) ? {{ webui_port: wn }} : {{}}),
          ...(wtok ? {{ webui_token: wtok }} : {{}}),
          ...(wsUrl ? {{ ws_url: wsUrl }} : {{}}),
          ...(wsName ? {{ ws_name: wsName }} : {{}}),
          ...(wsTok ? {{ ws_token: wsTok }} : {{}}),
        }};
        if (!qq) throw new Error("请填写 QQ 号");
        await api("/api/accounts", {{ method: "POST", headers: {{ "Content-Type": "application/json" }}, body: JSON.stringify(body) }});
        const t = (document.getElementById("token").value || "").trim();
        location.href = basePath;
      }} catch (e) {{ alert(e.message); }}
    }}
  </script>
</body>
</html>
"""

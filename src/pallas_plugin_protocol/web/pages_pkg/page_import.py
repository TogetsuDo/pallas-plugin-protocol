# ruff: noqa: E501
"""导入账号页。"""

from __future__ import annotations

import json

from ..contract import resolve_public_mount_path

from .shell_layout import (
    render_protocol_shell_close,
    render_protocol_shell_open,
    shell_head_assets,
)
from .shell_js import _render_common_api_js, _render_hidden_token_sync_js


def render_import_page(
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
        active="import",
        page_title="导入账号",
        page_desc="批量导入旧协议端数据",
    )
    shell_close = render_protocol_shell_close(
        path, active="import", pallas_console_http_base=pallas_console_http_base
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
{shell_head_assets(path)}  <title>导入账号 · 协议端</title>
  <style>
.result-row {{ display:flex; gap:8px; align-items:baseline; padding:6px 0; border-bottom:1px solid var(--bd); font-size:0.88rem; }}
.result-row:last-child {{ border-bottom:none; }}
.result-row .folder {{ font-weight:600; min-width:160px; }}
.result-row .detail {{ color:var(--muted); }}
  </style>
</head>
<body>
  <input type="hidden" id="token" value="" autocomplete="off" />
  {shell_open}
    <div class="proto-form-page">
    <div class="card">
      <h3 style="margin:0 0 4px">批量导入旧协议端账号</h3>
      <p class="muted" style="margin:0 0 16px">
        扫描指定目录下的账号文件夹（格式：<code>&lt;昵称&gt;/config/</code>），
        从 <code>onebot_*.json</code> 提取 QQ 号，原地注册为受管账号，
        并将 <code>QQ/</code> 复制到 <code>.config/QQ/</code>。
      </p>

      <div class="field">
        <label>账号文件夹根目录（服务器绝对路径）</label>
        <input id="sourceDir" autocomplete="off" placeholder="/data/old_accounts" style="width:100%" />
      </div>

      <div class="field">
        <label>WS 连接地址（留空则使用 .env 默认值）</label>
        <input id="wsUrl" autocomplete="off" placeholder="ws://127.0.0.1:8088/onebot/v11/ws" style="width:100%" />
      </div>

      <div class="field">
        <label>WS Token（留空则不鉴权）</label>
        <input id="wsToken" type="password" autocomplete="off" style="width:100%" />
      </div>

      <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;margin-bottom:8px">
        <label style="display:flex;align-items:center;gap:6px;font-size:0.88rem;cursor:pointer">
          <input type="checkbox" id="dryRun" /> 仅预览（不写入）
        </label>
        <label style="display:flex;align-items:center;gap:6px;font-size:0.88rem;cursor:pointer">
          <input type="checkbox" id="skipExisting" checked /> 跳过已存在账号
        </label>
      </div>

      <div class="row">
        <button class="btn" id="btnImport" type="button" onclick="doImport()">开始导入</button>
      </div>
    </div>

    <div id="resultSection" class="proto-form-results" style="display:none">
      <div class="kpi-grid" id="resultKpis"></div>
      <div class="card" style="margin-top:12px">
        <h3 style="margin:0 0 10px">导入结果</h3>
        <div id="resultImported"></div>
        <div id="resultSkipped" style="margin-top:10px"></div>
        <div id="resultFailed" style="margin-top:10px"></div>
      </div>
    </div>
    </div>
{shell_close}

  <script>
    const basePath = {p};
{token_sync_js}
{common_api_js}
    initPallasShellThemeFromStorage();

    function renderRows(containerId, items, labelFn, cls) {{
      const el = document.getElementById(containerId);
      if (!items || !items.length) {{ el.innerHTML = ""; return; }}
      el.innerHTML = `<div style="font-size:0.78rem;color:var(--muted);font-weight:700;margin-bottom:6px;text-transform:uppercase">${{cls}}</div>`
        + items.map((r) => `<div class="result-row"><span class="folder">${{r.folder || ""}}</span><span class="detail">${{labelFn(r)}}</span></div>`).join("");
    }}

    async function doImport() {{
      const src = document.getElementById("sourceDir").value.trim();
      if (!src) {{ alert("请填写账号文件夹根目录"); return; }}
      const btn = document.getElementById("btnImport");
      btn.disabled = true;
      btn.innerHTML = '<span class="spinner"></span>导入中…';
      document.getElementById("resultSection").style.display = "none";
      try {{
        const body = {{
          source_dir: src,
          dry_run: document.getElementById("dryRun").checked,
          skip_existing: document.getElementById("skipExisting").checked,
          ws_url: document.getElementById("wsUrl").value.trim(),
          ws_token: document.getElementById("wsToken").value,
        }};
        const data = await api("/api/accounts/import", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify(body),
        }});
        const imp = data.imported || [];
        const skp = data.skipped || [];
        const fld = data.failed || [];
        document.getElementById("resultKpis").innerHTML = `
          <div class="kpi"><div class="k">已导入</div><div class="v" style="color:var(--ok)">${{imp.length}}</div></div>
          <div class="kpi"><div class="k">已跳过</div><div class="v" style="color:var(--warn)">${{skp.length}}</div></div>
          <div class="kpi"><div class="k">失败</div><div class="v" style="color:var(--err)">${{fld.length}}</div></div>`;
        renderRows("resultImported", imp,
          (r) => `QQ: ${{r.qq}}  端口: ${{r.webui_port}}${{r.qq_copied_to ? "  QQ/ → .config/QQ/" : ""}}`,
          "已导入");
        renderRows("resultSkipped", skp,
          (r) => r.qq ? `QQ: ${{r.qq}}  (${{r.reason}})` : r.reason,
          "已跳过");
        renderRows("resultFailed", fld,
          (r) => r.reason,
          "失败");
        document.getElementById("resultSection").style.display = "block";
        if (imp.length && !body.dry_run) {{
          setTimeout(() => location.href = document.getElementById("backDash").href, 1800);
        }}
      }} catch (e) {{
        alert(e.message || String(e));
      }} finally {{
        btn.disabled = false;
        btn.textContent = "开始导入";
      }}
    }}
  </script>
  <div id="statusbar" class="statusbar"></div>
</body>
</html>
"""

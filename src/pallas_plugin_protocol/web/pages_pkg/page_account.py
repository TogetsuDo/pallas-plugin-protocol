# ruff: noqa: E501
"""单账号工作区页。"""

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


def render_account_workspace(
    base_path: str,
    account_id: str,
    pallas_console_http_base: str = "/pallas",
    *,
    page_session: str = "",
) -> str:
    path = base_path.rstrip("/") or resolve_public_mount_path(
        path_override="", implementation_slug=""
    )
    p = json.dumps(path)
    aid = json.dumps(account_id)
    aid_h = html_escape(account_id, quote=True)
    common_api_js = _render_common_api_js()
    token_sync_js = _render_hidden_token_sync_js("backDash", page_session=page_session)
    shell_open = render_protocol_shell_open(
        path,
        pallas_console_http_base,
        active="",
        page_title=f"账号 {account_id}",
        page_desc="实例控制台",
    )
    shell_close = render_protocol_shell_close(
        path, active="", pallas_console_http_base=pallas_console_http_base
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
{shell_head_assets(path)}  <title>账号 {aid_h} · 协议端</title>
</head>
<body>
  <input type="hidden" id="token" value="" autocomplete="off" />
  {shell_open}
    <div class="layout-acc">
      <nav class="side" id="nav">
        <a href="#" class="active" data-tab="overview">概览</a>
        <a href="#" data-tab="settings">设置</a>
        <a href="#" data-tab="configs">原始配置</a>
        <a href="#" id="accLinkRuntime">协议资产</a>
      </nav>
      <div class="acc-main">
        <section class="panel active" id="panel-overview">
          <div class="card">
            <h3>状态</h3>
            <div id="ovBody" class="muted">加载中…</div>
            <div class="row" style="margin-top:14px">
              <button class="btn secondary" type="button" onclick="doStart()">启动</button>
              <button class="btn secondary" type="button" onclick="doStop()">停止</button>
              <button class="btn secondary" type="button" onclick="doRestart()">重启</button>
              <button class="btn danger" type="button" onclick="doDelete()">删除账号</button>
            </div>
            <div id="snowlumaInjectRow" class="row" style="margin-top:10px;display:none;flex-wrap:wrap;gap:10px;align-items:flex-start">
              <span class="muted" style="font-size:0.82rem;line-height:1.5">SnowLuma 需在<strong>自带 WebUI</strong>中对 QQ 进程<strong>首次手动加载/注入</strong>后，进程列表才会显示 UIN；请先使用上方「打开原生 WebUI」登录并完成首次注入。</span>
            </div>
          </div>
          <div class="card acc-qr-card" id="accQrCard" hidden style="margin-top:12px">
            <div class="acc-qr-card__hd row" style="justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:10px;margin-bottom:10px">
              <div>
                <h3 style="margin:0">登录二维码</h3>
                <p class="muted acc-qr-card__hint" id="accQrHint" style="margin:4px 0 0;font-size:0.82rem">协议端已生成 PNG，可直接扫码登录</p>
              </div>
              <div class="row-actions acc-qr-card__actions">
                <a class="btn secondary" id="accQrOpenLink" href="#" target="_blank" rel="noopener noreferrer">新标签打开</a>
                <button class="btn secondary" type="button" onclick="pollAccQrcode(true)">刷新</button>
              </div>
            </div>
            <div class="acc-qr-card__body">
              <img id="accQrImg" class="acc-qr-card__img" alt="登录二维码" decoding="async" />
            </div>
          </div>
          <div class="card" style="margin-top:12px">
            <div class="row" style="justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:8px">
              <h3 style="margin:0">协议端进程</h3>
              <button class="btn secondary" type="button" onclick="copyLogText('accLogs')">复制</button>
            </div>
            <pre class="logs logs-protocol" id="accLogs" title="可鼠标框选复制">正在加载进程日志…</pre>
          </div>
          <div class="card" style="margin-top:12px">
            <div class="row" style="justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
              <p class="muted" style="margin:0">NoneBot 主进程日志（分片下数据量大，按需展开）</p>
              <button type="button" class="btn secondary" id="accNbToggleBtn">展开日志</button>
            </div>
            <div id="accNbLogSection" hidden>
            <div class="sl-runlog sl-runlog--account" id="accNbLogCard">
              <div class="sl-runlog-hd">
                <div class="sl-runlog-titles">
                  <h2 style="margin:0;font-size:1.05rem">运行日志<span class="sl-runlog-bad wait" id="accNbLogStreamBadge">未启用</span></h2>
                  <p style="margin:4px 0 0;font-size:0.78rem;color:var(--muted)" id="accNbLogSubLine">
                    最近 <span id="accNbLogFilteredN">0</span> / <span id="accNbLogTotalN">0</span> 条 · SSE
                  </p>
                </div>
                <div class="sl-runlog-tools">
                  <input type="search" id="accNbLogFilter" class="grow" placeholder="搜索消息 / 模块 / 级别" />
                  <select id="accNbLogScope" class="sl-runlog-scope" title="范围">
                    <option value="all">全部</option>
                    <option value="webui">控制台</option>
                    <option value="protocol">协议</option>
                  </select>
                  <button type="button" class="btn secondary" id="accNbLogPauseBtn">暂停</button>
                  <button type="button" class="btn secondary" id="accNbLogRefreshBtn">刷新</button>
                  <button type="button" class="btn secondary" id="accNbLogClearBtn">清空视图</button>
                  <button type="button" class="btn secondary" id="accNbLogCopyBtn">复制</button>
                </div>
              </div>
              <div class="sl-runlog-levels" id="accNbLogLevels"></div>
              <div class="sl-runlog-viewport" id="accNbLogViewport" title="可框选复制">
                <div class="sl-runlog-inner" id="accNbLogRows"></div>
              </div>
            </div>
            </div>
          </div>
        </section>
        <section class="panel" id="panel-settings">
          <div class="card">
            <h3>详细设置</h3>
            <p id="onebotHint" class="muted"></p>
            <p id="setMsg" class="muted"></p>
            <div class="field"><label>实例名</label><input id="display_name" /></div>
            <div class="field"><label>QQ（只读）</label><input id="qq" readonly /></div>
            <div class="field"><label>协议端类型</label>
              <select id="protocol_backend" class="shell-pretty-select">
                <option value="napcat">NapCat</option>
                <option value="snowluma">SnowLuma</option>
              </select>
            </div>
            <p class="muted" style="margin:-6px 0 10px;font-size:0.82rem">
              切换后启动命令与数据子目录会按后端调整；建议在进程已停止时修改并保存。
            </p>
            <div class="field" id="rowManagedRuntimeTag"><label>托管运行时版本</label>
              <select id="managed_runtime_tag" class="shell-pretty-select">
                <option value="">跟随全局默认（仪表盘当前托管）</option>
              </select>
            </div>
            <p class="muted" style="margin:-6px 0 10px;font-size:0.82rem;line-height:1.45">
              与协议资产页 <code>runtime_extract</code> 下子目录（Release 标签）一致；留空则跟随仪表盘全局托管。保存后需重启本账号协议进程。
            </p>
            <div class="field"><label>内置 WebUI 端口</label><input id="webui_port" type="number" /></div>
            <p id="webuiTokenHint" class="muted" style="display:none;margin:-4px 0 8px;font-size:0.82rem;white-space:pre-wrap"></p>
            <div class="field" id="rowWebuiToken"><label>内置 WebUI token</label><input id="webui_token" autocomplete="off" /></div>
            <div id="rowSnowlumaDockerVnc" style="display:none;margin-top:4px">
              <p class="muted" style="margin:0 0 10px;font-size:0.82rem;line-height:1.45">
                当前账号为 <strong>SnowLuma Linux Docker</strong> 时，<strong>OneBot HTTP/WS</strong> 与 <strong>noVNC / VNC</strong> 在留空时由服务端按已占用端口自动挑选宿主机端口（多实例互不冲突）。
                亦可在此手动指定 <strong>noVNC</strong>（浏览器桌面）与 <strong>VNC</strong>：<strong>填 0</strong> 表示不发布该映射，<strong>留空并保存</strong>则走自动或全局 <code>.env</code>。
              </p>
              <div class="field"><label>宿主机 noVNC 端口</label>
                <input id="snowluma_docker_host_novnc_port" type="number" min="0" max="65535" placeholder="留空=自动或全局" />
              </div>
              <div class="field"><label>宿主机 VNC 端口</label>
                <input id="snowluma_docker_host_vnc_port" type="number" min="0" max="65535" placeholder="留空=自动或全局" />
              </div>
            </div>
            <div id="snowlumaDockerPortMapCard" style="display:none;margin-top:12px;padding:12px 14px;border:1px solid var(--bd);border-radius:var(--radius);background:var(--bg1)">
              <div style="font-size:0.88rem;font-weight:700;color:var(--txt);margin-bottom:8px">SnowLuma Docker 端口映射</div>
              <p id="snowlumaDockerPortMapHint" class="muted" style="margin:0 0 8px;font-size:0.8rem;line-height:1.45"></p>
              <div id="snowlumaDockerPortMapTableWrap" style="overflow:auto;max-height:220px">
                <table class="acc-table" style="width:100%;border-collapse:collapse;font-size:0.82rem">
                  <thead><tr>
                    <th style="text-align:left;padding:6px 8px">服务</th>
                    <th style="text-align:left;padding:6px 8px">宿主机</th>
                    <th style="text-align:left;padding:6px 8px">容器内</th>
                  </tr></thead>
                  <tbody id="snowlumaDockerPortMapBody"></tbody>
                </table>
              </div>
            </div>
            <hr style="border:none;border-top:1px solid var(--bd);margin:6px 0 14px" />
            <h4 style="margin:0 0 12px;font-size:0.9rem;color:var(--muted);font-weight:700">WS 连接（协议端 → Bot）</h4>
            <p class="muted" style="margin:0 0 12px">正向 WS：协议端主动连接牛牛时使用的地址。跨机部署时填写牛牛所在机器对本机可达的地址；保存后<strong>重启协议端进程</strong>生效，无需重启牛牛。</p>
            <div class="field"><label>WS 连接地址</label>
              <input id="ws_url" placeholder="ws://bot-host:8088/onebot/v11/ws" autocomplete="off" />
            </div>
            <div class="field"><label id="lblWsName">连接名（协议端侧显示）</label>
              <input id="ws_name" placeholder="pallas" autocomplete="off" />
            </div>
            <div class="field"><label>WS Token（与 Bot 侧 access_token 一致）</label>
              <input id="ws_token" type="password" autocomplete="off" placeholder="留空则不鉴权" />
            </div>
            <div class="row">
              <button class="btn" type="button" onclick="saveSettings()">保存</button>
            </div>
          </div>
        </section>
        <section class="panel" id="panel-configs">
          <div class="card">
            <h3>原始配置</h3>
            <p id="cfgProtocolDirtyHint" class="muted" style="display:none;margin:-4px 0 10px;color:#b45309">
              当前选择的协议端类型与已保存不一致：请先回到「设置」保存协议类型，再编辑下方 JSON。
            </p>
            <p id="cfgMsg" class="muted"></p>
            <div class="field"><label>onebot</label><textarea class="cfg mono" id="tj_onebot"></textarea></div>
            <div class="field" id="rowCfgMid"><label id="lblCfgMid">napcat</label><textarea class="cfg mono" id="tj_napcat"></textarea></div>
            <div class="field" id="rowCfgWebui"><label>webui</label><textarea class="cfg mono" id="tj_webui"></textarea></div>
            <button class="btn" type="button" onclick="saveConfigs()">保存 JSON</button>
          </div>
        </section>
      </div>
    </div>
{shell_close}
  <script>
    const basePath = {p};
    const accountId = {aid};
    let accountProcessRunning = false;
{common_api_js}
    initPallasShellThemeFromStorage();
    applyShellUiPrefsFromStorage();
    const ACC_NB_LEVELS = ["debug", "info", "success", "warn", "error"];
    let accNbLogEntries = [];
    let accNbLogPaused = false;
    let accNbLogFilter = "";
    let accNbLogLevels = new Set(ACC_NB_LEVELS);
    let accNbLogEs = null;
    let accNbLogExpanded = false;
    let accNbLogLoading = false;
    let accNbLogRenderDeferred = false;
    let accNbRenderScheduled = 0;
    const ACC_NB_MAX_ENTRIES = 80;
    function accNbFormatTime(iso) {{
      try {{
        const d = new Date(iso);
        if (Number.isNaN(d.getTime())) return String(iso || "");
        return d.toLocaleTimeString();
      }} catch (e) {{ return String(iso || ""); }}
    }}
    function accNbStreamBadge(text, kind) {{
      const el = document.getElementById("accNbLogStreamBadge");
      if (!el) return;
      el.textContent = text;
      el.className = "sl-runlog-bad " + (kind === "ok" ? "ok" : kind === "err" ? "err" : "wait");
    }}
    function accNbLevelUiClass(lv) {{
      const u = String(lv || "").toLowerCase();
      if (u === "debug") return "sl-lv-debug";
      if (u === "success") return "sl-lv-success";
      if (u === "warn") return "sl-lv-warn";
      if (u === "error") return "sl-lv-error";
      return "sl-lv-info";
    }}
    function accNbFiltered() {{
      const f = (accNbLogFilter || "").trim().toLowerCase();
      return accNbLogEntries.filter((x) => {{
        if (!accNbLogLevels.has(String(x.level || "").toLowerCase())) return false;
        if (!f) return true;
        const m = String(x.message || "").toLowerCase();
        const sc = String(x.scope || "").toLowerCase();
        const lv = String(x.level || "").toLowerCase();
        return m.includes(f) || sc.includes(f) || lv.includes(f);
      }});
    }}
    function accNbShouldPauseDom() {{
      const vp = document.getElementById("accNbLogViewport");
      if (!vp) return false;
      if (isLogElementUserSelecting(vp)) return true;
      return false;
    }}
    function accNbRender() {{
      const rows = document.getElementById("accNbLogRows");
      const sub = document.getElementById("accNbLogFilteredN");
      const tot = document.getElementById("accNbLogTotalN");
      if (tot) tot.textContent = String(accNbLogEntries.length);
      const list = accNbFiltered();
      if (sub) sub.textContent = String(list.length);
      if (!rows) return;
      if (!list.length) {{
        rows.innerHTML = '<div class="sl-runlog-empty">暂无日志</div>';
        return;
      }}
      rows.innerHTML = list.slice(-ACC_NB_MAX_ENTRIES).map((x) => {{
        const lv = String(x.level || "").toUpperCase();
        const t = accNbFormatTime(x.time);
        const sc = escHtml(x.scope || "");
        const msg = escHtml(x.message || "");
        const lc = accNbLevelUiClass(x.level);
        return `<div class="sl-runlog-row"><span class="sl-runlog-t">${{t}}</span><span class="sl-runlog-lv ${{lc}}">${{lv}}</span><span class="sl-runlog-sc">[${{sc}}]</span><span class="sl-runlog-msg">${{msg}}</span></div>`;
      }}).join("");
    }}
    function flushDeferredAccNbLogRender() {{
      if (!accNbLogRenderDeferred || !accNbLogExpanded) return;
      accNbLogRenderDeferred = false;
      scheduleAccNbRender();
    }}
    function scheduleAccNbRender() {{
      if (!accNbSnapshotExpanded()) return;
      if (accNbRenderScheduled) return;
      if (accNbShouldPauseDom()) {{
        accNbLogRenderDeferred = true;
        return;
      }}
      accNbRenderScheduled = requestAnimationFrame(() => {{
        accNbRenderScheduled = 0;
        if (accNbShouldPauseDom()) {{
          accNbLogRenderDeferred = true;
          return;
        }}
        accNbRender();
        accNbSyncViewportLayout();
        accNbScrollToEnd();
      }});
    }}
    function accNbSnapshotExpanded() {{
      return accNbLogExpanded;
    }}
    function accNbScrollToEnd() {{
      if (accNbLogPaused) return;
      if (accNbShouldPauseDom()) return;
      const vp = document.getElementById("accNbLogViewport");
      if (vp) vp.scrollTop = vp.scrollHeight;
    }}
    function accNbSyncViewportLayout() {{
      const card = document.getElementById("accNbLogCard");
      const vp = document.getElementById("accNbLogViewport");
      if (!card || !vp || !accNbLogExpanded) return;
      const cardStyle = getComputedStyle(card);
      const gap = parseFloat(cardStyle.rowGap || cardStyle.gap || "10") || 10;
      const padY = parseFloat(cardStyle.paddingTop) + parseFloat(cardStyle.paddingBottom);
      let siblings = 0;
      let siblingCount = 0;
      for (const el of card.children) {{
        if (el === vp) continue;
        siblings += el.getBoundingClientRect().height;
        siblingCount += 1;
      }}
      const avail = card.clientHeight - padY - gap * siblingCount - siblings;
      if (avail > 72) vp.style.height = `${{Math.floor(avail)}}px`;
      else vp.style.height = "";
    }}
    function accNbInitLevelPills() {{
      const host = document.getElementById("accNbLogLevels");
      if (!host) return;
      host.innerHTML = ACC_NB_LEVELS.map((lv) =>
        `<button type="button" data-acc-nb-lv="${{lv}}" class="on">${{String(lv).toUpperCase()}}</button>`
      ).join("");
      host.querySelectorAll("[data-acc-nb-lv]").forEach((btn) => {{
        btn.addEventListener("click", () => {{
          const lv = btn.getAttribute("data-acc-nb-lv");
          if (accNbLogLevels.has(lv)) accNbLogLevels.delete(lv);
          else accNbLogLevels.add(lv);
          btn.classList.toggle("on", accNbLogLevels.has(lv));
          btn.classList.toggle("off", !accNbLogLevels.has(lv));
          scheduleAccNbRender();
        }});
      }});
    }}
    async function accNbEnsureStarted() {{
      if (!accNbLogExpanded || accNbLogLoading) return;
      accNbLogLoading = true;
      try {{
        await accNbLoadInitial();
        accNbStartSse();
      }} finally {{
        accNbLogLoading = false;
      }}
    }}
    async function accNbLoadInitial() {{
      const scopeEl = document.getElementById("accNbLogScope");
      const sc = scopeEl ? scopeEl.value : "all";
      const data = await api(`/api/nonebot-logs?lines=60&scope=${{encodeURIComponent(sc)}}`);
      accNbLogEntries = Array.isArray(data.entries) ? data.entries.slice(-ACC_NB_MAX_ENTRIES) : [];
      if (accNbLogExpanded) {{
        accNbRender();
        accNbSyncViewportLayout();
        accNbScrollToEnd();
      }} else {{
        scheduleAccNbRender();
      }}
    }}
    function accNbClear() {{
      if (!confirm("清空当前日志视图？仅影响浏览器展示，不清服务端缓冲。")) return;
      accNbLogEntries = [];
      accNbRender();
    }}
    function accNbCopy() {{
      const lines = accNbFiltered().map((x) =>
        `${{accNbFormatTime(x.time)}} ${{String(x.level || "").toUpperCase()}} [${{x.scope}}] ${{x.message}}`
      );
      const t = lines.join("\\n");
      if (!String(t).trim()) {{ notify("当前无可复制内容", "warn"); return; }}
      navigator.clipboard.writeText(t).then(() => notify("已复制", "ok")).catch((e) => notify(String(e.message || e), "err"));
    }}
    function accNbStopSse() {{
      if (accNbLogEs) {{
        try {{ accNbLogEs.close(); }} catch (e) {{}}
        accNbLogEs = null;
      }}
    }}
    function accNbStartSse() {{
      accNbStopSse();
      const tok = getSessionToken();
      const scopeEl = document.getElementById("accNbLogScope");
      const sc = scopeEl ? scopeEl.value : "all";
      let url = `${{basePath}}/api/nonebot-logs/stream?scope=${{encodeURIComponent(sc)}}`;
      if (tok) url += `&token=${{encodeURIComponent(tok)}}`;
      accNbStreamBadge("连接中", "wait");
      const es = new EventSource(url);
      accNbLogEs = es;
      es.onopen = () => accNbStreamBadge("实时", "ok");
      es.onerror = () => accNbStreamBadge("重连中", "err");
      es.onmessage = (ev) => {{
        try {{
          const row = JSON.parse(ev.data);
          if (row && row.type === "ready") return;
          if (!row || typeof row.id !== "number") return;
          if (accNbLogPaused) return;
          accNbLogEntries = [...accNbLogEntries.filter((it) => it.id !== row.id), row].slice(-ACC_NB_MAX_ENTRIES);
          scheduleAccNbRender();
        }} catch (e) {{}}
      }};
    }}
    function accNbWireRunlogUi() {{
      accNbInitLevelPills();
      document.getElementById("accNbLogFilter")?.addEventListener("input", (e) => {{
        accNbLogFilter = (e.target && e.target.value) || "";
        scheduleAccNbRender();
      }});
      document.getElementById("accNbLogPauseBtn")?.addEventListener("click", () => {{
        accNbLogPaused = !accNbLogPaused;
        const b = document.getElementById("accNbLogPauseBtn");
        if (b) b.textContent = accNbLogPaused ? "继续" : "暂停";
        if (!accNbLogPaused) accNbScrollToEnd();
      }});
      document.getElementById("accNbLogRefreshBtn")?.addEventListener("click", () => {{
        accNbLoadInitial().catch((e) => notify(e.message || e, "err"));
      }});
      document.getElementById("accNbLogClearBtn")?.addEventListener("click", accNbClear);
      document.getElementById("accNbLogCopyBtn")?.addEventListener("click", accNbCopy);
      document.getElementById("accNbLogScope")?.addEventListener("change", () => {{
        if (!accNbLogExpanded) return;
        accNbStopSse();
        accNbEnsureStarted().catch((e) => notify(String(e.message || e), "err"));
      }});
      document.getElementById("accNbToggleBtn")?.addEventListener("click", () => {{
        accNbLogExpanded = !accNbLogExpanded;
        const sec = document.getElementById("accNbLogSection");
        const btn = document.getElementById("accNbToggleBtn");
        if (sec) sec.hidden = !accNbLogExpanded;
        if (btn) btn.textContent = accNbLogExpanded ? "收起日志" : "展开日志";
        if (accNbLogExpanded) {{
          accNbEnsureStarted().then(() => {{
            flushDeferredAccNbLogRender();
            accNbRender();
            requestAnimationFrame(() => {{
              accNbSyncViewportLayout();
              requestAnimationFrame(() => accNbScrollToEnd());
            }});
          }}).catch((e) => notify(String(e.message || e), "err"));
        }} else {{
          accNbStopSse();
          accNbStreamBadge("未启用", "wait");
          const vp = document.getElementById("accNbLogViewport");
          if (vp) vp.style.height = "";
        }}
      }});
      window.addEventListener("resize", () => {{
        if (!accNbLogExpanded) return;
        accNbSyncViewportLayout();
      }});
    }}
    let activeTab = "overview";
    function tab(name) {{
      activeTab = name;
      document.querySelectorAll(".panel").forEach((el) => el.classList.remove("active"));
      document.getElementById("panel-" + name).classList.add("active");
      document.querySelectorAll(".side a[data-tab]").forEach((a) => a.classList.toggle("active", a.dataset.tab === name));
      const q = "tab=" + encodeURIComponent(name);
      history.replaceState(null, "", `${{basePath}}/account/${{encodeURIComponent(accountId)}}?${{q}}`);
      if (name !== "overview") {{
        accNbStopSse();
      }}
      if (name === "settings") loadHints();
      if (name === "configs") {{
        loadJsonCfgs().catch(() => {{}});
        updateCfgDirtyHint();
      }}
    }}
    document.getElementById("protocol_backend").addEventListener("change", () => {{
      applySettingsForProtocolSelect();
    }});
    document.getElementById("nav").addEventListener("click", (e) => {{
      const a = e.target.closest("a[data-tab]");
      if (!a) return;
      e.preventDefault();
      tab(a.dataset.tab);
    }});
    document.getElementById("accLinkRuntime").addEventListener("click", (e) => {{
      e.preventDefault();
      const q = __savedAccountBackend === "snowluma" ? "?protocol=snowluma" : "?protocol=napcat";
      location.href = `${{basePath}}/assets${{q}}`;
    }});
    function escHtml(s) {{
      return String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }}
    let accQrLastUpdated = 0;
    let accQrObjectUrl = "";
    function accQrcodeFetchUrl(ts) {{
      let url = `${{basePath}}/api/accounts/${{encodeURIComponent(accountId)}}/qrcode`;
      const q = [];
      const tok = getSessionToken();
      if (tok) q.push(`token=${{encodeURIComponent(tok)}}`);
      if (ts) q.push(`t=${{encodeURIComponent(String(ts))}}`);
      if (q.length) url += "?" + q.join("&");
      return url;
    }}
    async function loadAccQrcodeImage(ts) {{
      const img = document.getElementById("accQrImg");
      const hint = document.getElementById("accQrHint");
      const link = document.getElementById("accQrOpenLink");
      const url = accQrcodeFetchUrl(ts);
      if (link) link.href = url;
      if (!img) return;
      const headers = {{}};
      const tok = getSessionToken();
      if (tok) headers["X-Pallas-Protocol-Token"] = tok;
      const res = await fetch(url, {{ credentials: "same-origin", headers }});
      if (!res.ok) throw new Error((await res.text()) || String(res.status));
      const blob = await res.blob();
      if (accQrObjectUrl) {{
        try {{ URL.revokeObjectURL(accQrObjectUrl); }} catch (e) {{}}
      }}
      accQrObjectUrl = URL.createObjectURL(blob);
      img.src = accQrObjectUrl;
      img.onerror = () => {{
        if (hint) hint.textContent = "二维码加载失败，请点「刷新」重试";
      }};
    }}
    async function pollAccQrcode(force) {{
      const card = document.getElementById("accQrCard");
      const hint = document.getElementById("accQrHint");
      try {{
        if (force) {{
          if (hint) hint.textContent = "正在刷新二维码…";
          await api(`/api/accounts/${{encodeURIComponent(accountId)}}/qrcode/refresh`, {{ method: "POST" }});
        }}
        const meta = await api(`/api/accounts/${{encodeURIComponent(accountId)}}/qrcode/meta`);
        const pngNow = !!(meta && meta.exists);
        if (!pngNow) {{
          if (card) card.hidden = true;
          accQrLastUpdated = 0;
          return;
        }}
        const ts = meta.updated_at || 0;
        if (force || ts !== accQrLastUpdated) {{
          accQrLastUpdated = ts;
          if (card) card.hidden = false;
          await loadAccQrcodeImage(force ? Date.now() : ts);
          if (hint && ts) {{
            try {{
              hint.textContent = "更新于 " + new Date(ts * 1000).toLocaleString() + " · 可直接扫码";
            }} catch (e) {{}}
          }}
        }}
      }} catch (e) {{
        if (card && force) card.hidden = true;
        if (hint && force) hint.textContent = String(e.message || e);
      }}
    }}
    async function bootAccountOverview() {{
      pollAccLogs().catch((e) => notify(String(e.message || e), "err"));
      pollAccQrcode(true).catch(() => {{}});
      try {{
        await loadAccount({{ brief: true }});
      }} catch (e) {{
        notify(String(e.message || e), "err");
      }}
      loadAccount({{ brief: false }}).catch((e) => notify(String(e.message || e), "err"));
    }}
    let __savedAccountBackend = "napcat";
    window.__managedTagSaved = "";
    async function fillManagedRuntimeTagSelect() {{
      const sel = document.getElementById("managed_runtime_tag");
      if (!sel) return;
      const saved = window.__managedTagSaved || "";
      try {{
        const path = currentProtocolSelect() === "snowluma"
          ? "/api/snowluma/runtime/local-inventory"
          : "/api/runtime/local-inventory";
        const data = await api(path);
        const dirs = Array.isArray(data.extract_dirs) ? data.extract_dirs : [];
        const names = dirs.map((d) => d.name).filter(Boolean);
        const parts = ['<option value="">跟随全局默认（仪表盘当前托管）</option>'];
        for (const n of names) {{
          const enc = String(n).replace(/&/g, "&amp;").replace(/"/g, "&quot;").replace(/</g, "&lt;");
          parts.push(`<option value="${{enc}}">${{escHtml(n)}}</option>`);
        }}
        sel.innerHTML = parts.join("");
        sel.value = saved && names.includes(saved) ? saved : "";
      }} catch (e) {{
        sel.innerHTML = '<option value="">（加载失败）</option>';
      }}
      if (typeof shellPrettySyncSelect === "function") shellPrettySyncSelect(sel);
    }}
    function currentProtocolSelect() {{
      return (document.getElementById("protocol_backend").value || "napcat").trim().toLowerCase() === "snowluma" ? "snowluma" : "napcat";
    }}
    function applySettingsForProtocolSelect() {{
      const isSl = currentProtocolSelect() === "snowluma";
      const row = document.getElementById("rowWebuiToken");
      if (row) row.style.display = isSl ? "none" : "";
      updateCfgDirtyHint();
      void fillManagedRuntimeTagSelect();
    }}
    function syncSnowlumaDockerVncRow(account) {{
      const rowD = document.getElementById("rowSnowlumaDockerVnc");
      if (!rowD) return;
      const show = !!(account && account.snowluma_linux_docker);
      rowD.style.display = show ? "block" : "none";
      if (!show) return;
      const nn = document.getElementById("snowluma_docker_host_novnc_port");
      const vv = document.getElementById("snowluma_docker_host_vnc_port");
      const gn = account.snowluma_docker_host_novnc_port;
      const gv = account.snowluma_docker_host_vnc_port;
      if (nn) nn.value = (gn !== undefined && gn !== null && String(gn).trim() !== "") ? String(gn) : "";
      if (vv) vv.value = (gv !== undefined && gv !== null && String(gv).trim() !== "") ? String(gv) : "";
    }}
    function syncSnowlumaDockerPortMapCard(account) {{
      const card = document.getElementById("snowlumaDockerPortMapCard");
      const hint = document.getElementById("snowlumaDockerPortMapHint");
      const body = document.getElementById("snowlumaDockerPortMapBody");
      if (!card || !body) return;
      const sp = account && account.snowluma_publish_ports;
      const items = sp && Array.isArray(sp.items) ? sp.items : [];
      const show = !!(account && account.snowluma_linux_docker && items.length);
      card.style.display = show ? "block" : "none";
      if (!show) return;
      const host = String((sp && sp.bind_host) || "127.0.0.1").trim() || "127.0.0.1";
      if (hint) {{
        hint.textContent = "宿主机 " + escHtml(host) + " 上映射到容器内端口如下；保存设置并重启本账号协议进程后生效。";
      }}
      body.innerHTML = items.map((row) => {{
        const lab = escHtml(row.label || "");
        const hp = escHtml(String(row.host ?? ""));
        const cp = escHtml(String(row.container ?? ""));
        return "<tr><td style=\\"padding:6px 8px\\">" + lab + "</td>"
          + "<td style=\\"padding:6px 8px;font-family:var(--font-mono,monospace)\\">" + escHtml(host) + ":" + hp + "</td>"
          + "<td style=\\"padding:6px 8px;font-family:var(--font-mono,monospace)\\">" + cp + "</td></tr>";
      }}).join("");
    }}
    function applyConfigsPanelForSavedBackend() {{
      const isSl = __savedAccountBackend === "snowluma";
      const lbl = document.getElementById("lblCfgMid");
      if (lbl) lbl.textContent = isSl ? "runtime（SnowLuma）" : "napcat（NapCat）";
      const rowW = document.getElementById("rowCfgWebui");
      if (rowW) rowW.style.display = isSl ? "none" : "";
    }}
    function updateCfgDirtyHint() {{
      const h = document.getElementById("cfgProtocolDirtyHint");
      if (!h) return;
      h.style.display = currentProtocolSelect() !== __savedAccountBackend ? "block" : "none";
    }}
    async function loadHints() {{
      try {{
        const h = await api("/api/connection-hints");
        const el = document.getElementById("onebotHint");
        if (!h.onebot_configured) {{
          el.textContent = "OneBot 未就绪：请检查 .env 中 HOST / PORT / ACCESS_TOKEN。";
          return;
        }}
        el.textContent = "当前连接: " + h.onebot_ws_url;
      }} catch (err) {{
        document.getElementById("onebotHint").textContent = String(err.message || err);
      }}
    }}
    async function loadAccount(opts) {{
      const ov = document.getElementById("ovBody");
      const brief = !!(opts && opts.brief);
      const q = brief ? "?brief=1" : "";
      try {{
        const data = await api(`/api/accounts/${{encodeURIComponent(accountId)}}${{q}}`);
        const a = data.account;
        accountProcessRunning = !!a.process_running;
      let st = "";
      if (a.process_running) {{
        st = "运行中 · PID：" + (a.pid || "—");
        if (a.connected) st += " · 已连接";
      }} else if (a.running) {{
        st = "已连接（进程可能已脱离）";
      }} else if (a.launch_ready) {{
        st = "已停止";
      }} else {{
        st = (a.launch_issues || []).join("; ");
      }}
      const wu = a.native_webui_url || "";
      const note = a.native_webui_auth_note || "";
      const rtpw = a.snowluma_runtime_webui_password || "";
      let html = "<div><strong>" + String(st).replace(/</g, "&lt;") + "</strong></div>";
      html += '<div class="muted" style="margin-top:8px">版本: ' + escHtml(a.runtime_version || "未知") + "</div>";
      if (wu) {{
        html += '<div style="margin-top:8px"><a href="' + escHtml(wu) + '" target="_blank" rel="noopener">打开原生 WebUI</a></div>';
      }}
      if (a.snowluma_linux_docker) {{
        const nv = a.snowluma_docker_novnc;
        if (nv && nv.url) {{
          const defPw = !!nv.uses_default_vnc_password;
          html += '<div style="margin-top:10px;padding:10px 12px;border:1px solid var(--bd);border-radius:var(--radius);background:var(--bg1);max-width:640px">';
          html += '<div style="font-weight:700;font-size:0.92rem;margin-bottom:6px;color:var(--txt)">SnowLuma 桌面（noVNC）</div>';
          html += '<p class="muted" style="margin:0 0 8px;font-size:0.82rem;line-height:1.5">请在容器<strong>启动后</strong>使用下方链接进入桌面；在 noVNC 中连接 VNC 时填写口令。'
            + (defPw ? ' 未设置全局 <code>PALLAS_PROTOCOL_SNOWLUMA_DOCKER_VNC_PASSWD</code> 时，默认口令为 <span class="mono">vncpasswd</span>。' : ' 口令以服务端 <code>PALLAS_PROTOCOL_SNOWLUMA_DOCKER_VNC_PASSWD</code> 为准。')
            + '</p>';
          html += '<div style="margin-top:4px"><a class="btn secondary" href="' + escHtml(String(nv.url)) + '" target="_blank" rel="noopener">打开 noVNC</a>'
            + '<span class="muted" style="margin-left:10px;font-size:0.78rem">无法打开时可尝试同端口根路径 <span class="mono">/</span></span></div>';
          html += '</div>';
        }} else {{
          html += '<div class="muted" style="margin-top:8px;font-size:0.82rem;line-height:1.45">SnowLuma Docker：当前未发布 noVNC 宿主机端口，浏览器无法进桌面；请到「设置」填写或留空以自动分配端口。</div>';
        }}
      }}
      if (note) {{
        html += '<div class="muted" style="margin-top:8px;white-space:pre-wrap">' + escHtml(note) + "</div>";
      }}
      if (rtpw) {{
        const u = (a.snowluma_webui_default_user || "").trim();
        const ubit = u ? ('<span class="muted">用户名</span> <span class="mono">' + escHtml(u) + '</span> <span class="muted">·</span> ') : "";
        html += '<div class="row" style="margin-top:8px;flex-wrap:wrap;gap:8px;align-items:center">' + ubit + '<span class="muted">初始口令</span> <span class="mono">' + escHtml(rtpw) + '</span> <button type="button" class="btn secondary" data-copy-plain="' + encodeURIComponent(rtpw) + '">复制</button></div>';
      }}
      html += '<div class="muted" style="margin-top:8px">WORKDIR: ' + escHtml(a.account_data_dir || "") + "</div>";
      ov.innerHTML = html;
      if (brief) return;
      document.getElementById("display_name").value = a.display_name || "";
      document.getElementById("qq").value = a.qq || "";
      {{
        const pb = (a.protocol_backend || "napcat").toString().trim().toLowerCase();
        document.getElementById("protocol_backend").value = pb === "snowluma" ? "snowluma" : "napcat";
        __savedAccountBackend = pb === "snowluma" ? "snowluma" : "napcat";
        if (typeof shellPrettySyncSelect === "function") {{
          const s = document.getElementById("protocol_backend");
          if (s) shellPrettySyncSelect(s);
        }}
      }}
      window.__managedTagSaved = (a.managed_runtime_tag || "").trim();
      applySettingsForProtocolSelect();
      applyConfigsPanelForSavedBackend();
      document.getElementById("webui_port").value = a.webui_port != null ? String(a.webui_port) : "";
      document.getElementById("webui_token").value = a.webui_token || "";
      syncSnowlumaDockerVncRow(a);
      syncSnowlumaDockerPortMapCard(a);
      {{
        const hint = document.getElementById("webuiTokenHint");
        if (hint) {{
          const pb = (a.protocol_backend || "napcat").toString().trim().toLowerCase();
          if (pb === "snowluma" && !a.snowluma_runtime_webui_password && a.native_webui_auth_note) {{
            hint.textContent = a.native_webui_auth_note;
            hint.style.display = "block";
          }} else {{
            hint.textContent = "";
            hint.style.display = "none";
          }}
        }}
      }}
      document.getElementById("ws_url").value = a.ws_url || "";
      document.getElementById("ws_name").value = a.ws_name || "";
      document.getElementById("ws_token").value = a.ws_token || "";
        {{
          const row = document.getElementById("snowlumaInjectRow");
          if (row) {{
            const pb = (a.protocol_backend || "napcat").toString().trim().toLowerCase();
            row.style.display = pb === "snowluma" ? "flex" : "none";
          }}
        }}
      }} catch (e) {{
        const msg = String(e.message || e);
        if (ov) ov.innerHTML = '<div class="muted">加载失败：' + escHtml(msg) + "</div>";
        notify(msg, "err");
      }}
    }}
    async function pollAccLogs() {{
      try {{
        const data = await api(`/api/accounts/${{encodeURIComponent(accountId)}}/logs?lines=120`);
        const el = document.getElementById("accLogs");
        if (shouldPauseLiveLogDomWrite(el)) return;
        const lines = data.logs || [];
        const atBottom = el.scrollHeight - el.scrollTop - el.clientHeight < 60;
        el.textContent = lines.length ? lines.join("\\n") : "暂无进程输出";
        if (atBottom) el.scrollTop = el.scrollHeight;
      }} catch (e) {{
        const el = document.getElementById("accLogs");
        if (!shouldPauseLiveLogDomWrite(el)) el.textContent = String(e.message || e);
      }}
    }}
    async function loadJsonCfgs() {{
      const c = await api(`/api/accounts/${{encodeURIComponent(accountId)}}/configs`);
      document.getElementById("tj_onebot").value = JSON.stringify(c.onebot || {{}}, null, 2);
      if (__savedAccountBackend === "snowluma") {{
        document.getElementById("tj_napcat").value = JSON.stringify(c.runtime || {{}}, null, 2);
        document.getElementById("tj_webui").value = "";
      }} else {{
        document.getElementById("tj_napcat").value = JSON.stringify(c.napcat || {{}}, null, 2);
        document.getElementById("tj_webui").value = JSON.stringify(c.webui || {{}}, null, 2);
      }}
    }}
    async function saveSettings() {{
      const el = document.getElementById("setMsg");
      el.textContent = "";
      try {{
        const wport = document.getElementById("webui_port").value.trim();
        const wn = parseInt(wport, 10);
        const pbSave = (document.getElementById("protocol_backend").value || "napcat").trim().toLowerCase();
        const body = {{
          display_name: document.getElementById("display_name").value.trim(),
          protocol_backend: pbSave === "snowluma" ? "snowluma" : "napcat",
          managed_runtime_tag: (document.getElementById("managed_runtime_tag") || {{}}).value || "",
          ws_url: document.getElementById("ws_url").value.trim(),
          ws_name: document.getElementById("ws_name").value.trim(),
          ws_token: document.getElementById("ws_token").value,
        }};
        if (pbSave !== "snowluma") {{
          body.webui_token = document.getElementById("webui_token").value.trim();
        }} else {{
          const rowD = document.getElementById("rowSnowlumaDockerVnc");
          if (rowD && rowD.style.display !== "none") {{
            const nns = String((document.getElementById("snowluma_docker_host_novnc_port") || {{}}).value || "").trim();
            const vvs = String((document.getElementById("snowluma_docker_host_vnc_port") || {{}}).value || "").trim();
            body.snowluma_docker_host_novnc_port = nns === "" ? null : parseInt(nns, 10);
            body.snowluma_docker_host_vnc_port = vvs === "" ? null : parseInt(vvs, 10);
          }}
        }}
        if (wport && !Number.isNaN(wn)) body.webui_port = wn;
        let restartNow = true;
        if (accountProcessRunning) {{
          restartNow = confirm("当前账号正在运行，保存后需要重启进程才能生效。是否立即重启？");
        }}
        showPageLoading("保存中…");
        const put = await api(`/api/accounts/${{encodeURIComponent(accountId)}}?restart=${{restartNow ? "1" : "0"}}`, {{
          method: "PUT", headers: {{ "Content-Type": "application/json" }}, body: JSON.stringify(body),
        }});
        showPageLoading("读取最新数据…");
        await loadAccount();
        el.textContent = put.restarted ? "已保存并已重启进程。" : (put.needs_restart ? "已保存，重启后生效。" : "已保存。");
        notify(el.textContent, "ok");
      }} catch (e) {{
        el.textContent = String(e.message || e);
      }} finally {{
        hidePageLoading();
      }}
    }}
    async function saveConfigs() {{
      const el = document.getElementById("cfgMsg");
      el.textContent = "";
      try {{
        if (currentProtocolSelect() !== __savedAccountBackend) {{
          const msg = "请先在「设置」中保存协议端类型，再保存原始配置。";
          el.textContent = msg;
          notify(msg, "warn");
          return;
        }}
        let payload;
        if (__savedAccountBackend === "snowluma") {{
          payload = {{
            onebot: JSON.parse(document.getElementById("tj_onebot").value || "{{}}"),
            runtime: JSON.parse(document.getElementById("tj_napcat").value || "{{}}"),
          }};
        }} else {{
          payload = {{
            onebot: JSON.parse(document.getElementById("tj_onebot").value || "{{}}"),
            napcat: JSON.parse(document.getElementById("tj_napcat").value || "{{}}"),
            webui: JSON.parse(document.getElementById("tj_webui").value || "{{}}"),
          }};
        }}
        let restartNow = true;
        if (accountProcessRunning) {{
          restartNow = confirm("当前账号正在运行，配置变更需重启后生效。是否立即重启？");
        }}
        showPageLoading("保存中…");
        const cfgPut = await api(`/api/accounts/${{encodeURIComponent(accountId)}}/configs?restart=${{restartNow ? "1" : "0"}}`, {{
          method: "PUT", headers: {{ "Content-Type": "application/json" }}, body: JSON.stringify(payload),
        }});
        showPageLoading("读取最新数据…");
        await loadJsonCfgs();
        el.textContent = cfgPut.restarted ? "已写入磁盘并已重启进程。" : (cfgPut.needs_restart ? "已写入磁盘，重启后生效。" : "已写入磁盘。");
        notify(el.textContent, "ok");
      }} catch (e) {{
        el.textContent = String(e.message || e);
      }} finally {{
        hidePageLoading();
      }}
    }}
    function showPageLoading(label = "加载中…") {{
      const ov = document.getElementById("pageOverlay");
      const lb = document.getElementById("pageOverlayLabel");
      if (lb) lb.textContent = label;
      if (ov) ov.classList.add("visible");
    }}
    function hidePageLoading() {{
      const ov = document.getElementById("pageOverlay");
      if (ov) ov.classList.remove("visible");
    }}
    function notify(msg, level = "ok") {{
      const host = document.getElementById("statusbar");
      const el = document.createElement("div");
      el.className = `toast ${{level}}`;
      el.textContent = String(msg || "");
      host.appendChild(el);
      setTimeout(() => el.remove(), 4200);
    }}
    function copyLogText(id) {{
      const el = document.getElementById(id);
      const t = (el && el.textContent) ? el.textContent : "";
      if (!String(t).trim()) {{ notify("当前无内容可复制", "warn"); return; }}
      navigator.clipboard.writeText(t).then(() => notify("已复制到剪贴板", "ok"))
        .catch((e) => notify(String(e.message || e), "err"));
    }}
    function accBtnLoad(btn, text) {{
      if (!btn) return;
      btn.disabled = true;
      btn.dataset.idle = btn.textContent;
      btn.innerHTML = `<span class="spinner"></span>${{text}}`;
    }}
    function accBtnReset(btn) {{
      if (!btn) return;
      btn.disabled = false;
      btn.textContent = btn.dataset.idle || btn.textContent;
    }}
    async function doStart() {{
      const btn = event?.currentTarget || null;
      accBtnLoad(btn, "启动中…");
      try {{
        await api(`/api/accounts/${{encodeURIComponent(accountId)}}/start`, {{ method: "POST" }});
        await loadAccount();
        await pollAccQrcode(true);
        await pollAccLogs();
        notify("启动成功", "ok");
      }} catch (e) {{
        notify(e.message || e, "err");
      }} finally {{ accBtnReset(btn); }}
    }}
    async function doStop() {{
      const btn = event?.currentTarget || null;
      accBtnLoad(btn, "停止中…");
      try {{
        await api(`/api/accounts/${{encodeURIComponent(accountId)}}/stop`, {{ method: "POST" }});
        await loadAccount();
        notify("停止成功", "warn");
      }} catch (e) {{
        notify(e.message || e, "err");
      }} finally {{ accBtnReset(btn); }}
    }}
    async function doRestart() {{
      const btn = event?.currentTarget || null;
      accBtnLoad(btn, "重启中…");
      try {{
        await api(`/api/accounts/${{encodeURIComponent(accountId)}}/restart`, {{ method: "POST" }});
        await loadAccount();
        await pollAccQrcode(true);
        await pollAccLogs();
        notify("重启成功", "ok");
      }} catch (e) {{
        notify(e.message || e, "err");
      }} finally {{ accBtnReset(btn); }}
    }}
    async function doDelete() {{
      if (!confirm("确定删除该账号？")) return;
      const btn = event?.currentTarget || null;
      accBtnLoad(btn, "删除中…");
      try {{
        await api(`/api/accounts/${{encodeURIComponent(accountId)}}`, {{ method: "DELETE" }});
        location.href = document.getElementById("backDash").href;
      }} catch (e) {{
        notify(e.message || e, "err");
      }} finally {{
        accBtnReset(btn);
      }}
    }}
    accNbWireRunlogUi();
    (function init() {{
{token_sync_js}
      const u = new URL(location.href);
      const tabn = (u.searchParams.get("tab") || "overview").toLowerCase();
      tab(["overview","settings","configs"].includes(tabn) ? tabn : "overview");
    }})();
    loadHints().catch(() => {{}});
    bootAccountOverview();
    setInterval(() => {{
      if (document.hidden || activeTab !== "overview") return;
      loadAccount({{ brief: true }}).catch(() => {{}});
    }}, 10000);
    setInterval(() => {{
      if (document.hidden || activeTab !== "overview") return;
      pollAccLogs();
    }}, 8000);
    setInterval(() => {{
      if (document.hidden || activeTab !== "overview") return;
      pollAccQrcode(false);
    }}, 8000);
  </script>
  <div id="pageOverlay" class="page-overlay">
    <div class="page-overlay-inner">
      <div class="page-overlay-spinner"></div>
      <div class="page-overlay-label" id="pageOverlayLabel">保存中…</div>
    </div>
  </div>
  <div id="statusbar" class="statusbar"></div>
</body>
</html>
"""

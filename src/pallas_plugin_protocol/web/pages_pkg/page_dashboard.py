# ruff: noqa: E501
"""协议仪表盘页。"""

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


def render_dashboard(base_path: str, pallas_console_http_base: str = "/pallas") -> str:
    path = base_path.rstrip("/") or resolve_public_mount_path(
        path_override="", implementation_slug=""
    )
    p = json.dumps(path)
    common_api_js = _render_common_api_js()
    token_sync_js = _render_hidden_token_sync_js("backDash")
    shell_open = render_protocol_shell_open(
        path,
        pallas_console_http_base,
        active="dashboard",
        page_title="仪表盘",
        page_desc="协议账号与运行日志",
        topbar_actions=(
            '<button class="btn secondary" id="btnRefresh" type="button" onclick="refreshAccounts()">刷新</button>'
        ),
    )
    shell_close = render_protocol_shell_close(
        path, active="dashboard", pallas_console_http_base=pallas_console_http_base
    )
    new_href = html_escape(f"{path}/new", quote=True)
    webui_base = (pallas_console_http_base or "/pallas").rstrip("/") or "/pallas"
    webui_protocol_href = html_escape(f"{webui_base}/protocol", quote=True)
    webui_create_href = html_escape(f"{webui_base}/protocol/create", quote=True)
    webui_import_href = html_escape(f"{webui_base}/protocol/import", quote=True)
    webui_assets_href = html_escape(f"{webui_base}/protocol/assets", quote=True)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
{shell_head_assets(path)}  <title>仪表盘 · 协议端</title>
</head>
<body data-base-path="{html_escape(path, quote=True)}">
  <input type="hidden" id="token" value="" autocomplete="off" />
{shell_open}
    <div class="proto-webui-banner" id="protoWebuiBanner" role="status">
      <div class="proto-webui-banner__main">
        <strong>推荐使用 Pallas Bot WebUI</strong>
        <span class="muted">创建账号、批量导入与协议资产已并入 Bot 控制台，体验与窄屏布局更一致。</span>
      </div>
      <div class="proto-webui-banner__links">
        <a class="btn btn--primary" href="{webui_protocol_href}">打开 WebUI 协议页</a>
        <a class="btn secondary" href="{webui_create_href}">创建</a>
        <a class="btn secondary" href="{webui_import_href}">导入</a>
        <a class="btn secondary" href="{webui_assets_href}">资产</a>
        <button type="button" class="btn linkish proto-webui-banner__dismiss" id="protoWebuiBannerDismiss">不再显示</button>
      </div>
    </div>
    <div class="panel proto-panel proto-panel--accounts">
      <div class="panel__hd panel__hd--split proto-panel__hd">
        <h2 class="panel__title">协议账号</h2>
        <div class="proto-panel__toolbar">
        <a href="{new_href}" class="btn btn--primary proto-panel__hd-create">+ 创建账号</a>
        <div class="row-actions proto-panel__hd-batch">
        <button class="btn secondary" id="btnToggleAll" type="button" onclick="toggleAllAccounts(this)">一键启动全部</button>
        <button class="btn secondary" id="btnStopSelected" type="button" onclick="stopSelectedAccounts(this)" disabled>停止所选</button>
        <button class="btn secondary" id="btnRestartAll" type="button" onclick="restartAllAccounts(this)">一键重启全部</button>
        <span class="muted proto-panel__hd-count" id="selectedCountHint">已选 0</span>
        </div>
        </div>
      </div>
      <div class="panel__bd">
      <div class="kpi-grid" id="kpis"></div>
      <div class="toolbar">
        <input id="search" class="grow" placeholder="筛选：输入 QQ / 实例名 / 账号 ID" oninput="renderAccounts()" />
        <div class="view-toggle" role="tablist" aria-label="视图切换">
          <button id="btnViewCard" class="btn active" type="button" onclick="setViewMode('card')">卡片视图</button>
          <button id="btnViewTable" class="btn" type="button" onclick="setViewMode('table')">表格视图</button>
        </div>
        <label class="pill" style="cursor:pointer">
          <input id="selectAllFiltered" type="checkbox" style="margin-right:6px" onchange="toggleSelectAllFiltered(this.checked)" />
          全选当前列表
        </label>
        <label class="pill" style="cursor:pointer">
          <input id="autoRefresh" type="checkbox" checked style="margin-right:6px" />
          自动刷新日志
        </label>
      </div>
      <div id="cards" class="grid proto-account-grid"></div>
      <div id="tableWrap" class="table-wrap" style="display:none"></div>
      </div>
    </div>

    <div class="panel proto-panel proto-panel--log">
      <div class="sl-runlog" id="nbLogCard">
        <div class="sl-runlog-hd">
          <div class="sl-runlog-titles">
            <h2 style="margin:0;font-size:1.05rem">运行日志<span class="sl-runlog-bad wait" id="nbLogStreamBadge">连接中</span></h2>
            <p style="margin:4px 0 0;font-size:0.78rem;color:var(--muted)" id="nbLogSubLine">
              最近 <span id="nbLogFilteredN">0</span> / <span id="nbLogTotalN">0</span> 条 · SSE 推送
            </p>
          </div>
          <div class="sl-runlog-tools">
            <input type="search" id="nbLogFilter" class="grow" placeholder="搜索消息 / 模块 / 级别" />
            <select id="nbLogScope" class="sl-runlog-scope" title="范围">
              <option value="all">全部</option>
              <option value="webui">控制台</option>
              <option value="protocol">协议</option>
            </select>
            <button type="button" class="btn secondary" id="nbLogPauseBtn">暂停</button>
            <button type="button" class="btn secondary" id="nbLogRefreshBtn">刷新</button>
            <button type="button" class="btn secondary" id="nbLogClearBtn">清空视图</button>
            <button type="button" class="btn secondary" id="nbLogCopyBtn">复制</button>
          </div>
        </div>
        <div class="sl-runlog-levels" id="nbLogLevels"></div>
        <div class="sl-runlog-viewport" id="nbLogViewport" tabindex="0" title="可框选复制；框选或聚焦时暂停自动滚动">
          <div class="sl-runlog-inner" id="nbLogRows"></div>
        </div>
      </div>
    </div>
{shell_close}
  <script>
    const basePath = {p};
{common_api_js}
{token_sync_js}
    let accountRows = [];
    let viewMode = "card";
    const selectedAccountIds = new Set();
    let lastAccountsRenderSig = "";
    let pendingSilentAccountsDom = false;
    const PALLAS_FAV_BOT_ACCOUNTS_KEY = "pallas_fav_bot_accounts_v1";
    let botFavoriteAccounts = readBotFavoriteAccounts();
    function readBotFavoriteAccounts() {{
      try {{
        const raw = localStorage.getItem(PALLAS_FAV_BOT_ACCOUNTS_KEY);
        if (!raw) return new Set();
        const data = JSON.parse(raw);
        if (!Array.isArray(data)) return new Set();
        const s = new Set();
        for (const x of data) {{
          const n = typeof x === "number" ? x : parseInt(String(x), 10);
          if (Number.isFinite(n) && n > 0) s.add(Math.floor(n));
        }}
        return s;
      }} catch (e) {{
        return new Set();
      }}
    }}
    function writeBotFavoriteAccounts(s) {{
      try {{
        localStorage.setItem(PALLAS_FAV_BOT_ACCOUNTS_KEY, JSON.stringify([...s].sort((a, b) => a - b)));
      }} catch (e) {{}}
    }}
    function accountFavoriteNumber(a) {{
      const q = parseInt(String(a?.qq ?? a?.id ?? "").replace(/\\s/g, ""), 10);
      if (Number.isFinite(q) && q > 0) return Math.floor(q);
      return null;
    }}
    function isFavoriteAccount(a) {{
      const n = accountFavoriteNumber(a);
      return n != null && botFavoriteAccounts.has(n);
    }}
    function toggleFavoriteAccountById(id, ev) {{
      if (ev) {{
        ev.preventDefault();
        ev.stopPropagation();
      }}
      const a = (accountRows || []).find((x) => String(x.id) === String(id));
      if (!a) return;
      const n = accountFavoriteNumber(a);
      if (n == null) return;
      const s = new Set(botFavoriteAccounts);
      if (s.has(n)) s.delete(n);
      else s.add(n);
      botFavoriteAccounts = s;
      writeBotFavoriteAccounts(s);
      accountRows = sortAccountsDashboard(accountRows);
      renderAccounts();
    }}
    if (typeof window !== "undefined") {{
      window.addEventListener("storage", (ev) => {{
        if (ev.key !== PALLAS_FAV_BOT_ACCOUNTS_KEY) return;
        botFavoriteAccounts = readBotFavoriteAccounts();
        accountRows = sortAccountsDashboard(accountRows);
        renderAccounts();
      }});
    }}
    function accountFavStarHtml(a) {{
      const n = accountFavoriteNumber(a);
      if (n == null) return "";
      const on = botFavoriteAccounts.has(n);
      const id = escHtmlDash(String(a.id));
      const title = on ? "取消收藏" : "收藏";
      return `<button type="button" class="inst-fav-star data-card-fav-star" aria-pressed="${{on ? "true" : "false"}}" title="${{title}}" onclick="toggleFavoriteAccountById('${{id}}', event)">★</button>`;
    }}
    function accountsListSignature(rows) {{
      return (rows || []).map((a) => {{
        const id = String(a.id ?? a.qq ?? "").trim();
        const qq = String(a.qq ?? "").trim();
        const connected = a.connected ? "1" : "0";
        const running = (a.process_running || a.running) ? "1" : "0";
        return `${{id}}:${{qq}}:${{connected}}:${{running}}`;
      }}).join("|");
    }}
    function flushPendingAccountsDom() {{
      if (!pendingSilentAccountsDom) return;
      pendingSilentAccountsDom = false;
      const sig = accountsListSignature(accountRows);
      if (sig === lastAccountsRenderSig) return;
      lastAccountsRenderSig = sig;
      renderKpis(accountRows);
      pruneSelectedAccountIds();
      renderAccounts();
      updateToggleAllButton();
    }}
    onProtoMainInnerScrollEnd(flushPendingAccountsDom);
    function setBusy(el, busy, idleText = "刷新", busyText = "刷新中...") {{
      if (!el) return;
      el.disabled = !!busy;
      el.classList.toggle("busy", !!busy);
      if (typeof el.textContent === "string") el.textContent = busy ? busyText : idleText;
    }}
    (function initPagePrefs() {{
      initPallasShellThemeFromStorage();
      applyShellUiPrefsFromStorage();
      initProtocolShellChrome();
    }})();
    function notify(msg, level = "ok") {{
      const host = document.getElementById("statusbar");
      const el = document.createElement("div");
      el.className = `toast ${{level}}`;
      el.textContent = String(msg || "");
      host.appendChild(el);
      setTimeout(() => el.remove(), 4200);
    }}
    function nbFormatTime(iso) {{
      try {{
        const d = new Date(iso);
        if (Number.isNaN(d.getTime())) return String(iso || "");
        return d.toLocaleTimeString();
      }} catch (e) {{ return String(iso || ""); }}
    }}
    const NB_LEVELS = ["debug", "info", "success", "warn", "error"];
    let nbLogEntries = [];
    let nbLogPaused = false;
    let nbLogFilter = "";
    let nbLogLevels = new Set(NB_LEVELS);
    let nbLogEs = null;
    function nbStreamBadge(text, kind) {{
      const el = document.getElementById("nbLogStreamBadge");
      if (!el) return;
      el.textContent = text;
      el.className = "sl-runlog-bad " + (kind === "ok" ? "ok" : kind === "err" ? "err" : "wait");
    }}
    function nbLevelUiClass(lv) {{
      const u = String(lv || "").toLowerCase();
      if (u === "debug") return "sl-lv-debug";
      if (u === "success") return "sl-lv-success";
      if (u === "warn") return "sl-lv-warn";
      if (u === "error") return "sl-lv-error";
      return "sl-lv-info";
    }}
    function nbFiltered() {{
      const f = (nbLogFilter || "").trim().toLowerCase();
      return nbLogEntries.filter((x) => {{
        if (!nbLogLevels.has(String(x.level || "").toLowerCase())) return false;
        if (!f) return true;
        const m = String(x.message || "").toLowerCase();
        const sc = String(x.scope || "").toLowerCase();
        const lv = String(x.level || "").toLowerCase();
        return m.includes(f) || sc.includes(f) || lv.includes(f);
      }});
    }}
    function nbShouldPauseDom() {{
      const vp = document.getElementById("nbLogViewport");
      if (!vp) return false;
      return shouldPauseLiveLogDomWrite(vp);
    }}
    function nbRender() {{
      const rows = document.getElementById("nbLogRows");
      const sub = document.getElementById("nbLogFilteredN");
      const tot = document.getElementById("nbLogTotalN");
      if (tot) tot.textContent = String(nbLogEntries.length);
      const list = nbFiltered();
      if (sub) sub.textContent = String(list.length);
      if (!rows) return;
      if (!list.length) {{
        rows.innerHTML = '<div class="sl-runlog-empty">暂无日志</div>';
        return;
      }}
      rows.innerHTML = list.map((x) => {{
        const lv = String(x.level || "").toUpperCase();
        const t = nbFormatTime(x.time);
        const sc = escHtmlDash(x.scope || "");
        const msg = escHtmlDash(x.message || "");
        const lc = nbLevelUiClass(x.level);
        return `<div class="sl-runlog-row"><span class="sl-runlog-t">${{t}}</span><span class="sl-runlog-lv ${{lc}}">${{lv}}</span><span class="sl-runlog-sc">[${{sc}}]</span><span class="sl-runlog-msg">${{msg}}</span></div>`;
      }}).join("");
    }}
    let nbLogRenderDeferred = false;
    let nbRenderScheduled = 0;
    function scheduleNbRender() {{
      if (nbRenderScheduled) return;
      if (isProtoMainInnerScrolling() || nbShouldPauseDom()) {{
        nbLogRenderDeferred = true;
        return;
      }}
      nbRenderScheduled = requestAnimationFrame(() => {{
        nbRenderScheduled = 0;
        if (nbShouldPauseDom()) {{
          nbLogRenderDeferred = true;
          return;
        }}
        nbRender();
        nbScrollToEnd();
      }});
    }}
    function flushDeferredNbLogRender() {{
      if (!nbLogRenderDeferred) return;
      nbLogRenderDeferred = false;
      scheduleNbRender();
    }}
    onProtoMainInnerScrollEnd(flushDeferredNbLogRender);
    function nbScrollToEnd() {{
      if (nbLogPaused) return;
      if (nbShouldPauseDom()) return;
      const vp = document.getElementById("nbLogViewport");
      if (vp) vp.scrollTop = vp.scrollHeight;
    }}
    function nbInitLevelPills() {{
      const host = document.getElementById("nbLogLevels");
      if (!host) return;
      host.innerHTML = NB_LEVELS.map((lv) =>
        `<button type="button" data-nb-lv="${{lv}}" class="on">${{String(lv).toUpperCase()}}</button>`
      ).join("");
      host.querySelectorAll("[data-nb-lv]").forEach((btn) => {{
        btn.addEventListener("click", () => {{
          const lv = btn.getAttribute("data-nb-lv");
          if (nbLogLevels.has(lv)) nbLogLevels.delete(lv);
          else nbLogLevels.add(lv);
          btn.classList.toggle("on", nbLogLevels.has(lv));
          btn.classList.toggle("off", !nbLogLevels.has(lv));
          nbRender();
        }});
      }});
    }}
    async function nbLoadInitial() {{
      const scopeEl = document.getElementById("nbLogScope");
      const sc = scopeEl ? scopeEl.value : "all";
      const data = await api(`/api/nonebot-logs?lines=180&scope=${{encodeURIComponent(sc)}}`);
      nbLogEntries = Array.isArray(data.entries) ? data.entries.slice() : [];
      nbRender();
      nbScrollToEnd();
    }}
    function nbClear() {{
      if (!confirm("清空当前日志视图？仅影响浏览器展示，不清服务端缓冲。")) return;
      nbLogEntries = [];
      nbRender();
    }}
    function nbCopy() {{
      const lines = nbFiltered().map((x) =>
        `${{nbFormatTime(x.time)}} ${{String(x.level || "").toUpperCase()}} [${{x.scope}}] ${{x.message}}`
      );
      const t = lines.join("\\n");
      if (!String(t).trim()) {{ notify("当前无可复制内容", "warn"); return; }}
      navigator.clipboard.writeText(t).then(() => notify("已复制", "ok")).catch((e) => notify(String(e.message || e), "err"));
    }}
    function nbStopSse() {{
      if (nbLogEs) {{
        try {{ nbLogEs.close(); }} catch (e) {{}}
        nbLogEs = null;
      }}
    }}
    function nbStartSse() {{
      nbStopSse();
      const tok = getSessionToken();
      const scopeEl = document.getElementById("nbLogScope");
      const sc = scopeEl ? scopeEl.value : "all";
      let url = `${{basePath}}/api/nonebot-logs/stream?scope=${{encodeURIComponent(sc)}}`;
      if (tok) url += `&token=${{encodeURIComponent(tok)}}`;
      nbStreamBadge("连接中", "wait");
      const es = new EventSource(url);
      nbLogEs = es;
      es.onopen = () => nbStreamBadge("实时", "ok");
      es.onerror = () => nbStreamBadge("重连中", "err");
      es.onmessage = (ev) => {{
        try {{
          const row = JSON.parse(ev.data);
          if (row && row.type === "ready") return;
          if (!row || typeof row.id !== "number") return;
          if (nbLogPaused) return;
          nbLogEntries = [...nbLogEntries.filter((it) => it.id !== row.id), row].slice(-1000);
          scheduleNbRender();
        }} catch (e) {{}}
      }};
    }}
    function nbWireRunlogUi() {{
      nbInitLevelPills();
      document.getElementById("nbLogFilter")?.addEventListener("input", (e) => {{
        nbLogFilter = (e.target && e.target.value) || "";
        nbRender();
      }});
      document.getElementById("nbLogPauseBtn")?.addEventListener("click", () => {{
        nbLogPaused = !nbLogPaused;
        const b = document.getElementById("nbLogPauseBtn");
        if (b) b.textContent = nbLogPaused ? "继续" : "暂停";
        if (!nbLogPaused) nbScrollToEnd();
      }});
      document.getElementById("nbLogRefreshBtn")?.addEventListener("click", () => {{
        nbLoadInitial().catch((e) => notify(e.message || e, "err"));
      }});
      document.getElementById("nbLogClearBtn")?.addEventListener("click", nbClear);
      document.getElementById("nbLogCopyBtn")?.addEventListener("click", nbCopy);
      document.getElementById("nbLogScope")?.addEventListener("change", () => {{
        nbLoadInitial().catch(() => {{}});
        nbStartSse();
      }});
    }}
    function accountStatusMeta(a) {{
      if (a.connected) return {{ text: "已连接", cls: "data-conn-capsule data-conn-capsule--on" }};
      if (a.process_running) return {{ text: "运行中", cls: "data-conn-capsule data-conn-capsule--run" }};
      if (a.launch_ready) return {{ text: "已停止", cls: "data-conn-capsule data-conn-capsule--off" }};
      return {{ text: "异常", cls: "data-conn-capsule data-conn-capsule--off" }};
    }}
    function accountWebuiBlockHtml(a) {{
      const pb = String(a.protocol_backend || "napcat").toLowerCase();
      const wu = a.native_webui_url || "";
      if (!wu) return "";
      const slPw = String(a.snowluma_runtime_webui_password || "").trim();
      const wtok = String(a.webui_token || "").replace(/</g, "");
      if (pb === "snowluma") {{
        return (`<div class="data-summary-card__row"><span class="data-summary-card__label">内置 WebUI</span>`
          + `<span class="data-summary-card__val data-summary-card__val--link"><a href="${{wu}}" target="_blank" rel="noopener">SnowLuma</a></span></div>`
          + (slPw
            ? (`<div class="data-summary-card__row"><span class="data-summary-card__label">临时密码</span>`
              + `<span class="data-summary-card__val"><span class="mono">${{escHtmlDash(slPw)}}</span> `
              + `<button type="button" class="btn secondary" style="font-size:0.78rem;padding:4px 8px;margin-left:6px" data-copy-plain="${{encodeURIComponent(slPw)}}">复制</button></span></div>`)
            : ""));
      }}
      return (`<div class="data-summary-card__row"><span class="data-summary-card__label">内置 WebUI</span>`
        + `<span class="data-summary-card__val data-summary-card__val--link"><a href="${{wu}}" target="_blank" rel="noopener">NapCat</a></span></div>`
        + `<div class="data-summary-card__row"><span class="data-summary-card__label">token</span>`
        + `<span class="data-summary-card__val mono">${{escHtmlDash(wtok)}}</span></div>`);
    }}
    function openAccount(id) {{
      location.href = `${{basePath}}/account/${{encodeURIComponent(id)}}`;
    }}
    function escHtmlDash(s) {{
      return String(s ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }}
    function qqAvatarUrl(uin) {{
      const n = String(uin ?? "").replace(/\\s/g, "");
      if (!/^\\d+$/.test(n)) return "";
      return `https://q1.qlogo.cn/g?b=qq&nk=${{encodeURIComponent(n)}}&s=160`;
    }}
    function accCardAvatarHtml(qqOrId) {{
      const q = String(qqOrId ?? "").trim();
      const url = qqAvatarUrl(q);
      const label = escHtmlDash(q ? q.slice(-2) : "?");
      if (!url) {{
        return `<div class="acc-card-avatar"><span class="acc-card-avatar-fallback">${{label}}</span></div>`;
      }}
      return `<div class="acc-card-avatar"><img src="${{url}}" alt="" width="48" height="48" loading="lazy" decoding="async" onerror="this.style.display='none';var f=this.nextElementSibling;if(f)f.style.display='flex';" /><span class="acc-card-avatar-fallback" style="display:none">${{label}}</span></div>`;
    }}
    function getFilteredAccountRows() {{
      const q = (document.getElementById("search").value || "").trim().toLowerCase();
      if (!q) return accountRows;
      return accountRows.filter((a) => {{
        return String(a.id || "").toLowerCase().includes(q)
          || String(a.qq || "").toLowerCase().includes(q)
          || String(a.display_name || "").toLowerCase().includes(q);
      }});
    }}
    function accountSelectCheckbox(id) {{
      const on = selectedAccountIds.has(id) ? " checked" : "";
      return `<label class="acc-select" onclick="event.stopPropagation()"><input type="checkbox"${{on}} onchange="toggleAccountSelected('${{escHtmlDash(id)}}', this.checked)" aria-label="选择账号" /><span class="acc-select__box" aria-hidden="true"></span></label>`;
    }}
    function toggleAccountSelected(id, checked) {{
      if (checked) selectedAccountIds.add(id);
      else selectedAccountIds.delete(id);
      updateSelectionUi();
      syncSelectAllCheckbox();
    }}
    function syncSelectAllCheckbox() {{
      const box = document.getElementById("selectAllFiltered");
      if (!box) return;
      const rows = getFilteredAccountRows();
      if (!rows.length) {{
        box.checked = false;
        box.indeterminate = false;
        return;
      }}
      const n = rows.filter((a) => selectedAccountIds.has(a.id)).length;
      box.checked = n > 0 && n === rows.length;
      box.indeterminate = n > 0 && n < rows.length;
    }}
    function toggleSelectAllFiltered(checked) {{
      getFilteredAccountRows().forEach((a) => {{
        if (checked) selectedAccountIds.add(a.id);
        else selectedAccountIds.delete(a.id);
      }});
      renderAccounts();
      updateSelectionUi();
    }}
    function updateSelectionUi() {{
      const n = selectedAccountIds.size;
      const btn = document.getElementById("btnStopSelected");
      if (btn) btn.disabled = n === 0;
      const hint = document.getElementById("selectedCountHint");
      if (hint) hint.textContent = "已选 " + n;
    }}
    function pruneSelectedAccountIds() {{
      const valid = new Set((accountRows || []).map((a) => a.id));
      for (const id of [...selectedAccountIds]) {{
        if (!valid.has(id)) selectedAccountIds.delete(id);
      }}
      updateSelectionUi();
      syncSelectAllCheckbox();
    }}
    async function stopSelectedAccounts(btn) {{
      const ids = [...selectedAccountIds];
      if (!ids.length) {{
        notify("请先勾选要停止的账号", "warn");
        return;
      }}
      btnLoad(btn, "停止中…");
      try {{
        const job = await runAccountBatch("stop", ids);
        await refreshAccounts({{ silent: true }});
        const failed = (job.results || []).filter((r) => !r.ok).length;
        notify(failed ? `已停止 ${{ids.length - failed}} 个，${{failed}} 个失败` : "已停止 " + ids.length + " 个账号", failed ? "warn" : "warn");
      }} catch (e) {{
        notify(e.message || e, "err");
      }} finally {{
        btnReset(btn);
      }}
    }}
    function renderKpis(rows) {{
      const total = rows.length;
      const running = rows.filter((x) => !!x.process_running).length;
      const connected = rows.filter((x) => !!x.connected).length;
      const bad = rows.filter((x) => !x.launch_ready).length;
      const el = document.getElementById("kpis");
      const stat = (label, value) => (
        `<div class="stat-card stat-card--dense card"><div class="card__body">`
        + `<div class="stat-card__label">${{label}}</div><div class="stat-card__value">${{value}}</div></div></div>`
      );
      el.innerHTML = stat("账号总数", total) + stat("运行中", running) + stat("已连接", connected) + stat("异常", bad);
    }}
    function renderAccounts() {{
      const mode = viewMode || "card";
      const rows = getFilteredAccountRows();
      const g = document.getElementById("cards");
      const tw = document.getElementById("tableWrap");
      g.innerHTML = "";
      tw.innerHTML = "";
      if (mode === "table") {{
        g.style.display = "none";
        tw.style.display = "block";
        const body = rows.map((a) => {{
          const stMeta = accountStatusMeta(a);
          const pb = String(a.protocol_backend || "napcat").toLowerCase();
          const slPw = String(a.snowluma_runtime_webui_password || "").trim();
          const wtok = String(a.webui_token || "").replace(/</g, "");
          const webuiCell = a.native_webui_url
            ? (pb === "snowluma"
              ? `<div class="acc-card-webui" style="margin:0;padding:0;border:0"><div class="acc-card-webui-line" style="margin:0">`
                + `<a href="${{a.native_webui_url}}" target="_blank" rel="noopener">SnowLuma WebUI</a></div>`
                + ((slPw
                  ? `<div class="acc-card-webui-line" style="margin-top:4px"><span class="muted">临时密码</span> <span class="mono">${{escHtmlDash(slPw)}}</span> `
                    + `<button type="button" class="btn secondary" style="font-size:0.72rem;padding:2px 6px" data-copy-plain="${{encodeURIComponent(slPw)}}">复制</button></div>`
                  : ""))
                + `</div>`
              : `<div class="acc-card-webui" style="margin:0;padding:0;border:0"><div class="acc-card-webui-line" style="margin:0">`
                + `<a href="${{a.native_webui_url}}" target="_blank" rel="noopener">NapCat WebUI</a></div>`
                + `<div class="acc-card-webui-line" style="margin-top:4px"><span class="muted">token</span> <span class="mono">${{escHtmlDash(wtok)}}</span></div></div>`)
            : "—";
          const running = !!a.process_running;
          const startStopBtn = running
            ? `<button class="btn secondary" type="button" onclick="stopAccount('${{a.id}}',this)">停止</button>`
            : `<button class="btn secondary" type="button" onclick="startAccount('${{a.id}}',this)">启动</button>`;
          return `<tr>
            <td data-label="选择" class="acc-td-select">${{accountSelectCheckbox(a.id)}}</td>
            <td data-label="实例名"><span class="acc-td-val">${{a.display_name || a.qq || a.id}}</span></td>
            <td data-label="QQ号"><span class="acc-td-val">${{a.qq || a.id}}</span></td>
            <td data-label="版本"><span class="acc-td-val">${{a.runtime_version || "未知"}}<div class="muted" style="font-size:0.75rem">${{a.runtime_source || "未知来源"}}</div></span></td>
            <td data-label="状态"><span class="acc-td-val"><span class="${{stMeta.cls}}">${{stMeta.text}}</span></span></td>
            <td data-label="内置 WebUI"><span class="acc-td-val">${{webuiCell}}</span></td>
            <td data-label="操作" class="acc-td-actions">
              <div class="row">
                <button class="btn acc-card-console-btn" type="button" onclick="openAccount('${{a.id}}')">控制台</button>
                ${{accountFavStarHtml(a)}}
                ${{startStopBtn}}
                <button class="btn secondary" type="button" onclick="restartAccount('${{a.id}}',this)">重启</button>
              </div>
            </td>
          </tr>`;
        }}).join("");
        tw.innerHTML = `<table class="acc-table acc-table--responsive"><thead><tr>
          <th class="acc-th-select">选择</th><th>实例名</th><th>QQ号</th><th>版本</th><th>状态</th><th>内置 WebUI</th><th>操作</th>
        </tr></thead><tbody>${{body || `<tr class="acc-table-empty"><td colspan="7" class="muted">无匹配账号</td></tr>`}}</tbody></table>`;
        syncSelectAllCheckbox();
        return;
      }}
      g.style.display = "grid";
      tw.style.display = "none";
      rows.forEach((a) => {{
        const stMeta = accountStatusMeta(a);
        const card = document.createElement("div");
        card.className = "data-summary-card data-summary-card--kv data-summary-card--bot card";
        const running = !!a.process_running;
        const startStopBtn = running
          ? `<button class="btn secondary" type="button" onclick="stopAccount('${{a.id}}',this)">停止</button>`
          : `<button class="btn secondary" type="button" onclick="startAccount('${{a.id}}',this)">启动</button>`;
        const webuiRows = accountWebuiBlockHtml(a);
        card.innerHTML = `
          <div class="data-summary-card__head data-summary-card__head--bot">
            ${{accountSelectCheckbox(a.id)}}
            ${{accCardAvatarHtml(a.qq || a.id)}}
            <div class="data-summary-card__head-main">
              <div class="data-summary-card__title-line">
                <div class="data-summary-card__primary">${{escHtmlDash(a.display_name || a.id)}}</div>
              </div>
              <div class="data-summary-card__secondary muted">QQ ${{escHtmlDash(a.qq || a.id)}}</div>
            </div>
            <div class="data-summary-card__head-badges">
              <span class="${{stMeta.cls}}">${{stMeta.text}}</span>
            </div>
            ${{accountFavStarHtml(a)}}
            <button class="btn acc-card-console-btn" type="button" onclick="openAccount('${{a.id}}')">控制台</button>
          </div>
          <div class="data-summary-card__body">
            <div class="data-summary-card__row">
              <span class="data-summary-card__label">版本</span>
              <span class="data-summary-card__val data-summary-card__val--version">${{escHtmlDash(a.runtime_version || "未知")}}</span>
            </div>
            <div class="data-summary-card__row">
              <span class="data-summary-card__label">归属</span>
              <span class="data-summary-card__val">${{escHtmlDash(a.runtime_source || "未知来源")}}</span>
            </div>
            ${{webuiRows}}
          </div>
          <div class="data-summary-card__tags data-summary-card__foot inst-card-actions">
            ${{startStopBtn}}
            <button class="btn secondary" type="button" onclick="restartAccount('${{a.id}}',this)">重启</button>
            <button class="btn danger" type="button" onclick="deleteAccount('${{a.id}}', this)">删除</button>
          </div>`;
        g.appendChild(card);
      }});
      syncSelectAllCheckbox();
    }}
    function setViewMode(mode) {{
      viewMode = mode === "table" ? "table" : "card";
      document.getElementById("btnViewCard").classList.toggle("active", viewMode === "card");
      document.getElementById("btnViewTable").classList.toggle("active", viewMode === "table");
      renderAccounts();
    }}
    async function refreshAccounts(opts) {{
      const silent = !!(opts && opts.silent);
      const force = !!(opts && opts.force) || !silent;
      const btn = document.getElementById("btnRefresh");
      if (!silent) setBusy(btn, true, "刷新", "刷新中...");
      try {{
        const data = await api("/api/accounts");
        accountRows = sortAccountsDashboard(data.accounts || []);
        const sig = accountsListSignature(accountRows);
        if (!force && sig === lastAccountsRenderSig) return;
        if (silent && isProtoMainInnerScrolling()) {{
          pendingSilentAccountsDom = true;
          return;
        }}
        pendingSilentAccountsDom = false;
        lastAccountsRenderSig = sig;
        renderKpis(accountRows);
        pruneSelectedAccountIds();
        renderAccounts();
        updateToggleAllButton();
        if (!silent) notify("已刷新账号列表", "ok");
      }} finally {{
        if (!silent) setBusy(btn, false, "刷新", "刷新中...");
      }}
    }}
    function btnLoad(btn, text) {{
      if (!btn) return;
      btn.disabled = true;
      btn.dataset.idle = btn.textContent;
      btn.innerHTML = `<span class="spinner"></span>${{text}}`;
    }}
    function btnReset(btn) {{
      if (!btn) return;
      btn.disabled = false;
      btn.textContent = btn.dataset.idle || btn.textContent;
    }}
    function isAccountRunning(a) {{
      return !!(a && a.process_running);
    }}
    function sortAccountsDashboard(rows) {{
      return [...(rows || [])].sort((a, b) => {{
        const fa = accountFavoriteNumber(a);
        const fb = accountFavoriteNumber(b);
        const favA = fa != null && botFavoriteAccounts.has(fa) ? 1 : 0;
        const favB = fb != null && botFavoriteAccounts.has(fb) ? 1 : 0;
        if (favA !== favB) return favB - favA;
        const ca = a.connected === true ? 1 : 0;
        const cb = b.connected === true ? 1 : 0;
        if (ca !== cb) return cb - ca;
        const an = String(a?.display_name || a?.qq || a?.id || "");
        const bn = String(b?.display_name || b?.qq || b?.id || "");
        const cmp = an.localeCompare(bn, "zh-CN", {{ sensitivity: "base", numeric: true }});
        if (cmp !== 0) return cmp;
        return String(a?.qq ?? a?.id ?? "").localeCompare(String(b?.qq ?? b?.id ?? ""), "zh-CN", {{ numeric: true }});
      }});
    }}
    function updateToggleAllButton() {{
      const btn = document.getElementById("btnToggleAll");
      if (!btn) return;
      const allRunning = accountRows.length > 0 && accountRows.every((a) => isAccountRunning(a));
      btn.textContent = allRunning ? "一键停止全部" : "一键启动全部";
    }}
    async function startAccount(id, btn) {{
      btnLoad(btn, "启动中…");
      try {{ await api(`/api/accounts/${{id}}/start`, {{ method: "POST" }}); await refreshAccounts({{ silent: true }}); notify(`已启动 ${{id}}`, "ok"); }}
      catch (e) {{ notify(e.message || e, "err"); }}
      finally {{ btnReset(btn); }}
    }}
    async function stopAccount(id, btn) {{
      btnLoad(btn, "停止中…");
      try {{ await api(`/api/accounts/${{id}}/stop`, {{ method: "POST" }}); await refreshAccounts({{ silent: true }}); notify(`已停止 ${{id}}`, "warn"); }}
      catch (e) {{ notify(e.message || e, "err"); }}
      finally {{ btnReset(btn); }}
    }}
    async function restartAccount(id, btn) {{
      btnLoad(btn, "重启中…");
      try {{ await api(`/api/accounts/${{id}}/restart`, {{ method: "POST" }}); await refreshAccounts({{ silent: true }}); notify(`已重启 ${{id}}`, "ok"); }}
      catch (e) {{ notify(e.message || e, "err"); }}
      finally {{ btnReset(btn); }}
    }}
    async function toggleAllAccounts(btn) {{
      if (!accountRows.length) {{
        notify("当前没有可操作实例", "warn");
        return;
      }}
      const allRunning = accountRows.every((a) => isAccountRunning(a));
      const action = allRunning ? "stop" : "start";
      const loadingText = allRunning ? "停止全部中…" : "启动全部中…";
      if (!allRunning && !confirm("将按间隔依次启动全部实例，以降低系统负载。继续？")) return;
      btnLoad(btn, loadingText);
      try {{
        const job = await runAccountBatch(action, accountRows.map((a) => a.id));
        await refreshAccounts({{ silent: true }});
        const failed = (job.results || []).filter((r) => !r.ok).length;
        notify(
          allRunning
            ? (failed ? `停止完成，${{failed}} 个失败` : "已停止全部实例")
            : (failed ? `启动完成，${{failed}} 个失败` : "已启动全部实例"),
          failed ? "warn" : (allRunning ? "warn" : "ok")
        );
      }} catch (e) {{
        notify(e.message || e, "err");
      }} finally {{
        btnReset(btn);
        updateToggleAllButton();
      }}
    }}
    async function restartAllAccounts(btn) {{
      if (!accountRows.length) {{
        notify("当前没有可操作实例", "warn");
        return;
      }}
      if (!confirm("将先停止再按间隔依次重启全部实例（rolling），以降低峰值负载。继续？")) return;
      btnLoad(btn, "重启全部中…");
      try {{
        const job = await runAccountBatch("restart", accountRows.map((a) => a.id));
        await refreshAccounts({{ silent: true }});
        const failed = (job.results || []).filter((r) => !r.ok).length;
        notify(failed ? `重启完成，${{failed}} 个失败` : "已重启全部实例", failed ? "warn" : "ok");
      }} catch (e) {{
        notify(e.message || e, "err");
      }} finally {{
        btnReset(btn);
        updateToggleAllButton();
      }}
    }}
    async function deleteAccount(id, btn) {{
      if (!confirm("确定删除 " + id + " ?")) return;
      btnLoad(btn, "删除中…");
      try {{
        await api(`/api/accounts/${{id}}`, {{ method: "DELETE" }});
        await refreshAccounts({{ silent: true }});
        notify(`已删除 ${{id}}`, "warn");
      }} catch (e) {{
        notify(e.message || e, "err");
      }} finally {{
        btnReset(btn);
      }}
    }}
    refreshAccounts({{ silent: true }}).catch((e) => notify(e.message || e, "err"));
    nbWireRunlogUi();
    setTimeout(() => {{
      nbLoadInitial().then(() => nbStartSse()).catch((e) => notify(e.message || e, "err"));
    }}, 350);
    setInterval(() => {{
      if (!document.getElementById("autoRefresh").checked) return;
      if (document.hidden || isProtoMainInnerScrolling()) return;
      nbLoadInitial().catch(() => {{}});
    }}, 8000);
    (function() {{
      const poll = parseInt(localStorage.getItem("pallas-dashboard-poll-ms") || "10000", 10);
      const ms = Number.isFinite(poll) ? Math.max(poll, 5000) : 10000;
      setInterval(() => {{
        if (document.hidden || isProtoMainInnerScrolling()) return;
        refreshAccounts({{ silent: true }}).catch(() => {{}});
      }}, ms);
    }})();
    (function() {{
      const key = "proto_webui_banner_dismissed_v1";
      const banner = document.getElementById("protoWebuiBanner");
      if (!banner) return;
      if (localStorage.getItem(key) === "1") {{
        banner.hidden = true;
        return;
      }}
      const btn = document.getElementById("protoWebuiBannerDismiss");
      if (btn) btn.addEventListener("click", () => {{
        localStorage.setItem(key, "1");
        banner.hidden = true;
      }});
    }})();
  </script>
  <div id="statusbar" class="statusbar"></div>
</body>
</html>
"""

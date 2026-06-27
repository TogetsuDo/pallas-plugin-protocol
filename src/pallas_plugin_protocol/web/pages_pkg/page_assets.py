# ruff: noqa: E501
"""协议资产页。"""

from __future__ import annotations

import json

from ..contract import resolve_public_mount_path

from .shell_layout import (
    render_protocol_shell_close,
    render_protocol_shell_open,
    shell_head_assets,
)
from .shell_js import _render_common_api_js, _render_hidden_token_sync_js


def render_protocol_assets_page(
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
        active="assets",
        page_title="协议资产",
        page_desc="运行时下载与 Docker",
    )
    shell_close = render_protocol_shell_close(
        path, active="assets", pallas_console_http_base=pallas_console_http_base
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
{shell_head_assets(path)}  <title>协议资产 · 协议端</title>
</head>
<body>
  <input type="hidden" id="token" value="" autocomplete="off" />
  {shell_open}
    <div class="card">
      <p class="muted" style="margin:0 0 14px">
        在此管理 NapCat / SnowLuma 发行包与全局运行方式；改完后点上方「保存设置」。
      </p>
      <div class="row" style="gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:14px">
        <button class="btn secondary" type="button" id="btnCleanupDist" onclick="cleanupRuntimeDistCaches()">清理下载缓存</button>
        <span style="flex:1"></span>
        <span id="saveProfileDirtyHint" class="muted" style="display:none;color:#b91c1c;font-weight:600">有未保存修改</span>
        <button class="btn" id="btnSaveProfile" type="button" onclick="saveUnifiedRuntimeProfile()" style="font-size:0.92rem;padding:10px 18px;font-weight:700">保存设置</button>
      </div>
      <div style="margin:4px 0 14px;padding:14px 16px;border:1px solid var(--bd);border-radius:var(--radius-lg);background:var(--bg1)">
        <div class="row" style="align-items:center;gap:10px;flex-wrap:wrap">
          <input id="followBotLifecycle" type="checkbox" style="width:auto;height:auto;accent-color:var(--accent)" />
          <label for="followBotLifecycle" class="muted" style="margin:0;font-size:0.9rem;line-height:1.45">
            实例随 Bot 启停（全局）
          </label>
        </div>
      </div>
      <div class="assets-napcat-global-card" style="margin:0 0 16px;border:1px solid var(--bd);border-radius:var(--radius);padding:16px 18px;background:var(--bg1)">
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:12px">
          <span style="font-size:0.95rem;font-weight:700;color:var(--txt)">全局运行模式</span>
        </div>
        <div class="row" style="gap:12px;align-items:flex-end;flex-wrap:wrap">
          <div class="field" style="margin:0;min-width:170px;flex:1">
            <label>NapCat 运行模式</label>
            <select id="runtimeModeNapcat" class="shell-pretty-select" onchange="onRuntimeModeChanged()">
              <option value="docker">Docker</option>
              <option value="appimage">AppImage</option>
              <option value="shell">Shell</option>
            </select>
          </div>
          <div class="field" style="margin:0;min-width:170px;flex:1">
            <label>SnowLuma 运行模式</label>
            <select id="runtimeModeSnowluma" class="shell-pretty-select" onchange="onRuntimeModeChanged()">
              <option value="docker">Docker</option>
              <option value="appimage">AppImage</option>
              <option value="shell">Shell</option>
            </select>
          </div>
          <div class="field" style="margin:0;min-width:190px;flex:1">
            <label>下载目标平台（NapCat）</label>
            <select id="targetPlatform" class="shell-pretty-select">
              <option value="auto">auto（跟随当前平台）</option>
              <option value="linux-amd64">linux-amd64</option>
              <option value="linux-arm64">linux-arm64</option>
              <option value="windows-amd64">windows-amd64</option>
            </select>
          </div>
        </div>
        <div class="row" style="gap:12px;align-items:flex-end;margin-top:10px">
          <div class="field" style="margin:0;min-width:260px;flex:1;max-width:520px">
            <label>保存全局运行配置时：对协议 Docker 容器的处理</label>
            <select id="runtimeProfilePruneContainers" class="shell-pretty-select">
              <option value="all">NapCat 与 SnowLuma 全部</option>
              <option value="napcat">仅 NapCat</option>
              <option value="snowluma">仅 SnowLuma</option>
            </select>
          </div>
        </div>
        <p class="muted" style="margin:8px 0 0;font-size:0.82rem;line-height:1.45">
          点击本页「保存设置」并写入全局运行模式或镜像后，会按此处范围<strong>先停止</strong>对应协议账号进程，再<strong>删除已有 Docker 容器</strong>，避免旧容器继续占用旧镜像或端口。
          只更新一侧镜像时可点「仅 NapCat / 仅 SnowLuma」；<strong>同一端</strong>在 Docker 与 AppImage/Shell 之间切换时须选对应该端的清理范围（或「全部」），否则无法一步清掉该端旧容器。
        </p>
        <div id="dockerProfileArea" style="margin-top:10px;display:none">
          <div class="row" style="gap:8px;align-items:flex-end">
            <div class="field" style="margin:0;min-width:260px;flex:1">
              <label>NapCat Docker 镜像</label>
              <input id="dockerImage" placeholder="mlikiowa/napcat-docker:latest" autocomplete="off" />
            </div>
            <button class="btn secondary" id="btnPullImage" type="button" onclick="pullDockerImage()">拉取镜像</button>
            <button class="btn secondary" id="btnListImage" type="button" onclick="listDockerImages('napcat')">查看本地镜像</button>
          </div>
          <div class="row" style="gap:8px;align-items:flex-end;margin-top:8px">
            <div class="field" style="margin:0;min-width:260px;flex:1">
              <label>SnowLuma Docker 镜像</label>
              <input id="snowlumaDockerImage" placeholder="motricseven7/snowluma:latest" autocomplete="off" />
            </div>
            <button class="btn secondary" id="btnPullSnowlumaImage" type="button" onclick="pullSnowlumaDockerImage()">拉取镜像</button>
            <button class="btn secondary" id="btnListSnowlumaImage" type="button" onclick="listDockerImages('snowluma')">查看本地镜像</button>
          </div>
          <div class="row" style="gap:8px;align-items:flex-end;margin-top:8px;flex-wrap:wrap">
            <div class="field" style="margin:0;min-width:220px;flex:1">
              <label>NapCat 本地镜像</label>
              <select id="dockerImageSelect" class="shell-pretty-select">
                <option value="">（先点 NapCat「查看本地镜像」，仅当前配置的仓库）</option>
              </select>
            </div>
            <button class="btn secondary" id="btnUseSelectedImage" type="button" onclick="applySelectedDockerImage()">填入 NapCat 镜像框</button>
            <div class="field" style="margin:0;min-width:220px;flex:1">
              <label>SnowLuma 本地镜像</label>
              <select id="snowlumaDockerImageSelect" class="shell-pretty-select">
                <option value="">（先点 SnowLuma「查看本地镜像」，仅当前配置的仓库）</option>
              </select>
            </div>
            <button class="btn secondary" id="btnUseSelectedSnowlumaImage" type="button" onclick="applySelectedSnowlumaDockerImage()">填入 SnowLuma 镜像框</button>
          </div>
          <div class="row" style="gap:8px;align-items:flex-end;margin-top:8px;flex-wrap:wrap">
            <button class="btn secondary" id="btnStopAllDocker" type="button" onclick="stopAllDockerContainers()">停止全部协议容器</button>
            <button class="btn secondary" id="btnPruneStoppedDocker" type="button" onclick="pruneStoppedDockerContainers()">清理已停止协议容器</button>
          </div>
          <p class="muted" style="margin:8px 0 0;font-size:0.82rem">Docker 模式需本机已安装 Docker；镜像名见上。</p>
          <details style="margin-top:10px">
            <summary class="muted" style="cursor:pointer">查看 Docker pull 日志</summary>
            <pre class="mono" id="dockerPullLogs" style="max-height:min(42vh,360px);overflow:auto;margin-top:8px;font-size:12px;background:#0f1624;color:#dbe7ff;padding:10px;border-radius:10px;border:1px solid var(--bd)">尚未执行拉取。</pre>
          </details>
        </div>
      </div>
      <div class="proto-switch-toolbar">
        <div class="row" style="gap:10px;align-items:flex-end;flex-wrap:wrap">
          <div class="field" style="margin:0;min-width:200px">
            <label for="assetsProtoSelect">发行包</label>
            <select id="assetsProtoSelect" class="shell-pretty-select" aria-label="协议发行包类型">
              <option value="napcat">NapCat</option>
              <option value="snowluma">SnowLuma</option>
            </select>
          </div>
        </div>
      </div>
      <div id="assetsPaneUnified">
      <h2 id="assetsProtoHeading" class="section-title" style="margin:16px 0 8px;font-size:1.05rem;font-weight:700">发行包</h2>
      <p id="assetsProtoHint" class="muted" style="margin:0 0 10px;font-size:0.86rem">在 NapCat 与 SnowLuma 间切换；全局运行模式与 Docker 镜像见上方。</p>
      <div id="rowAssetsSlTargetPlatform" class="field" style="margin-bottom:12px;display:none">
        <label>下载目标平台（SnowLuma）</label>
        <select id="slTargetPlatform" class="shell-pretty-select">
          <option value="auto">自动（按本机系统）</option>
          <option value="windows-amd64">windows-amd64</option>
          <option value="linux-amd64">linux-amd64</option>
          <option value="linux-arm64">linux-arm64</option>
        </select>
      </div>
      <div class="kpi-grid">
        <div class="kpi"><div class="k">任务状态</div><div class="v" id="rtStatus">-</div></div>
        <div class="kpi"><div class="k">当前阶段</div><div class="v" id="rtStage">-</div></div>
        <div class="kpi"><div class="k">目标 / 版本</div><div class="v" id="rtAsset" title="">-</div></div>
        <div class="kpi"><div class="k">最后刷新</div><div class="v" id="rtTime">-</div></div>
      </div>
      <div class="card" style="margin:10px 0 0;box-shadow:none">
        <div class="field" style="margin-bottom:10px">
          <label>状态消息</label>
          <div class="mono" id="rtMessage">-</div>
        </div>
        <div class="field" style="margin-bottom:10px">
          <label>下载来源</label>
          <div class="mono" id="rtSource">-</div>
        </div>
        <div class="field" style="margin-bottom:0">
          <label id="lblRtProgramDir">运行目录</label>
          <div class="mono" id="rtProgramDir">-</div>
        </div>
      </div>
      <div class="row" style="margin-top:12px;flex-wrap:wrap;gap:8px">
        <button class="btn" id="btnAssetDownload" type="button" onclick="assetDownloadRuntime()">立即更新</button>
        <button class="btn secondary" id="btnRescan" type="button" onclick="rescanRuntime()">刷新检测</button>
        <button class="btn secondary" id="btnAssetRefresh" type="button" onclick="assetRefreshOverview()">刷新状态</button>
      </div>
      <div style="margin-top:18px;border:1px solid var(--bd);border-radius:var(--radius);padding:16px 18px;background:var(--bg1)">
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:12px">
          <span style="font-size:0.95rem;font-weight:700;color:var(--txt)">选择版本</span>
          <button class="btn secondary" id="btnLoadReleases" type="button" onclick="loadAssetReleases()" style="font-size:0.82rem;padding:7px 14px">加载版本列表</button>
        </div>
        <div id="releasesArea" style="display:none">
          <div class="row" style="gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:8px">
            <select id="releaseSelect" class="shell-pretty-select" style="flex:1;min-width:200px;height:40px"></select>
            <button class="btn secondary" id="btnDownloadTag" type="button" onclick="assetActivateSelectedTag()">选择此版本</button>
          </div>
          <div id="releaseDetail" class="muted" style="font-size:0.78rem;min-height:1.4em"></div>
        </div>
        <p id="releasesPlaceholder" class="muted" style="margin:0;font-size:0.82rem">先点「加载版本列表」。</p>
      </div>
      <div style="margin-top:18px;border:1px solid var(--bd);border-radius:var(--radius);padding:16px 18px;background:var(--bg1)">
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:10px">
          <span style="font-size:0.95rem;font-weight:700;color:var(--txt)">本机解压目录（切换托管版本）</span>
          <button class="btn secondary" type="button" id="btnAssetInvRefresh" onclick="loadAssetLocalInventory()">刷新列表</button>
        </div>
        <p class="muted" style="margin:0 0 10px;font-size:0.82rem">按 Release 标签分子目录；切换后使用对应托管的账号需重启协议进程。</p>
        <p id="assetDistFilesHint" class="muted" style="font-size:0.78rem;margin:0 0 8px"></p>
        <div id="assetLocalInvPlaceholder" class="muted" style="font-size:0.82rem">点击「刷新列表」加载。</div>
        <div id="assetLocalInvTable" style="display:none;margin-top:8px;overflow:auto;border:1px solid var(--bd);border-radius:var(--radius-sm);max-height:min(36vh,320px)">
          <table class="acc-table" style="width:100%;border-collapse:collapse;font-size:0.84rem">
            <thead><tr>
              <th style="text-align:left;padding:8px">版本（目录）</th>
              <th style="text-align:left;padding:8px">修改时间</th>
              <th style="text-align:left;padding:8px">托管</th>
              <th style="text-align:right;padding:8px">操作</th>
            </tr></thead>
            <tbody id="assetLocalInvBody"></tbody>
          </table>
        </div>
      </div>
      <details style="margin-top:14px">
        <summary id="assetsRuntimeJsonSummary" class="muted" style="cursor:pointer">状态 JSON</summary>
        <pre class="mono muted" id="runtimeStatus" tabindex="0" title="框选复制；聚焦时暂停自动刷新" style="max-height:min(70vh,720px);overflow:auto;margin-top:8px;font-size:12px"></pre>
      </details>
      </div>
    </div>
{shell_close}
  <script>
    const basePath = {p};
{common_api_js}
    initPallasShellThemeFromStorage();
    let runtimeRefreshing = false;
    let runtimeProfileSnapshot = null;
    let runtimeProfileWatchBound = false;
    let pendingTag = null;
    let pendingSnowlumaTag = null;
    let _assetReleaseList = [];
    function assetsProtoIsSl() {{
      const s = document.getElementById("assetsProtoSelect");
      return !!(s && String(s.value || "").toLowerCase() === "snowluma");
    }}
    async function assetRefreshOverview(opts = {{}}) {{
      if (assetsProtoIsSl()) return await refreshSnowlumaOverview(opts);
      return await refreshRuntime(opts);
    }}
    function assetDownloadRuntime() {{
      void (assetsProtoIsSl() ? downloadSnowlumaRuntime() : downloadRuntime());
    }}
    function anyRuntimeDocker() {{
      const a = String(document.getElementById("runtimeModeNapcat")?.value || "");
      const b = String(document.getElementById("runtimeModeSnowluma")?.value || "");
      return a === "docker" || b === "docker";
    }}
    function syncAssetDownloadButtonText() {{
      const isDocker = anyRuntimeDocker();
      const dlBtn = document.getElementById("btnAssetDownload");
      if (!dlBtn) return;
      if (assetsProtoIsSl()) {{
        dlBtn.textContent = "下载 / 更新";
      }} else {{
        dlBtn.textContent = isDocker ? "Docker 模式无需下载" : "立即更新";
      }}
    }}
    function syncSelectVersionButtonState() {{
      const dlTagBtn = document.getElementById("btnDownloadTag");
      if (!dlTagBtn) return;
      const napDocker = String(document.getElementById("runtimeModeNapcat")?.value || "") === "docker";
      const slDocker = String(document.getElementById("runtimeModeSnowluma")?.value || "") === "docker";
      const sl = assetsProtoIsSl();
      const disable = sl ? slDocker : napDocker;
      dlTagBtn.disabled = disable;
      dlTagBtn.title = disable
        ? (sl ? "SnowLuma 为 Docker 模式时无需选择本地发行包版本。" : "NapCat 为 Docker 模式时无需选择本地发行包版本。")
        : "";
    }}
    function setAssetsProtocolPane(which, pushUrl) {{
      const sel = document.getElementById("assetsProtoSelect");
      const v = (String(which || "napcat").toLowerCase() === "snowluma") ? "snowluma" : "napcat";
      if (sel) sel.value = v;
      const slRow = document.getElementById("rowAssetsSlTargetPlatform");
      if (slRow) slRow.style.display = v === "snowluma" ? "block" : "none";
      const rs = document.getElementById("btnRescan");
      if (rs) rs.style.display = v === "snowluma" ? "none" : "";
      const h = document.getElementById("assetsProtoHeading");
      if (h) h.textContent = v === "snowluma" ? "SnowLuma 发行包" : "NapCat 发行包";
      const hi = document.getElementById("assetsProtoHint");
      if (hi) {{
        hi.textContent = v === "snowluma"
          ? "从 GitHub Release 下载；Docker 见上方「SnowLuma Docker 镜像」与「拉取镜像」。"
          : "从官方渠道下载；Docker 见上方「NapCat Docker 镜像」与「拉取镜像」。";
      }}
      const lb = document.getElementById("lblRtProgramDir");
      if (lb) lb.textContent = v === "snowluma" ? "程序根目录（index.mjs）" : "运行目录";
      const rf = document.getElementById("btnAssetRefresh");
      if (rf) rf.textContent = "刷新状态";
      const sm = document.getElementById("assetsRuntimeJsonSummary");
      if (sm) sm.textContent = v === "snowluma" ? "SnowLuma 状态 JSON" : "NapCat 状态 JSON";
      try {{
        localStorage.setItem("pallas_protocol_assets_pane", v);
      }} catch (e) {{}}
      if (pushUrl !== false) {{
        const u = new URL(location.href);
        u.searchParams.set("protocol", v);
        history.replaceState(null, "", u.pathname + u.search);
      }}
      syncAssetsSaveButton();
      syncAssetDownloadButtonText();
      syncSelectVersionButtonState();
      const ra = document.getElementById("releasesArea");
      const rp = document.getElementById("releasesPlaceholder");
      const rsel = document.getElementById("releaseSelect");
      if (ra) ra.style.display = "none";
      if (rp) rp.style.display = "block";
      if (rsel) rsel.innerHTML = "";
      _assetReleaseList = [];
      if (v === "snowluma") {{
        const slTpEl = document.getElementById("slTargetPlatform");
        if (slTpEl) {{
          const sv = localStorage.getItem("pallas_protocol_sl_target_platform") || "";
          if (["auto", "windows-amd64", "linux-amd64", "linux-arm64"].includes(sv)) slTpEl.value = sv;
          if (typeof shellPrettySyncSelect === "function") shellPrettySyncSelect(slTpEl);
        }}
      }}
      if (typeof shellPrettySyncSelect === "function" && sel) shellPrettySyncSelect(sel);
      void loadAssetLocalInventory();
    }}
    function initAssetsProtocolPane() {{
      const u = new URL(location.href);
      let p = (u.searchParams.get("protocol") || localStorage.getItem("pallas_protocol_assets_pane") || "napcat").toLowerCase();
      if (p !== "snowluma") p = "napcat";
      setAssetsProtocolPane(p, false);
      const slTp = document.getElementById("slTargetPlatform");
      if (slTp) {{
        const sv = localStorage.getItem("pallas_protocol_sl_target_platform") || "";
        if (["auto", "windows-amd64", "linux-amd64", "linux-arm64"].includes(sv)) slTp.value = sv;
      }}
    }}
    const _assetsProtoSel = document.getElementById("assetsProtoSelect");
    if (_assetsProtoSel) {{
      _assetsProtoSel.addEventListener("change", () => setAssetsProtocolPane(_assetsProtoSel.value));
    }}
    initAssetsProtocolPane();
    const _slTpCh = document.getElementById("slTargetPlatform");
    if (_slTpCh) {{
      _slTpCh.addEventListener("change", () => {{
        try {{ localStorage.setItem("pallas_protocol_sl_target_platform", _slTpCh.value || "auto"); }} catch (e) {{}}
      }});
    }}
    function setBtnBusy(el, busy, idleText, busyText) {{
      if (!el) return;
      el.disabled = !!busy;
      el.textContent = busy ? busyText : idleText;
      el.classList.toggle("busy", !!busy);
    }}
    async function cleanupRuntimeDistCaches() {{
      if (!confirm("删除已下载的安装包（runtime_dist），不删解压目录与 manifest。确定？")) return;
      const btn = document.getElementById("btnCleanupDist");
      setBtnBusy(btn, true, "清理下载缓存", "清理中...");
      try {{
        const r = await api("/api/runtime/cleanup-dist", {{ method: "POST" }});
        const nc = r.napcat_files_removed ?? 0;
        const sl = r.snowluma_files_removed ?? 0;
        alert("已清理：NapCat " + nc + " 个文件，SnowLuma " + sl + " 个文件。");
      }} catch (e) {{
        alert(e.message || e);
      }} finally {{
        setBtnBusy(btn, false, "清理下载缓存", "清理中...");
      }}
      void loadAssetLocalInventory();
    }}
    function invEsc(t) {{
      return String(t ?? "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
    }}
    async function loadAssetLocalInventory() {{
      const ph = document.getElementById("assetLocalInvPlaceholder");
      const tb = document.getElementById("assetLocalInvTable");
      const body = document.getElementById("assetLocalInvBody");
      const distEl = document.getElementById("assetDistFilesHint");
      if (!ph || !tb || !body) return;
      ph.style.display = "block";
      ph.textContent = "加载中…";
      const sl = assetsProtoIsSl();
      const ep = sl ? "/api/snowluma/runtime/local-inventory" : "/api/runtime/local-inventory";
      try {{
        const data = await api(ep);
        const dirs = Array.isArray(data.extract_dirs) ? data.extract_dirs : [];
        const files = Array.isArray(data.dist_files) ? data.dist_files : [];
        if (distEl) {{
          distEl.textContent = files.length
            ? ("runtime_dist 中现有文件（" + files.length + "）：" + files.map((f) => f.name).join(" · "))
            : "runtime_dist 目录暂无文件。";
        }}
        if (!dirs.length) {{
          ph.textContent = "暂无解压子目录（成功安装至少一次后会出现对应 Release 标签目录）。";
          tb.style.display = "none";
          body.innerHTML = "";
          return;
        }}
        ph.style.display = "none";
        tb.style.display = "block";
        body.innerHTML = dirs.map((d) => {{
          const active = !!d.is_active;
          const mt = d.mtime_iso ? new Date(d.mtime_iso).toLocaleString("zh-CN") : "-";
          const btn = active
            ? '<span class="muted">当前托管</span>'
            : (sl
              ? ("<button type=\\"button\\" class=\\"btn secondary\\" onclick='activateSnowlumaExtract(" + JSON.stringify(d.name) + ")'>托管使用此目录</button>")
              : ("<button type=\\"button\\" class=\\"btn secondary\\" onclick='activateNapcatExtract(" + JSON.stringify(d.name) + ")'>托管使用此目录</button>"));
          return "<tr><td style=\\"padding:8px;font-family:var(--font-mono,monospace);font-size:0.8rem\\">" + invEsc(d.name) + "</td>"
            + "<td style=\\"padding:8px\\">" + invEsc(mt) + "</td>"
            + "<td style=\\"padding:8px\\">" + (active ? "当前" : "—") + "</td>"
            + "<td style=\\"padding:8px;text-align:right\\">" + btn + "</td></tr>";
        }}).join("");
      }} catch (e) {{
        ph.textContent = "加载失败：" + (e.message || e);
        tb.style.display = "none";
      }}
    }}
    async function activateNapcatExtract(folderName) {{
      if (!folderName) return;
      if (!confirm("将当前托管的 NapCat 切换到解压版本：\\n" + folderName + "\\n（不重新下载）")) return;
      try {{
        await api("/api/runtime/activate-tag", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ tag: folderName }}),
        }});
        await refreshRuntime({{ silent: true }});
        await loadAssetLocalInventory();
        alert("已切换托管目录。使用此托管的账号请重启协议端进程后生效。");
      }} catch (e) {{
        alert(e.message || e);
      }}
    }}
    async function activateSnowlumaExtract(folderName) {{
      if (!folderName) return;
      if (!confirm("将当前托管的 SnowLuma 切换到解压版本：\\n" + folderName + "\\n（不重新下载）")) return;
      try {{
        await api("/api/snowluma/runtime/activate-tag", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ tag: folderName }}),
        }});
        const slo = await api("/api/snowluma/runtime/overview");
        fillRuntimeOverviewFromPayload(slo);
        await loadAssetLocalInventory();
        alert("已切换托管目录。使用此托管的账号请重启协议端进程后生效。");
      }} catch (e) {{
        alert(e.message || e);
      }}
    }}
    function statusText(s) {{
      if (!s) return "未知";
      const map = {{
        idle: "空闲",
        downloading: "下载中",
        extracting: "处理中",
        installing: "安装中",
        done: "完成",
        error: "失败",
      }};
      return map[s] || s;
    }}
    function stageText(msg) {{
      const m = String(msg || "");
      if (!m) return "-";
      if (m.includes("下载")) return "下载";
      if (m.includes("解压") || m.includes("安装")) return "安装/解包";
      if (m.includes("检测")) return "检测";
      if (m.includes("完成")) return "完成";
      if (m.includes("失败") || m.includes("错误")) return "失败";
      return "处理中";
    }}
    function setText(id, value) {{
      const el = document.getElementById(id);
      if (!el) return;
      const v = String(value || "-");
      el.textContent = v;
      el.title = v;
    }}
    function appendDockerPullLog(line) {{
      const el = document.getElementById("dockerPullLogs");
      if (!el) return;
      const now = new Date().toLocaleTimeString();
      const text = `[${{now}}] ${{String(line || "")}}`;
      if (!el.textContent || el.textContent === "尚未执行拉取。") {{
        el.textContent = text;
      }} else {{
        el.textContent += "\\n" + text;
      }}
      el.scrollTop = el.scrollHeight;
    }}
    function normalizeRuntimeProfile(p) {{
      const leg = ["docker", "appimage", "shell"].includes(String(p.runtime_mode || "")) ? String(p.runtime_mode) : "shell";
      const nap = ["docker", "appimage", "shell"].includes(String(p.napcat_runtime_mode || ""))
        ? String(p.napcat_runtime_mode)
        : leg;
      const snow = ["docker", "appimage", "shell"].includes(String(p.snowluma_runtime_mode || ""))
        ? String(p.snowluma_runtime_mode)
        : leg;
      const platform = ["auto", "linux-amd64", "linux-arm64", "windows-amd64"].includes(String(p.target_platform || ""))
        ? String(p.target_platform)
        : "auto";
      const pr = String(p.prune_containers || "all").toLowerCase();
      const pruneOk = pr === "napcat" || pr === "snowluma" ? pr : "all";
      return {{
        runtime_mode: nap,
        napcat_runtime_mode: nap,
        snowluma_runtime_mode: snow,
        target_platform: platform,
        docker_image: String(p.docker_image || "").trim(),
        snowluma_docker_image: String(p.snowluma_docker_image || "").trim(),
        follow_bot_lifecycle: !!p.follow_bot_lifecycle,
        prune_containers: pruneOk,
      }};
    }}
    function currentRuntimeProfileForm() {{
      return normalizeRuntimeProfile({{
        napcat_runtime_mode: document.getElementById("runtimeModeNapcat")?.value || "shell",
        snowluma_runtime_mode: document.getElementById("runtimeModeSnowluma")?.value || "shell",
        target_platform: document.getElementById("targetPlatform")?.value || "auto",
        docker_image: document.getElementById("dockerImage")?.value || "",
        snowluma_docker_image: document.getElementById("snowlumaDockerImage")?.value || "",
        follow_bot_lifecycle: !!document.getElementById("followBotLifecycle")?.checked,
        prune_containers: (document.getElementById("runtimeProfilePruneContainers")?.value || "all"),
      }});
    }}
    function updateSaveProfileDirtyState() {{
      const hint = document.getElementById("saveProfileDirtyHint");
      if (!hint || !runtimeProfileSnapshot) return;
      const dirty = JSON.stringify(currentRuntimeProfileForm()) !== JSON.stringify(runtimeProfileSnapshot);
      hint.style.display = dirty ? "inline" : "none";
    }}
    function syncAssetsSaveButton() {{
      const btn = document.getElementById("btnSaveProfile");
      if (btn) {{
        btn.disabled = false;
        btn.title = "";
      }}
      const hint = document.getElementById("saveProfileDirtyHint");
      if (hint) {{
        updateSaveProfileDirtyState();
      }}
    }}
    function bindRuntimeProfileWatchers() {{
      if (runtimeProfileWatchBound) return;
      runtimeProfileWatchBound = true;
      ["runtimeModeNapcat", "runtimeModeSnowluma", "targetPlatform", "dockerImage", "snowlumaDockerImage", "followBotLifecycle", "runtimeProfilePruneContainers"].forEach((id) => {{
        const el = document.getElementById(id);
        if (!el) return;
        el.addEventListener("change", updateSaveProfileDirtyState);
        el.addEventListener("input", updateSaveProfileDirtyState);
      }});
    }}
    function onRuntimeModeChanged() {{
      const isDocker = anyRuntimeDocker();
      const napDocker = String(document.getElementById("runtimeModeNapcat")?.value || "") === "docker";
      const dockerArea = document.getElementById("dockerProfileArea");
      if (dockerArea) dockerArea.style.display = isDocker ? "block" : "none";
      const target = document.getElementById("targetPlatform");
      if (target) target.disabled = napDocker;
      syncSelectVersionButtonState();
      syncAssetDownloadButtonText();
      if (typeof shellPrettySyncSelect === "function") {{
        const r1 = document.getElementById("runtimeModeNapcat");
        const r2 = document.getElementById("runtimeModeSnowluma");
        const tp = document.getElementById("targetPlatform");
        if (r1) shellPrettySyncSelect(r1);
        if (r2) shellPrettySyncSelect(r2);
        if (tp) shellPrettySyncSelect(tp);
      }}
    }}
    async function loadRuntimeProfile() {{
      const data = await api("/api/runtime/profile");
      const p = data.profile || {{}};
      const leg = ["docker", "appimage", "shell"].includes(String(p.runtime_mode || "")) ? p.runtime_mode : "shell";
      const nap = ["docker", "appimage", "shell"].includes(String(p.napcat_runtime_mode || ""))
        ? p.napcat_runtime_mode
        : leg;
      const snow = ["docker", "appimage", "shell"].includes(String(p.snowluma_runtime_mode || ""))
        ? p.snowluma_runtime_mode
        : leg;
      const platform = ["auto", "linux-amd64", "linux-arm64", "windows-amd64"].includes(String(p.target_platform || ""))
        ? p.target_platform
        : "auto";
      document.getElementById("runtimeModeNapcat").value = nap;
      document.getElementById("runtimeModeSnowluma").value = snow;
      document.getElementById("targetPlatform").value = platform;
      document.getElementById("dockerImage").value = String(p.docker_image || "");
      const sld = document.getElementById("snowlumaDockerImage");
      if (sld) sld.value = String(p.snowluma_docker_image || "");
      document.getElementById("followBotLifecycle").checked = !!p.follow_bot_lifecycle;
      const pc = document.getElementById("runtimeProfilePruneContainers");
      if (pc) pc.value = "all";
      runtimeProfileSnapshot = normalizeRuntimeProfile({{ ...p, prune_containers: "all" }});
      bindRuntimeProfileWatchers();
      updateSaveProfileDirtyState();
      onRuntimeModeChanged();
      if (typeof shellPrettySyncSelect === "function") {{
        ["runtimeModeNapcat", "runtimeModeSnowluma", "targetPlatform", "dockerImageSelect", "snowlumaDockerImageSelect", "runtimeProfilePruneContainers", "assetsProtoSelect"].forEach((id) => {{
          const el = document.getElementById(id);
          if (el) shellPrettySyncSelect(el);
        }});
      }}
    }}
    async function saveUnifiedRuntimeProfile() {{
      await saveRuntimeProfile();
    }}
    async function saveRuntimeProfile() {{
      const btn = document.getElementById("btnSaveProfile");
      setBtnBusy(btn, true, "保存设置", "保存中...");
      try {{
        const body = {{
          napcat_runtime_mode: document.getElementById("runtimeModeNapcat").value,
          snowluma_runtime_mode: document.getElementById("runtimeModeSnowluma").value,
          target_platform: document.getElementById("targetPlatform").value,
          docker_image: document.getElementById("dockerImage").value.trim(),
          snowluma_docker_image: (document.getElementById("snowlumaDockerImage")?.value || "").trim(),
          follow_bot_lifecycle: !!document.getElementById("followBotLifecycle").checked,
          prune_containers: (document.getElementById("runtimeProfilePruneContainers")?.value || "all"),
        }};
        await api("/api/runtime/profile", {{
          method: "PUT",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify(body),
        }});
        runtimeProfileSnapshot = normalizeRuntimeProfile(body);
        updateSaveProfileDirtyState();
        await assetRefreshOverview({{ silent: true }});
      }} catch (e) {{
        alert(e.message || e);
      }} finally {{
        setBtnBusy(btn, false, "保存设置", "保存中...");
      }}
    }}
    async function pullSnowlumaDockerImage() {{
      const btn = document.getElementById("btnPullSnowlumaImage");
      setBtnBusy(btn, true, "拉取镜像", "拉取中...");
      try {{
        const image = (document.getElementById("snowlumaDockerImage")?.value || "").trim();
        appendDockerPullLog("开始拉取 SnowLuma 镜像: " + (image || "motricseven7/snowluma:latest"));
        const body = {{ image }};
        const res = await api("/api/runtime/docker/pull", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify(body),
        }});
        const output = String(res.output || "").trim();
        if (output) appendDockerPullLog(output);
        if (!res.ok) {{
          appendDockerPullLog("拉取失败，退出码: " + String(res.code ?? "-"));
          return;
        }}
        appendDockerPullLog("拉取成功: " + String(res.image || ""));
      }} catch (e) {{
        appendDockerPullLog("拉取异常: " + String(e.message || e));
      }} finally {{
        setBtnBusy(btn, false, "拉取镜像", "拉取中...");
      }}
    }}
    async function pullDockerImage() {{
      const btn = document.getElementById("btnPullImage");
      setBtnBusy(btn, true, "拉取镜像", "拉取中...");
      try {{
        const image = document.getElementById("dockerImage").value.trim();
        appendDockerPullLog("开始拉取 NapCat 镜像: " + (image || "mlikiowa/napcat-docker:latest"));
        const body = {{ image }};
        const res = await api("/api/runtime/docker/pull", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify(body),
        }});
        const output = String(res.output || "").trim();
        if (output) appendDockerPullLog(output);
        if (!res.ok) {{
          appendDockerPullLog("拉取失败，退出码: " + String(res.code ?? "-"));
          return;
        }}
        appendDockerPullLog("拉取成功: " + String(res.image || ""));
      }} catch (e) {{
        appendDockerPullLog("拉取异常: " + String(e.message || e));
      }} finally {{
        setBtnBusy(btn, false, "拉取镜像", "拉取中...");
      }}
    }}
    async function listDockerImages(protocol) {{
      const proto = String(protocol || "napcat").toLowerCase();
      const isSl = proto === "snowluma";
      const btn = document.getElementById(isSl ? "btnListSnowlumaImage" : "btnListImage");
      const label = isSl ? "SnowLuma 查看本地镜像" : "NapCat 查看本地镜像";
      setBtnBusy(btn, true, label, "查询中...");
      try {{
        const res = await api("/api/runtime/docker/images?protocol=" + encodeURIComponent(proto));
        if (!res.ok) {{
          appendDockerPullLog("查询失败: " + String(res.detail || res.output || res.code || "未知错误"));
          return;
        }}
        const fr = res.filter_repository ? String(res.filter_repository) : "";
        if (fr) {{
          appendDockerPullLog((isSl ? "SnowLuma" : "NapCat") + " 按当前配置仓库筛选: " + fr);
        }}
        const images = Array.isArray(res.images) ? res.images : [];
        const sel = document.getElementById(isSl ? "snowlumaDockerImageSelect" : "dockerImageSelect");
        const currentImage = String(
          document.getElementById(isSl ? "snowlumaDockerImage" : "dockerImage")?.value || ""
        ).trim();
        if (sel) {{
          const options = [`<option value="">（请选择）</option>`];
          images.forEach((img) => {{
            const name = String(img.name || "").trim();
            if (!name) return;
            const meta = [img.created_since ? String(img.created_since) : "", img.size ? String(img.size) : ""].filter(Boolean).join(" / ");
            const currentMark = name === currentImage ? "（当前）" : "";
            options.push(`<option value="${{name.replace(/"/g, "&quot;")}}">${{name}}${{currentMark ? " " + currentMark : ""}}${{meta ? " · " + meta : ""}}</option>`);
          }});
          sel.innerHTML = options.join("");
          if (currentImage) sel.value = currentImage;
          if (typeof shellPrettySyncSelect === "function") shellPrettySyncSelect(sel);
        }}
        if (!images.length) {{
          appendDockerPullLog("本地暂无匹配镜像（可检查上方输入框中的镜像名是否与已拉取仓库一致）。");
          return;
        }}
        appendDockerPullLog("本地镜像列表（" + String(images.length) + "）:");
        images.slice(0, 80).forEach((img) => {{
          const line = [
            String(img.name || "<none>:<none>"),
            img.id ? `id=${{img.id}}` : "",
            img.created_since ? `created=${{img.created_since}}` : "",
            img.size ? `size=${{img.size}}` : "",
          ].filter(Boolean).join(" | ");
          appendDockerPullLog("  - " + line);
        }});
      }} catch (e) {{
        appendDockerPullLog("查询异常: " + String(e.message || e));
      }} finally {{
        setBtnBusy(btn, false, label, "查询中...");
      }}
    }}
    function applySelectedDockerImage() {{
      const sel = document.getElementById("dockerImageSelect");
      const input = document.getElementById("dockerImage");
      if (!sel || !input) return;
      const v = String(sel.value || "").trim();
      if (!v) {{
        alert("请先从 NapCat 本地镜像下拉框选择一项。");
        return;
      }}
      input.value = v;
      appendDockerPullLog("已填入 NapCat 镜像: " + v + "（记得点「保存设置」生效）");
    }}
    function applySelectedSnowlumaDockerImage() {{
      const sel = document.getElementById("snowlumaDockerImageSelect");
      const input = document.getElementById("snowlumaDockerImage");
      if (!sel || !input) return;
      const v = String(sel.value || "").trim();
      if (!v) {{
        alert("请先从 SnowLuma 本地镜像下拉框选择一项。");
        return;
      }}
      input.value = v;
      appendDockerPullLog("已填入 SnowLuma 镜像: " + v + "（记得点「保存设置」生效）");
    }}
    async function stopAllDockerContainers() {{
      const btn = document.getElementById("btnStopAllDocker");
      setBtnBusy(btn, true, "停止全部协议容器", "处理中...");
      try {{
        const res = await api("/api/runtime/docker/stop-all", {{ method: "POST" }});
        if (!res.ok) {{
          appendDockerPullLog("批量停止失败: " + String(res.detail || res.output || res.code || "未知错误"));
          return;
        }}
        appendDockerPullLog("已停止协议容器数量: " + String(res.stopped || 0));
        if (res.output) appendDockerPullLog(String(res.output));
      }} catch (e) {{
        appendDockerPullLog("批量停止异常: " + String(e.message || e));
      }} finally {{
        setBtnBusy(btn, false, "停止全部协议容器", "处理中...");
      }}
    }}
    async function pruneStoppedDockerContainers() {{
      const btn = document.getElementById("btnPruneStoppedDocker");
      setBtnBusy(btn, true, "清理已停止协议容器", "处理中...");
      try {{
        const res = await api("/api/runtime/docker/prune-stopped", {{ method: "POST" }});
        if (!res.ok) {{
          appendDockerPullLog("清理失败: " + String(res.detail || res.output || res.code || "未知错误"));
          return;
        }}
        appendDockerPullLog("已清理停止容器数量: " + String(res.removed || 0));
        if (res.output) appendDockerPullLog(String(res.output));
      }} catch (e) {{
        appendDockerPullLog("清理异常: " + String(e.message || e));
      }} finally {{
        setBtnBusy(btn, false, "清理已停止协议容器", "处理中...");
      }}
    }}
    async function refreshRuntime(opts = {{}}) {{
      const silent = !!opts.silent;
      if (runtimeRefreshing) return;
      runtimeRefreshing = true;
      if (!silent) {{
        setBtnBusy(document.getElementById("btnAssetRefresh"), true, "刷新状态", "刷新中...");
      }}
      try {{
        const data = await api("/api/runtime");
        {{
          const rs = document.getElementById("runtimeStatus");
          if (rs && !shouldPauseLiveLogDomWrite(rs)) rs.textContent = JSON.stringify(data, null, 2);
        }}
        const job = data.job || {{}};
        const d = data.download || {{}};
        const manifest = data.manifest || {{}};
        setText("rtStatus", statusText(job.status));
        setText("rtStage", stageText(job.message));
        const tag = pendingTag || job.tag || manifest.release_tag || d.tag || "";
        const assetEl = document.getElementById("rtAsset");
        if (assetEl) {{ assetEl.title = d.asset || manifest.asset_name || ""; }}
        setText("rtAsset", tag || d.asset || manifest.asset_name || "-");
        setText("rtMessage", job.message || "-");
        setText("rtSource", manifest.source_url || `${{d.repo || "-"}} @ ${{tag || "latest"}}`);
        setText("rtProgramDir", data.effective_program_dir || manifest.program_dir || "-");
        setText("rtTime", new Date().toLocaleTimeString());
      }} catch (e) {{
        {{
          const rs = document.getElementById("runtimeStatus");
          if (rs && !shouldPauseLiveLogDomWrite(rs)) rs.textContent = String(e.message || e);
        }}
        setText("rtStatus", "失败");
        setText("rtStage", "错误");
        setText("rtMessage", String(e.message || e));
        setText("rtTime", new Date().toLocaleTimeString());
      }} finally {{
        if (!silent) {{
          setBtnBusy(document.getElementById("btnAssetRefresh"), false, "刷新状态", "刷新中...");
        }}
        runtimeRefreshing = false;
      }}
    }}
    async function refreshSnowlumaOverview(opts = {{}}) {{
      const silent = !!opts.silent;
      if (!silent) {{
        setBtnBusy(document.getElementById("btnAssetRefresh"), true, "刷新状态", "刷新中...");
      }}
      try {{
        const sl = await api("/api/snowluma/runtime/overview");
        fillRuntimeOverviewFromPayload(sl);
      }} catch (e) {{
        {{
          const rs = document.getElementById("runtimeStatus");
          if (rs && !shouldPauseLiveLogDomWrite(rs)) rs.textContent = String(e.message || e);
        }}
        setText("rtStatus", "失败");
        setText("rtStage", "错误");
        setText("rtMessage", String(e.message || e));
        setText("rtTime", new Date().toLocaleTimeString());
        if (!silent) alert(String(e.message || e));
      }} finally {{
        if (!silent) {{
          setBtnBusy(document.getElementById("btnAssetRefresh"), false, "刷新状态", "刷新中...");
        }}
      }}
    }}
    async function loadAssetReleases() {{
      const btn = document.getElementById("btnLoadReleases");
      const ra = document.getElementById("releasesArea");
      const rp = document.getElementById("releasesPlaceholder");
      const sel = document.getElementById("releaseSelect");
      if (!sel || !ra || !rp) return;
      if (btn) {{
        btn.disabled = true;
        btn.textContent = "加载中…";
      }}
      try {{
        const url = assetsProtoIsSl()
          ? "/api/snowluma/runtime/releases?limit=200"
          : "/api/runtime/releases?limit=200";
        const data = await api(url);
        const raw = Array.isArray(data.releases) ? data.releases : [];
        _assetReleaseList = raw
          .map((x) => {{
            const tn = String(x.tag_name || x.tag || "").trim();
            if (!tn) return null;
            return {{ ...x, tag_name: tn }};
          }})
          .filter(Boolean);
        if (!_assetReleaseList.length) {{
          sel.innerHTML = "";
          ra.style.display = "block";
          rp.style.display = "block";
          rp.textContent =
            "未获取到版本列表（请检查仓库配置、网络或 GitHub API 限流；可在配置中设置 pallas_protocol_github_token）。";
          const det = document.getElementById("releaseDetail");
          if (det) det.textContent = "";
          return;
        }}
        rp.style.display = "none";
        sel.innerHTML = _assetReleaseList.map((r) => {{
          const tag = r.tag_name;
          const label = tag + (r.prerelease ? " (pre)" : "") + (r.name && r.name !== tag ? " · " + r.name : "");
          return `<option value="${{invEsc(tag)}}">${{invEsc(label)}}</option>`;
        }}).join("");
        ra.style.display = "block";
        updateAssetReleaseDetail();
        sel.onchange = () => updateAssetReleaseDetail();
        if (typeof initShellPrettySelects === "function") initShellPrettySelects(ra);
        if (typeof shellPrettySyncSelect === "function") shellPrettySyncSelect(sel);
      }} catch (e) {{
        alert("加载 release 列表失败: " + (e.message || e));
      }} finally {{
        if (btn) {{
          btn.disabled = false;
          btn.textContent = "加载版本列表";
        }}
      }}
    }}
    function updateAssetReleaseDetail() {{
      const releases = _assetReleaseList || [];
      const sel = document.getElementById("releaseSelect");
      if (!sel) return;
      const tag = sel.value;
      const r = releases.find((x) => x.tag_name === tag);
      const el = document.getElementById("releaseDetail");
      if (!el) return;
      if (!r) {{ el.textContent = ""; return; }}
      const parts = [];
      if (r.published_at) parts.push("发布于 " + new Date(r.published_at).toLocaleDateString("zh-CN"));
      if (r.assets && r.assets.length) parts.push("资产: " + r.assets.map((a) => a.name).join(", "));
      el.textContent = parts.join(" · ");
    }}
    function fillRuntimeOverviewFromPayload(sl) {{
      if (!sl) sl = {{}};
      const job = sl.job || {{}};
      const d = sl.download || {{}};
      const manifest = sl.manifest || {{}};
      setText("rtStatus", statusText(job.status));
      setText("rtStage", stageText(job.message));
      const tag = pendingSnowlumaTag || job.tag || manifest.release_tag || d.tag || "";
      const assetEl = document.getElementById("rtAsset");
      if (assetEl) assetEl.title = String(d.asset || manifest.asset_name || "");
      setText("rtAsset", tag || d.asset || manifest.asset_name || "-");
      setText("rtMessage", job.message || "-");
      const repo = d.repo || "-";
      const tagHint = tag || d.tag || "latest";
      setText("rtSource", manifest.source_url ? manifest.source_url : `${{repo}} @ ${{tagHint}}`);
      setText("rtProgramDir", sl.effective_program_dir || manifest.program_dir || "-");
      setText("rtTime", new Date().toLocaleTimeString());
      const pre = document.getElementById("runtimeStatus");
      if (pre && !shouldPauseLiveLogDomWrite(pre)) pre.textContent = JSON.stringify(sl, null, 2);
    }}
    async function assetActivateSelectedTag() {{
      const sel = document.getElementById("releaseSelect");
      const tag = sel ? sel.value : "";
      if (!tag) {{ alert("请先选择版本"); return; }}
      if (assetsProtoIsSl()) {{
        try {{
          await api("/api/snowluma/runtime/activate-tag", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{ tag }}),
          }});
          pendingSnowlumaTag = null;
          const slo = await api("/api/snowluma/runtime/overview");
          fillRuntimeOverviewFromPayload(slo);
          await loadAssetLocalInventory();
          alert("已将托管切换到版本 " + tag + "。");
        }} catch (e) {{
          const msg = String(e.message || e);
          if (msg.includes("未找到") && msg.includes("解压")) {{
            pendingSnowlumaTag = tag;
            setText("rtAsset", tag);
            setText("rtStatus", "待更新");
            setText("rtStage", "已选择");
            setText("rtMessage", "本地尚无该版本解压目录，已选中 " + tag + "，请点击「下载 / 更新」");
            setText("rtTime", new Date().toLocaleTimeString());
            const btn = document.getElementById("btnDownloadTag");
            if (btn) {{
              const prev = btn.textContent;
              btn.textContent = "✓ 待下载";
              setTimeout(() => {{ btn.textContent = prev; }}, 1500);
            }}
          }} else {{
            alert(msg);
          }}
        }}
        return;
      }}
      try {{
        await api("/api/runtime/activate-tag", {{
          method: "POST",
          headers: {{ "Content-Type": "application/json" }},
          body: JSON.stringify({{ tag }}),
        }});
        pendingTag = null;
        await refreshRuntime({{ silent: true }});
        await loadAssetLocalInventory();
        alert("已将托管切换到版本 " + tag + "。");
      }} catch (e) {{
        const msg = String(e.message || e);
        if (msg.includes("未找到") && msg.includes("解压")) {{
          pendingTag = tag;
          const detailEl = document.getElementById("releaseDetail");
          const assetHint = detailEl ? detailEl.textContent : "";
          setText("rtAsset", tag);
          setText("rtSource", assetHint ? "待下载: " + assetHint : "待下载: " + tag);
          setText("rtStatus", "待更新");
          setText("rtStage", "已选择");
          setText("rtMessage", "本地尚无该版本解压目录，已选中 " + tag + "，请点击「立即更新」下载");
          setText("rtTime", new Date().toLocaleTimeString());
          const btn = document.getElementById("btnDownloadTag");
          if (btn) {{
            const prev = btn.textContent;
            btn.textContent = "✓ 待下载";
            setTimeout(() => {{ btn.textContent = prev; }}, 1500);
          }}
        }} else {{
          alert(msg);
        }}
      }}
    }}
    async function downloadRuntime() {{
      const mode = String(document.getElementById("runtimeModeNapcat")?.value || "");
      if (mode === "docker") {{
        alert("Docker 模式无需下载发行包，请使用上方「NapCat Docker 镜像」旁的「拉取镜像」。");
        return;
      }}
      const dl = document.getElementById("btnAssetDownload");
      setBtnBusy(dl, true, "立即更新", "更新中...");
      try {{
        const tp = String(document.getElementById("targetPlatform")?.value || "auto");
        const modeQ = String(document.getElementById("runtimeModeNapcat")?.value || "");
        const qs = [];
        if (tp) qs.push("target_platform=" + encodeURIComponent(tp));
        if (modeQ) qs.push("runtime_mode=" + encodeURIComponent(modeQ));
        const url = pendingTag
          ? "/api/runtime/download?tag=" + encodeURIComponent(pendingTag) + (qs.length ? "&" + qs.join("&") : "")
          : "/api/runtime/download" + (qs.length ? "?" + qs.join("&") : "");
        await api(url, {{ method: "POST" }});
        pendingTag = null;
        await refreshRuntime();
        void loadAssetLocalInventory();
      }} catch (e) {{ alert(e.message); }}
      finally {{
        setBtnBusy(dl, false, "立即更新", "更新中...");
        syncAssetDownloadButtonText();
      }}
    }}
    async function rescanRuntime() {{
      if (assetsProtoIsSl()) return;
      setBtnBusy(document.getElementById("btnRescan"), true, "刷新检测", "检测中...");
      try {{
        await api("/api/runtime/rescan", {{ method: "POST" }});
        await refreshRuntime();
        void loadAssetLocalInventory();
      }} catch (e) {{ alert(e.message); }}
      finally {{
        setBtnBusy(document.getElementById("btnRescan"), false, "刷新检测", "检测中...");
      }}
    }}
    async function downloadSnowlumaRuntime() {{
      const dl = document.getElementById("btnAssetDownload");
      setBtnBusy(dl, true, "下载 / 更新", "处理中...");
      try {{
        const tp = String(document.getElementById("slTargetPlatform")?.value || "auto");
        try {{ localStorage.setItem("pallas_protocol_sl_target_platform", tp); }} catch (e) {{}}
        const qs = [];
        if (pendingSnowlumaTag) qs.push("tag=" + encodeURIComponent(pendingSnowlumaTag));
        if (tp && tp !== "auto") qs.push("target_platform=" + encodeURIComponent(tp));
        const q = qs.length ? ("?" + qs.join("&")) : "";
        await api("/api/snowluma/runtime/download" + q, {{ method: "POST" }});
        pendingSnowlumaTag = null;
        const slo = await api("/api/snowluma/runtime/overview");
        fillRuntimeOverviewFromPayload(slo);
        void loadAssetLocalInventory();
      }} catch (e) {{ alert(e.message || e); }}
      finally {{
        setBtnBusy(dl, false, "下载 / 更新", "处理中...");
        syncAssetDownloadButtonText();
      }}
    }}
{token_sync_js}
    loadRuntimeProfile().catch((e) => {{
      const rs = document.getElementById("runtimeStatus");
      if (rs && !shouldPauseLiveLogDomWrite(rs)) rs.textContent = "加载 profile 失败: " + String(e.message || e);
    }});
    assetRefreshOverview({{ silent: true }}).catch(() => {{}});
    setInterval(() => {{ void assetRefreshOverview({{ silent: true }}); }}, 1200);
  </script>
</body>
</html>
"""

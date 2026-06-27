# ruff: noqa: E501
"""偏好设置页。"""

from __future__ import annotations

import json

from ..contract import resolve_public_mount_path

from .shell_layout import (
    render_protocol_shell_close,
    render_protocol_shell_open,
    shell_head_assets,
)
from .shell_js import _render_common_api_js, _render_hidden_token_sync_js


def render_settings_page(
    base_path: str, pallas_console_http_base: str = "/pallas"
) -> str:
    """协议端偏好设置：与 WebUI 共用 localStorage。"""
    path = base_path.rstrip("/") or resolve_public_mount_path(
        path_override="", implementation_slug=""
    )
    p = json.dumps(path)
    common_api_js = _render_common_api_js()
    token_sync_js = _render_hidden_token_sync_js("backDash")
    shell_open = render_protocol_shell_open(
        path,
        pallas_console_http_base,
        active="settings",
        page_title="偏好设置",
        page_desc="外观、轮询与控制台口令",
    )
    shell_close = render_protocol_shell_close(
        path, active="settings", pallas_console_http_base=pallas_console_http_base
    )
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
{shell_head_assets(path)}  <title>偏好设置 · 协议端</title>
  <style>
.pref-card {{ margin-bottom: 14px; }}
.pref-title {{ margin: 0 0 6px; font-size: 1rem; }}
.pref-desc {{ margin: 0 0 12px; font-size: 0.82rem; color: var(--muted); line-height: 1.45; }}
.pref-row {{ display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }}
.pref-chip {{
  display: inline-flex; align-items: center; gap: 6px;
  border-radius: 10px; border: 1px solid var(--bd); padding: 9px 14px;
  font-size: 0.82rem; font-weight: 600; cursor: pointer;
  background: color-mix(in srgb, var(--bg1) 88%, transparent); color: var(--txt);
}}
.pref-chip.on {{ border-color: var(--accent); background: color-mix(in srgb, var(--accent) 14%, transparent); color: var(--accent-strong); }}
.pref-swatch {{
  width: 36px; height: 36px; border-radius: 50%; border: 2px solid var(--bd); cursor: pointer; padding: 0;
}}
.pref-swatch.on {{ border-color: var(--txt); box-shadow: 0 0 0 2px color-mix(in srgb, var(--accent) 35%, transparent); }}
.pref-dens {{
  display: grid; gap: 10px; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
}}
.pref-dens button {{
  text-align: left; border-radius: 12px; border: 1px solid var(--bd); padding: 14px 16px;
  cursor: pointer; background: var(--card); color: var(--txt); font: inherit;
}}
.pref-dens button.on {{ border-color: var(--accent); background: color-mix(in srgb, var(--accent) 12%, transparent); }}
.pref-dens .t {{ font-weight: 650; font-size: 0.88rem; display: block; margin-bottom: 4px; }}
.pref-dens .d {{ font-size: 0.72rem; color: var(--muted); line-height: 1.4; }}
  </style>
</head>
<body>
  <input type="hidden" id="token" value="" autocomplete="off" />
  {shell_open}
    <div class="section" style="max-width:52rem;margin:0 auto;padding-bottom:48px">
      <div class="card pref-card">
        <h3 class="pref-title">统一控制台口令</h3>
        <p class="pref-desc">保存后需重新登录。</p>
        <div class="pref-row" style="flex-direction:column;align-items:stretch;gap:10px">
          <input id="prefNewConsolePw" type="password" autocomplete="new-password" placeholder="新口令" style="width:100%;border-radius:10px;border:1px solid var(--bd);padding:10px 12px;font:inherit;background:var(--card);color:var(--txt)" />
          <input id="prefNewConsolePw2" type="password" autocomplete="new-password" placeholder="再次输入" style="width:100%;border-radius:10px;border:1px solid var(--bd);padding:10px 12px;font:inherit;background:var(--card);color:var(--txt)" />
          <button type="button" class="btn" id="prefBtnSaveConsolePw">保存新口令</button>
          <p class="muted" id="prefConsolePwMsg" style="margin:0;font-size:0.78rem"></p>
        </div>
      </div>
      <div class="card pref-card">
        <h3 class="pref-title">显示模式</h3>
        <p class="pref-desc">浅色 / 深色 / 跟随系统；与 Pallas-Bot 控制台、顶部栏切换共用存储键。</p>
        <div class="pref-row" id="prefThemeRow"></div>
      </div>
      <div class="card pref-card">
        <h3 class="pref-title">强调色</h3>
        <p class="pref-desc">与 Pallas-Bot 控制台偏好中的强调色预设共用存储。</p>
        <div class="pref-row" id="prefAccentRow"></div>
        <p class="muted" style="margin:10px 0 0;font-size:0.78rem" id="prefAccentHint"></p>
      </div>
      <div class="card pref-card">
        <h3 class="pref-title">圆角</h3>
        <div class="pref-row" id="prefRadiusRow"></div>
      </div>
      <div class="card pref-card">
        <h3 class="pref-title">显示密度</h3>
        <div class="pref-dens" id="prefDensityRow"></div>
      </div>
      <div class="card pref-card">
        <h3 class="pref-title">仪表盘轮询</h3>
        <p class="pref-desc">协议仪表盘「自动刷新日志」等定时拉取间隔（毫秒）；暂停即不后台拉取。</p>
        <div class="pref-row" id="prefPollRow"></div>
        <p class="muted" style="margin:10px 0 0;font-size:0.78rem" id="prefPollHint"></p>
      </div>
    </div>
{shell_close}
  <script>
    const basePath = {p};
{common_api_js}
{token_sync_js}
    initPallasShellThemeFromStorage();
    applyShellUiPrefsFromStorage();
    initProtocolShellChrome();
    const ACCENTS = [
      {{ id: "sky", label: "天蓝", swatch: "#38bdf8" }},
      {{ id: "indigo", label: "靛蓝", swatch: "#818cf8" }},
      {{ id: "emerald", label: "翠绿", swatch: "#34d399" }},
      {{ id: "rose", label: "玫红", swatch: "#fb7185" }},
      {{ id: "amber", label: "琥珀", swatch: "#fbbf24" }},
      {{ id: "violet", label: "紫罗兰", swatch: "#a78bfa" }},
    ];
    const RADII = [
      {{ id: "tight", label: "紧凑" }},
      {{ id: "default", label: "默认" }},
      {{ id: "round", label: "圆润" }},
    ];
    const POLLS = [
      {{ value: 0, label: "暂停" }},
      {{ value: 1500, label: "1.5 秒" }},
      {{ value: 3000, label: "3 秒" }},
      {{ value: 5000, label: "5 秒" }},
      {{ value: 10000, label: "10 秒" }},
      {{ value: 30000, label: "30 秒" }},
    ];
    function syncPrefsUi() {{
      const prefs = readConsolePrefsJson();
      try {{
        const mode = resolveThemeModeFromStorage();
        document.querySelectorAll("#prefThemeRow .pref-chip").forEach((b) => {{
          b.classList.toggle("on", b.dataset.mode === mode);
        }});
      }} catch (e) {{}}
      try {{
        const accent = __SHELL_ACCENT_IDS.includes(prefs.accentPreset) ? prefs.accentPreset : "sky";
        document.querySelectorAll("#prefAccentRow .pref-swatch").forEach((b) => {{
          b.classList.toggle("on", b.dataset.accent === accent);
        }});
        const lab = ACCENTS.find((a) => a.id === accent);
        document.getElementById("prefAccentHint").textContent = "当前：" + (lab ? lab.label : accent);
      }} catch (e) {{}}
      try {{
        const radius = prefs.radius === "tight" || prefs.radius === "round" ? prefs.radius : "default";
        document.querySelectorAll("#prefRadiusRow .pref-chip").forEach((b) => {{
          b.classList.toggle("on", b.dataset.radius === radius);
        }});
      }} catch (e) {{}}
      try {{
        const d = prefs.density === "compact" ? "compact" : "comfortable";
        document.querySelectorAll("#prefDensityRow button").forEach((b) => {{
          b.classList.toggle("on", b.dataset.density === d);
        }});
      }} catch (e) {{}}
      try {{
        const poll = parseInt(localStorage.getItem("pallas-dashboard-poll-ms") || "3000", 10);
        const pv = Number.isFinite(poll) ? poll : 3000;
        document.querySelectorAll("#prefPollRow .pref-chip").forEach((b) => {{
          b.classList.toggle("on", parseInt(b.dataset.ms || "0", 10) === pv);
        }});
        const hint = document.getElementById("prefPollHint");
        if (hint) hint.textContent = pv === 0 ? "当前：已暂停轮询" : ("当前：" + pv + " 毫秒");
      }} catch (e) {{}}
    }}
    function wirePrefsPage() {{
      const tr = document.getElementById("prefThemeRow");
      [["light","浅色"],["dark","深色"],["system","跟随系统"]].forEach(([m, lab]) => {{
        const b = document.createElement("button");
        b.type = "button";
        b.className = "pref-chip";
        b.dataset.mode = m;
        b.textContent = lab;
        b.addEventListener("click", () => {{
          writeConsolePrefsJson({{ theme: m }});
          try {{ localStorage.setItem(PALLAS_THEME_MODE_KEY, m); }} catch (e) {{}}
          applyPallasShellTheme(resolvePallasThemePreference(), {{ persist: false }});
          applyShellUiPrefsFromStorage();
          syncShellThemeToolbar();
          syncPrefsUi();
        }});
        tr.appendChild(b);
      }});
      const ar = document.getElementById("prefAccentRow");
      ACCENTS.forEach((a) => {{
        const b = document.createElement("button");
        b.type = "button";
        b.className = "pref-swatch";
        b.dataset.accent = a.id;
        b.title = a.label;
        b.style.backgroundColor = a.swatch;
        b.addEventListener("click", () => {{
          writeConsolePrefsJson({{ accentPreset: a.id }});
          applyShellUiPrefsFromStorage();
          syncPrefsUi();
        }});
        ar.appendChild(b);
      }});
      const rr = document.getElementById("prefRadiusRow");
      RADII.forEach((r) => {{
        const b = document.createElement("button");
        b.type = "button";
        b.className = "pref-chip";
        b.dataset.radius = r.id;
        b.textContent = r.label;
        b.addEventListener("click", () => {{
          writeConsolePrefsJson({{ radius: r.id }});
          applyShellUiPrefsFromStorage();
          syncPrefsUi();
        }});
        rr.appendChild(b);
      }});
      const dr = document.getElementById("prefDensityRow");
      [
        {{ key: "comfortable", title: "舒适", desc: "默认间距，阅读更轻松" }},
        {{ key: "compact", title: "紧凑", desc: "更小字号与行距，单屏更多信息" }},
      ].forEach((x) => {{
        const b = document.createElement("button");
        b.type = "button";
        b.dataset.density = x.key;
        b.innerHTML = "<span class=\\"t\\">" + x.title + "</span><span class=\\"d\\">" + x.desc + "</span>";
        b.addEventListener("click", () => {{
          writeConsolePrefsJson({{ density: x.key }});
          applyShellUiPrefsFromStorage();
          syncPrefsUi();
        }});
        dr.appendChild(b);
      }});
      const pr = document.getElementById("prefPollRow");
      POLLS.forEach((p) => {{
        const b = document.createElement("button");
        b.type = "button";
        b.className = "pref-chip";
        b.dataset.ms = String(p.value);
        b.textContent = p.label;
        b.addEventListener("click", () => {{
          try {{
            localStorage.setItem("pallas-dashboard-poll-ms", String(p.value));
            window.dispatchEvent(new Event("pallas-dashboard-poll-changed"));
          }} catch (e) {{}}
          syncPrefsUi();
        }});
        pr.appendChild(b);
      }});
      syncPrefsUi();
    }}
    wirePrefsPage();
    (function wireConsolePw() {{
      const b = document.getElementById("prefBtnSaveConsolePw");
      const a = document.getElementById("prefNewConsolePw");
      const c = document.getElementById("prefNewConsolePw2");
      const msg = document.getElementById("prefConsolePwMsg");
      if (!b || !a || !c) return;
      b.addEventListener("click", async () => {{
        const p1 = (a.value || "").trim();
        const p2 = (c.value || "").trim();
        if (!p1) return;
        if (p1 !== p2) {{ if (msg) msg.textContent = "两次输入不一致"; return; }}
        if (msg) msg.textContent = "提交中…";
        try {{
          await api("/api/security/console-login", {{
            method: "POST",
            headers: {{ "Content-Type": "application/json" }},
            body: JSON.stringify({{ new_password: p1 }}),
          }});
          a.value = "";
          c.value = "";
          if (msg) msg.textContent = "已保存";
        }} catch (e) {{
          if (msg) msg.textContent = String(e && e.message ? e.message : e);
        }}
      }});
    }})();
  </script>
</body>
</html>
"""

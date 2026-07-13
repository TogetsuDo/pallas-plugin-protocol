# ruff: noqa: E501
"""协议端壳层 HTML 与导航。"""

from __future__ import annotations

import json
from datetime import datetime
from html import escape as html_escape

from ..shell_nav_icons import render_console_nav_icon


def shell_brand_mark_src(public_base_path: str) -> str:
    """侧栏品牌图。"""
    p = (public_base_path or "").strip().rstrip("/")
    return f"{p}/_pallas_ui/favicon.png" if p else "/_pallas_ui/favicon.png"


def shell_favicon_link(public_base_path: str) -> str:
    """favicon：静态目录 ``favicon.png``。"""
    href = shell_brand_mark_src(public_base_path)
    return f'  <link rel="icon" type="image/png" href="{html_escape(href, quote=True)}" />\n'


def shell_footer_html() -> str:
    y = datetime.now().year
    return f'    <footer class="shell-footer" role="contentinfo">© {y} Pallas-Bot</footer>\n'


def shell_font_stylesheet_link(public_base_path: str) -> str:
    """与 WebUI main.ts @fontsource 一致：Poppins + Noto Sans SC + JetBrains Mono。"""
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


def shell_stylesheet_link(public_base_path: str) -> str:
    """协议壳主样式。"""
    p = (public_base_path or "").strip().rstrip("/")
    href = f"{p}/_pallas_ui/shell.css" if p else "/_pallas_ui/shell.css"
    return f'  <link rel="stylesheet" href="{html_escape(href, quote=True)}" />\n'


def shell_theme_boot_inline_script() -> str:
    """首屏防闪：在 CSS 加载前读取与 WebUI 共用的 consolePrefs。"""
    return """  <script>
(function () {
  try {
    const raw = localStorage.getItem("pallas_console_prefs_v1");
    const prefs = raw ? JSON.parse(raw) : {};
    let mode = prefs.theme;
    if (mode !== "dark" && mode !== "light" && mode !== "system") {
      mode = localStorage.getItem("pallas-theme-mode") || "system";
    }
    const resolved =
      mode === "dark"
        ? "dark"
        : mode === "light"
          ? "light"
          : window.matchMedia("(prefers-color-scheme: dark)").matches
            ? "dark"
            : "light";
    const root = document.documentElement;
    root.dataset.theme = resolved;
    root.style.colorScheme = resolved;
    root.dataset.layout = "hub";
    root.dataset.surface = prefs.surfaceStyle === "solid" ? "solid" : "glass";
    root.dataset.uiPreset = prefs.uiPreset === "shadcn" ? "shadcn" : "gs";
    const accent = prefs.accentPreset || "sky";
    if (accent) root.dataset.accent = accent;
    const radius = prefs.radius;
    if (radius === "tight" || radius === "round") root.dataset.radius = radius;
    if (prefs.density === "compact") root.dataset.density = "compact";
    const blur = Number(prefs.glassBlur);
    if (Number.isFinite(blur)) root.style.setProperty("--surface-blur", blur + "px");
    const opacity = Number(prefs.cardGlassOpacity);
    if (Number.isFinite(opacity)) {
      root.style.setProperty("--card-glass-opacity", String(opacity));
      root.style.setProperty("--shell-glass-pct", Math.round(opacity * 100) + "%");
    }
  } catch (e) {}
})();
  </script>
"""


def shell_head_assets(public_base_path: str) -> str:
    return (
        shell_favicon_link(public_base_path)
        + shell_theme_boot_inline_script()
        + shell_font_stylesheet_link(public_base_path)
        + shell_stylesheet_link(public_base_path)
    )


def _normalize_pallas_console_http_base(raw: str | None) -> str:
    s = (raw or "").strip() or "/pallas"
    if not s.startswith("/"):
        s = "/" + s
    s = s.rstrip("/")
    return s or "/pallas"


def shell_pallas_web_console_topbar_chunk(pallas_console_http_base: str) -> str:
    root_js = json.dumps(_normalize_pallas_console_http_base(pallas_console_http_base))
    return (
        '<a class="btn secondary" id="linkPallasWebConsole" href="#" target="_blank" rel="noopener noreferrer">'
        "前往前端控制台</a>"
        f"<script>(function(){{var e=document.getElementById('linkPallasWebConsole');"
        f"if(e)e.href=location.origin+{root_js}+'/';}})();</script>"
    )


def shell_pallas_web_console_nav_link(
    pallas_console_http_base: str,
    *,
    link_class: str = "shell__nav-link",
    element_id: str = "linkPallasWebConsole",
) -> str:
    """侧栏 / 移动抽屉「前端控制台」入口。"""
    root_js = json.dumps(_normalize_pallas_console_http_base(pallas_console_http_base))
    eid = html_escape(element_id, quote=True)
    return (
        f'<a class="{html_escape(link_class)} shell__nav-link--ext" id="{eid}" href="#" title="前端控制台" '
        'target="_blank" rel="noopener noreferrer">'
        f"{render_console_nav_icon('globe')}"
        '<span class="shell__nav-text"><span class="shell__nav-label">前端控制台</span>'
        '<span class="shell__nav-desc">Pallas WebUI</span></span></a>'
        f"<script>(function(){{var e=document.getElementById({json.dumps(element_id)});"
        f"if(e)e.href=location.origin+{root_js}+'/';}})();</script>"
    )


_PROTOCOL_NAV: tuple[tuple[str, str, str, str, str], ...] = (
    ("dashboard", "", "dashboard", "仪表盘", "账号与运行日志"),
    ("new", "/new", "account", "创建账号", "新建协议实例"),
    ("import", "/import", "download", "导入账号", "批量导入旧数据"),
    ("assets", "/assets", "blocks", "协议资产", "运行时与镜像"),
    ("settings", "/settings", "settings", "偏好设置", "外观与轮询"),
)


def _render_protocol_nav_links(
    base_path: str,
    active: str,
    *,
    link_class: str,
) -> str:
    p = (base_path or "").strip().rstrip("/")
    links: list[str] = []
    for nav_id, suffix, icon_id, label, desc in _PROTOCOL_NAV:
        href = html_escape(f"{p}{suffix}" if suffix else f"{p}/", quote=True)
        cls = f"{link_class} is-router-active" if nav_id == active else link_class
        label_esc = html_escape(label)
        icon_html = render_console_nav_icon(icon_id)
        links.append(
            f'<a class="{cls}" href="{href}" title="{label_esc}">'
            f"{icon_html}"
            f'<span class="shell__nav-text"><span class="shell__nav-label">{label_esc}</span>'
            f'<span class="shell__nav-desc">{html_escape(desc)}</span></span></a>'
        )
    return "\n        ".join(links)


def _render_protocol_sidebar(
    base_path: str, active: str, pallas_console_http_base: str
) -> str:
    p = (base_path or "").strip().rstrip("/")
    home = html_escape(f"{p}/", quote=True)
    nav_body = _render_protocol_nav_links(
        base_path, active, link_class="shell__nav-link"
    )
    ext = shell_pallas_web_console_nav_link(pallas_console_http_base)
    mark_src = html_escape(shell_brand_mark_src(p), quote=True)
    return f"""    <aside class="shell__sidebar" aria-label="协议端导航">
      <div class="shell__sidebar-top">
        <a class="shell__brand" href="{home}">
          <img class="shell__brand-mark" src="{mark_src}" alt="" width="28" height="28" decoding="async" />
          <span class="shell__brand-text">
            <span class="shell__brand-name shell__title">Pallas-Bot</span>
            <span class="shell__brand-sub">协议端</span>
          </span>
        </a>
      </div>
      <nav class="shell__nav">
        <div class="shell__nav-section">管理</div>
        {nav_body}
        <div class="shell__nav-section">外部</div>
        {ext}
      </nav>
    </aside>"""


def _render_protocol_mobile_nav(
    base_path: str, active: str, pallas_console_http_base: str
) -> str:
    mark_src = html_escape(shell_brand_mark_src(base_path), quote=True)
    nav_body = _render_protocol_nav_links(
        base_path, active, link_class="shell-mobile-nav__link"
    )
    ext = shell_pallas_web_console_nav_link(
        pallas_console_http_base,
        link_class="shell-mobile-nav__link",
        element_id="linkPallasWebConsoleMobile",
    )
    return f"""  <div id="protoMobileNav" class="shell-mobile-nav" hidden>
    <aside id="proto-mobile-nav-panel" class="shell-mobile-nav__panel" role="dialog" aria-modal="true" aria-label="协议端导航">
      <div class="shell-mobile-nav__head">
        <div class="shell-mobile-nav__brand-block">
          <img class="shell-mobile-nav__mark" src="{mark_src}" alt="" width="28" height="28" decoding="async" />
          <div class="shell-mobile-nav__brand-text">
            <span class="shell-mobile-nav__brand">Pallas-Bot</span>
            <span class="shell-mobile-nav__ver">协议端</span>
          </div>
        </div>
        <button type="button" class="shell-mobile-nav__close" id="protoMobileNavClose" aria-label="关闭菜单">×</button>
      </div>
      <nav class="shell-mobile-nav__links" aria-label="协议端导航">
        <div class="shell-mobile-nav__section" role="presentation">管理</div>
        {nav_body}
        <div class="shell-mobile-nav__section" role="presentation">外部</div>
        {ext}
      </nav>
    </aside>
    <div class="shell-mobile-nav__backdrop" id="protoMobileNavBackdrop" aria-hidden="true"></div>
  </div>"""


def shell_topbar_collapse_html() -> str:
    return """      <div class="shell__topbar-start">
        <div class="shell__topbar-rail">
          <button type="button" class="shell__topbar-collapse" id="protoSidebarCollapse" aria-expanded="true" aria-label="收起菜单栏">«</button>
          <button type="button" class="shell__topbar-menu" id="protoMobileNavOpen" aria-label="打开导航菜单" aria-controls="proto-mobile-nav-panel">☰</button>
          <span class="shell__topbar-vrule" aria-hidden="true"></span>
        </div>
      </div>"""


def shell_topbar_theme_html() -> str:
    moon = (
        '<svg class="shell__ico" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">'
        '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>'
    )
    sun = (
        '<svg class="shell__ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<circle cx="12" cy="12" r="4"/>'
        '<path d="M12 2v2m0 16v2M2 12h2m16 0h2M4.93 4.93l1.41 1.41m11.31 11.31l1.41 1.41'
        'M19.07 4.93l-1.41 1.41M6.34 17.66l-1.41 1.41"/></svg>'
    )
    monitor = (
        '<svg class="shell__ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
        '<rect x="2" y="3" width="20" height="14" rx="2"/><path d="M8 21h8M12 17v4"/></svg>'
    )
    return f"""        <div class="shell-toolbar__seg shell-toolbar__seg--compact shell__topbar-theme" role="group" aria-label="颜色模式">
          <button type="button" data-proto-theme="dark" title="深色" aria-label="深色">
            <span class="shell__theme-ico">{moon}</span>
          </button>
          <button type="button" data-proto-theme="light" title="浅色" aria-label="浅色">
            <span class="shell__theme-ico">{sun}</span>
          </button>
          <button type="button" data-proto-theme="system" title="跟随系统" aria-label="跟随系统">
            <span class="shell__theme-ico">{monitor}</span>
          </button>
        </div>"""


def render_protocol_shell_open(
    base_path: str,
    pallas_console_http_base: str,
    *,
    active: str,
    page_title: str,
    page_desc: str = "",
    topbar_actions: str = "",
) -> str:
    sidebar = _render_protocol_sidebar(base_path, active, pallas_console_http_base)
    title_esc = html_escape(page_title)
    desc_block = (
        f'<p class="shell__topbar-desc muted shell__topbar-desc--hide-narrow">{html_escape(page_desc)}</p>'
        if (page_desc or "").strip()
        else ""
    )
    return f"""  <div class="shell__bg" aria-hidden="true"></div>
  <div class="shell proto-shell">
{sidebar}
    <header class="shell__topbar">
{shell_topbar_collapse_html()}
      <div class="shell__topbar-lead">
        <h1 class="shell__topbar-title"><span class="shell__topbar-title-text">{title_esc}</span></h1>
        {desc_block}
      </div>
      <div class="shell__topbar-end row-actions">
{shell_topbar_theme_html()}
        {topbar_actions}
        <button class="btn secondary shell__topbar-exit" type="button" data-action="logout" title="退出登录" aria-label="退出登录">退出</button>
      </div>
    </header>
    <main class="shell__main">
      <div class="shell__main-inner proto-shell__main-inner">
"""


def render_protocol_shell_close(
    base_path: str,
    *,
    active: str,
    pallas_console_http_base: str,
) -> str:
    mobile_nav = _render_protocol_mobile_nav(
        base_path, active, pallas_console_http_base
    )
    return f"""{shell_footer_html()} </div>
    </main>
  </div>
{mobile_nav}
"""


def _pallas_theme_bridge_js() -> str:
    """与 Pallas-Bot-WebUI consolePrefs 共用 pallas_console_prefs_v1。"""
    return """
    const PALLAS_CONSOLE_PREFS_KEY = "pallas_console_prefs_v1";
    const PALLAS_THEME_KEY = "pallas-webui-theme";
    const PALLAS_PROTOCOL_THEME_LEGACY = "pallas_protocol_theme";
    const PALLAS_THEME_MODE_KEY = "pallas-theme-mode";
    const __SHELL_ACCENT_IDS = ["sky", "indigo", "emerald", "rose", "amber", "violet"];
    function readConsolePrefsJson() {
      try {
        const raw = localStorage.getItem(PALLAS_CONSOLE_PREFS_KEY);
        if (!raw) return {};
        const o = JSON.parse(raw);
        return o && typeof o === "object" ? o : {};
      } catch (e) { return {}; }
    }
    function writeConsolePrefsJson(patch) {
      try {
        const cur = readConsolePrefsJson();
        localStorage.setItem(PALLAS_CONSOLE_PREFS_KEY, JSON.stringify({ ...cur, ...patch }));
      } catch (e) {}
    }
    function resolveThemeModeFromStorage() {
      const prefs = readConsolePrefsJson();
      let mode = prefs.theme;
      if (mode !== "dark" && mode !== "light" && mode !== "system") {
        try {
          const legacy = localStorage.getItem(PALLAS_THEME_MODE_KEY);
          if (legacy === "dark" || legacy === "light" || legacy === "system") mode = legacy;
        } catch (e) {}
      }
      if (mode !== "dark" && mode !== "light" && mode !== "system") return "system";
      return mode;
    }
    function resolvePallasThemePreference() {
      const mode = resolveThemeModeFromStorage();
      if (mode === "system") {
        try {
          return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
        } catch (e) { return "light"; }
      }
      return mode;
    }
    function applyPallasShellTheme(resolved, options) {
      const next = resolved === "dark" ? "dark" : "light";
      const root = document.documentElement;
      root.dataset.theme = next;
      root.style.colorScheme = next;
      document.body.setAttribute("data-theme", next);
      document.documentElement.classList.toggle("dark", next === "dark");
      applyShellUiPrefsFromStorage();
      const persist = options && options.persist;
      if (!persist) return;
      try {
        localStorage.setItem(PALLAS_THEME_KEY, next);
        localStorage.setItem(PALLAS_PROTOCOL_THEME_LEGACY, next);
      } catch (e) {}
    }
    function initPallasShellThemeFromStorage() {
      applyPallasShellTheme(resolvePallasThemePreference(), { persist: false });
    }
    try {
      window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
        if (resolveThemeModeFromStorage() === "system") {
          applyPallasShellTheme(resolvePallasThemePreference(), { persist: false });
        }
      });
    } catch (e) {}
"""


def _shell_prefs_js() -> str:
    """与 WebUI consolePrefs：data-accent / data-radius / data-density。"""
    return """
    function applyShellUiPrefsFromStorage() {
      const prefs = readConsolePrefsJson();
      const root = document.documentElement;
      const accentIds = ["sky", "indigo", "emerald", "rose", "amber", "violet"];
      const accent = accentIds.includes(prefs.accentPreset) ? prefs.accentPreset : "sky";
      root.dataset.accent = accent;
      root.dataset.layout = "hub";
      root.dataset.surface = prefs.surfaceStyle === "solid" ? "solid" : "glass";
      root.dataset.uiPreset = prefs.uiPreset === "shadcn" ? "shadcn" : "gs";
      const radius = prefs.radius === "tight" || prefs.radius === "round" ? prefs.radius : "default";
      if (radius === "default") delete root.dataset.radius;
      else root.dataset.radius = radius;
      const density = prefs.density === "compact" ? "compact" : "comfortable";
      if (density === "comfortable") delete root.dataset.density;
      else root.dataset.density = density;
      const blurRaw = Number(prefs.glassBlur);
      const blur = Number.isFinite(blurRaw) ? Math.min(40, Math.max(8, blurRaw)) : 12;
      const opacityRaw = Number(prefs.cardGlassOpacity);
      const opacity = Number.isFinite(opacityRaw) ? Math.min(0.72, Math.max(0.12, opacityRaw)) : 0.25;
      const saturate = 1.08 + ((blur - 8) / 32) * 0.18;
      root.style.setProperty("--surface-blur", blur + "px");
      root.style.setProperty("--card-glass-opacity", String(opacity));
      root.style.setProperty("--shell-glass-pct", Math.round(opacity * 100) + "%");
      root.style.setProperty("--glass-saturate", saturate.toFixed(2));
    }
    try {
      window.addEventListener("storage", (e) => {
        if (!e || !e.key) return;
        if (e.key === PALLAS_CONSOLE_PREFS_KEY || e.key === PALLAS_THEME_MODE_KEY || e.key === PALLAS_THEME_KEY) {
          applyShellUiPrefsFromStorage();
          applySidebarCollapsedFromStorage();
          syncShellThemeToolbar();
          if (e.key === PALLAS_CONSOLE_PREFS_KEY || e.key === PALLAS_THEME_MODE_KEY || e.key === PALLAS_THEME_KEY) {
            applyPallasShellTheme(resolvePallasThemePreference(), { persist: false });
          }
        }
      });
    } catch (e) {}
    try {
      applyShellUiPrefsFromStorage();
    } catch (e) {}
"""


def _shell_chrome_js() -> str:
    return """
    const PROTO_SHELL_NARROW_MQ = "(max-width: 860px)";
    function isProtoShellNarrow() {
      try { return window.matchMedia(PROTO_SHELL_NARROW_MQ).matches; } catch (e) { return false; }
    }
    function openProtocolMobileNav() {
      const root = document.getElementById("protoMobileNav");
      if (!root) return;
      root.hidden = false;
      document.body.classList.add("shell-mobile-nav-open");
    }
    function closeProtocolMobileNav() {
      const root = document.getElementById("protoMobileNav");
      if (!root) return;
      root.hidden = true;
      document.body.classList.remove("shell-mobile-nav-open");
    }
    function syncShellThemeToolbar() {
      const mode = resolveThemeModeFromStorage();
      document.querySelectorAll("[data-proto-theme]").forEach((btn) => {
        const m = btn.getAttribute("data-proto-theme");
        btn.classList.toggle("is-on", m === mode);
      });
    }
    function applySidebarCollapsedFromStorage() {
      const collapsed = !!readConsolePrefsJson().sidebarCollapsed;
      document.querySelectorAll(".proto-shell").forEach((el) => {
        el.classList.toggle("shell--sidebar-collapsed", collapsed);
      });
      const btn = document.getElementById("protoSidebarCollapse");
      if (!btn) return;
      btn.setAttribute("aria-expanded", collapsed ? "false" : "true");
      btn.textContent = collapsed ? "»" : "«";
      btn.setAttribute("aria-label", collapsed ? "展开菜单栏" : "收起菜单栏");
    }
    function toggleProtocolSidebar() {
      const prefs = readConsolePrefsJson();
      writeConsolePrefsJson({ sidebarCollapsed: !prefs.sidebarCollapsed });
      applySidebarCollapsedFromStorage();
    }
    function setConsoleThemeMode(mode) {
      if (mode !== "dark" && mode !== "light" && mode !== "system") return;
      writeConsolePrefsJson({ theme: mode });
      try { localStorage.setItem(PALLAS_THEME_MODE_KEY, mode); } catch (e) {}
      applyPallasShellTheme(resolvePallasThemePreference(), { persist: false });
      syncShellThemeToolbar();
    }
    function initProtocolShellChrome() {
      applySidebarCollapsedFromStorage();
      syncShellThemeToolbar();
      const collapseBtn = document.getElementById("protoSidebarCollapse");
      if (collapseBtn && !collapseBtn.dataset.bound) {
        collapseBtn.dataset.bound = "1";
        collapseBtn.addEventListener("click", toggleProtocolSidebar);
      }
      const mobileOpenBtn = document.getElementById("protoMobileNavOpen");
      if (mobileOpenBtn && !mobileOpenBtn.dataset.bound) {
        mobileOpenBtn.dataset.bound = "1";
        mobileOpenBtn.addEventListener("click", openProtocolMobileNav);
      }
      const mobileCloseBtn = document.getElementById("protoMobileNavClose");
      if (mobileCloseBtn && !mobileCloseBtn.dataset.bound) {
        mobileCloseBtn.dataset.bound = "1";
        mobileCloseBtn.addEventListener("click", closeProtocolMobileNav);
      }
      const mobileBackdrop = document.getElementById("protoMobileNavBackdrop");
      if (mobileBackdrop && !mobileBackdrop.dataset.bound) {
        mobileBackdrop.dataset.bound = "1";
        mobileBackdrop.addEventListener("click", closeProtocolMobileNav);
      }
      document.querySelectorAll("#protoMobileNav .shell-mobile-nav__link").forEach((link) => {
        if (link.dataset.bound) return;
        link.dataset.bound = "1";
        link.addEventListener("click", () => {
          if (isProtoShellNarrow()) closeProtocolMobileNav();
        });
      });
      if (!window.__protoShellNarrowMqBound) {
        window.__protoShellNarrowMqBound = true;
        try {
          window.matchMedia(PROTO_SHELL_NARROW_MQ).addEventListener("change", () => {
            if (!isProtoShellNarrow()) closeProtocolMobileNav();
          });
        } catch (e) {}
      }
      document.querySelectorAll("[data-proto-theme]").forEach((btn) => {
        if (btn.dataset.bound) return;
        btn.dataset.bound = "1";
        btn.addEventListener("click", () => {
          setConsoleThemeMode(btn.getAttribute("data-proto-theme"));
        });
      });
    }
    try {
      document.addEventListener("DOMContentLoaded", () => {
        try { initProtocolShellChrome(); } catch (e) {}
      });
    } catch (e) {}
"""

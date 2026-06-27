# ruff: noqa: E501
"""协议端内嵌 JS 片段。"""

from __future__ import annotations

import json

from .shell_layout import _pallas_theme_bridge_js, _shell_chrome_js, _shell_prefs_js


def _render_common_api_js() -> str:
    return (
        _pallas_theme_bridge_js()
        + _shell_prefs_js()
        + _shell_chrome_js()
        + """
    function getSessionToken() {
      return (sessionStorage.getItem("pallas_protocol_token_session") || "").trim();
    }

    async function logout() {
      sessionStorage.removeItem("pallas_protocol_token_session");
      try {
        await fetch(`${basePath}/logout`, { method: "POST" });
      } finally {
        location.href = `${basePath}/login`;
      }
    }

    async function api(path, options = {}) {
      const timeoutMs = typeof options.timeoutMs === "number" ? options.timeoutMs : 35000;
      const fetchOpts = { ...options };
      delete fetchOpts.timeoutMs;
      const token = getSessionToken();
      const headers = fetchOpts.headers || {};
      if (token) headers["X-Pallas-Protocol-Token"] = token;
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort(), timeoutMs);
      try {
        const res = await fetch(`${basePath}${path}`, {
          ...fetchOpts,
          headers,
          signal: ctrl.signal,
          credentials: fetchOpts.credentials || "same-origin",
        });
        if (res.status === 401) {
          sessionStorage.removeItem("pallas_protocol_token_session");
          const loc = location.pathname + location.search + location.hash;
          const next = encodeURIComponent(loc || `${basePath}/`);
          location.href = `${basePath}/login?next=${next}&reason=${encodeURIComponent("登录已失效或 Token 无效，请重新登录")}`;
          throw new Error("Unauthorized");
        }
        if (!res.ok) throw new Error((await res.text()) || res.status);
        return res.json();
      } catch (e) {
        if (e && e.name === "AbortError") throw new Error("请求超时，请稍后重试");
        throw e;
      } finally {
        clearTimeout(timer);
      }
    }

    function setBatchProgressUi(visible, percent, message) {
      let bar = document.getElementById("protoBatchProgress");
      if (!bar) {
        bar = document.createElement("div");
        bar.id = "protoBatchProgress";
        bar.className = "proto-batch-progress";
        bar.innerHTML =
          '<div class="proto-batch-progress__track"><div class="proto-batch-progress__fill"></div></div>'
          + '<p class="proto-batch-progress__msg muted"></p>';
        const panel = document.querySelector(".proto-panel--accounts .panel__bd");
        if (panel) panel.prepend(bar);
      }
      const fill = bar.querySelector(".proto-batch-progress__fill");
      const msg = bar.querySelector(".proto-batch-progress__msg");
      bar.hidden = !visible;
      if (fill) fill.style.width = Math.min(100, Math.max(0, percent)) + "%";
      if (msg) msg.textContent = message || "";
    }

    async function waitBatchJob(jobId, options) {
      options = options || {};
      return new Promise((resolve, reject) => {
        const tok = getSessionToken();
        let url = basePath + "/api/accounts/batch/" + encodeURIComponent(jobId) + "/stream";
        if (tok) url += "?token=" + encodeURIComponent(tok);
        const es = new EventSource(url);
        let settled = false;
        const finish = (job, err) => {
          if (settled) return;
          settled = true;
          try { es.close(); } catch (e) {}
          if (err) reject(err);
          else resolve(job);
        };
        const apply = (job) => {
          if (!job) return;
          const pct = job.total ? Math.round((job.completed || 0) * 100 / job.total) : 0;
          const parts = [job.message, job.phase, job.current_account_id].filter(Boolean);
          setBatchProgressUi(true, pct, parts.join(" · "));
          if (typeof options.onProgress === "function") options.onProgress(job);
          if (job.status && job.status !== "running") finish(job);
        };
        es.addEventListener("snapshot", (ev) => {
          try { apply(JSON.parse(ev.data)); } catch (e) {}
        });
        es.addEventListener("progress", (ev) => {
          try { apply(JSON.parse(ev.data)); } catch (e) {}
        });
        es.onerror = () => {
          api("/api/accounts/batch/" + encodeURIComponent(jobId), { timeoutMs: 15000 })
            .then((data) => finish(data.job))
            .catch((e) => finish(null, e));
        };
      });
    }

    async function runAccountBatch(action, accountIds, options) {
      options = options || {};
      const body = { action: action, mode: options.mode || "rolling" };
      if (Array.isArray(accountIds) && accountIds.length) body.account_ids = accountIds;
      if (options.max_concurrency != null) body.max_concurrency = options.max_concurrency;
      if (options.stagger_ms != null) body.stagger_ms = options.stagger_ms;
      setBatchProgressUi(true, 0, "已提交批量任务…");
      const data = await api("/api/accounts/batch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
        timeoutMs: 60000,
      });
      const jobId = data && data.job_id;
      if (!jobId) throw new Error("批量任务未返回 job_id");
      const job = await waitBatchJob(jobId, options);
      setBatchProgressUi(false, 100, "");
      return job;
    }

    document.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-action='logout']");
      if (!btn) return;
      e.preventDefault();
      logout();
    });

    function isLogElementUserSelecting(el) {
      if (!el) return false;
      const sel = window.getSelection();
      if (!sel || sel.rangeCount === 0) return false;
      if (sel.isCollapsed) return false;
      try {
        const r = sel.getRangeAt(0);
        return el.contains(r.commonAncestorContainer);
      } catch (e) {
        return false;
      }
    }

    function shouldPauseLiveLogDomWrite(el) {
      if (!el) return false;
      if (isLogElementUserSelecting(el)) return true;
      if (el.id === "accLogs") return false;
      try {
        if (typeof el.matches === "function" && el.matches(":focus-within")) return true;
      } catch (e) { }
      return false;
    }

    let protoMainScrollActive = false;
    let protoMainScrollTimer = null;
    const protoScrollEndHooks = [];
    function isProtoMainInnerScrolling() {
      return protoMainScrollActive;
    }
    function onProtoMainInnerScrollEnd(fn) {
      if (typeof fn === "function") protoScrollEndHooks.push(fn);
    }
    function wireProtoMainInnerScrollPause() {
      const el = document.querySelector(".proto-shell__main-inner");
      if (!el || el.dataset.protoScrollBound) return;
      el.dataset.protoScrollBound = "1";
      el.addEventListener("scroll", () => {
        protoMainScrollActive = true;
        clearTimeout(protoMainScrollTimer);
        protoMainScrollTimer = setTimeout(() => {
          protoMainScrollActive = false;
          protoScrollEndHooks.forEach((hook) => {
            try { hook(); } catch (e) {}
          });
        }, 400);
      }, { passive: true });
    }
    try {
      document.addEventListener("DOMContentLoaded", wireProtoMainInnerScrollPause);
    } catch (e) {}
    try { wireProtoMainInnerScrollPause(); } catch (e) {}

    function copyPlainStrToast(msg, level) {
      if (typeof notify === "function") notify(msg, level);
      else alert(msg);
    }

    function copyPlainStr(t) {
      const x = String(t ?? "");
      if (!x) {
        copyPlainStrToast("无可复制内容", "warn");
        return;
      }
      const ok = () => copyPlainStrToast("已复制", "ok");
      const fail = (e) => copyPlainStrToast(String(e && e.message ? e.message : e), "err");
      const runFallback = () => {
        try {
          const ta = document.createElement("textarea");
          ta.value = x;
          ta.style.position = "fixed";
          ta.style.left = "-9999px";
          ta.setAttribute("readonly", "");
          document.body.appendChild(ta);
          ta.select();
          ta.setSelectionRange(0, x.length);
          const done = document.execCommand("copy");
          document.body.removeChild(ta);
          if (done) ok();
          else fail(new Error("浏览器拒绝了复制"));
        } catch (err) {
          fail(err);
        }
      };
      if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(x).then(ok).catch(() => runFallback());
      } else {
        runFallback();
      }
    }

    document.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-copy-plain]");
      if (!btn) return;
      e.preventDefault();
      const raw = btn.getAttribute("data-copy-plain");
      copyPlainStr(raw != null ? decodeURIComponent(raw) : "");
    });

    function shellPrettySyncSelect(sel) {
      const wrap = sel && sel.closest ? sel.closest(".shell-pretty-wrap") : null;
      if (wrap && typeof wrap._shellPrettyRebuild === "function") wrap._shellPrettyRebuild();
    }

    function wireShellPrettySelect(sel) {
      if (!sel || sel.multiple || sel.dataset.shellPrettyWired) return;
      sel.dataset.shellPrettyWired = "1";
      sel.classList.remove("shell-pretty-select");
      const wrap = document.createElement("div");
      wrap.className = "shell-pretty-wrap";
      sel.parentNode.insertBefore(wrap, sel);
      wrap.appendChild(sel);
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "shell-pretty-btn";
      btn.setAttribute("aria-haspopup", "listbox");
      const panel = document.createElement("div");
      panel.className = "shell-pretty-panel";
      panel.setAttribute("role", "listbox");
      wrap.insertBefore(btn, sel);
      wrap.insertBefore(panel, sel);
      sel.classList.add("shell-pretty-native");
      function syncDisabled() {
        btn.disabled = !!sel.disabled;
      }
      function rebuild() {
        panel.innerHTML = "";
        Array.from(sel.options).forEach((opt, idx) => {
          const row = document.createElement("button");
          row.type = "button";
          row.className = "shell-pretty-option" + (idx === sel.selectedIndex ? " is-active" : "");
          row.textContent = opt.textContent;
          row.addEventListener("click", (ev) => {
            ev.preventDefault();
            ev.stopPropagation();
            sel.selectedIndex = idx;
            sel.dispatchEvent(new Event("change", { bubbles: true }));
            panel.classList.remove("is-open");
            wrap.classList.remove("shell-pretty-wrap--open");
            syncBtn();
            rebuild();
          });
          panel.appendChild(row);
        });
      }
      function syncBtn() {
        const opt = sel.options[sel.selectedIndex];
        btn.textContent = opt ? opt.textContent : "";
      }
      wrap._shellPrettyRebuild = function () {
        syncBtn();
        rebuild();
        syncDisabled();
      };
      btn.addEventListener("click", (ev) => {
        ev.preventDefault();
        ev.stopPropagation();
        if (sel.disabled) return;
        const willOpen = !panel.classList.contains("is-open");
        document.querySelectorAll(".shell-pretty-panel.is-open").forEach((p) => {
          p.classList.remove("is-open");
          const ow = p.closest(".shell-pretty-wrap");
          if (ow) ow.classList.remove("shell-pretty-wrap--open");
        });
        if (willOpen) {
          panel.classList.add("is-open");
          wrap.classList.add("shell-pretty-wrap--open");
        }
      });
      sel.addEventListener("change", () => {
        syncBtn();
        rebuild();
      });
      new MutationObserver(() => {
        syncBtn();
        rebuild();
      }).observe(sel, { childList: true });
      new MutationObserver(syncDisabled).observe(sel, { attributes: true, attributeFilter: ["disabled"] });
      syncBtn();
      rebuild();
      syncDisabled();
    }

    function initShellPrettySelects(root) {
      const scope = root || document;
      scope.querySelectorAll("select.shell-pretty-select").forEach(wireShellPrettySelect);
    }

    document.addEventListener("click", (e) => {
      if (e.target.closest && e.target.closest(".shell-pretty-wrap")) return;
      document.querySelectorAll(".shell-pretty-panel.is-open").forEach((p) => {
        p.classList.remove("is-open");
        const w = p.closest(".shell-pretty-wrap");
        if (w) w.classList.remove("shell-pretty-wrap--open");
      });
    });
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        document.querySelectorAll(".shell-pretty-panel.is-open").forEach((p) => {
          p.classList.remove("is-open");
          const w = p.closest(".shell-pretty-wrap");
          if (w) w.classList.remove("shell-pretty-wrap--open");
        });
      }
    });
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", () => initShellPrettySelects());
    } else {
      initShellPrettySelects();
    }
"""
    )


def _render_hidden_token_sync_js(
    back_button_id: str = "backDash", *, page_session: str = ""
) -> str:
    back_id_js = json.dumps(back_button_id)
    page_sess_js = json.dumps(page_session)
    return f"""
    (function initTokenSync() {{
      const u = new URL(location.href);
      const fromQs = (u.searchParams.get("token") || "").trim();
      const fromBootstrap = ({page_sess_js} || "").trim();
      const fromSession = (sessionStorage.getItem("pallas_protocol_token_session") || "").trim();
      const t = fromQs || fromBootstrap || fromSession;
      if (t) sessionStorage.setItem("pallas_protocol_token_session", t);
      const tokenEl = document.getElementById("token");
      if (tokenEl) tokenEl.value = t;
      const b = document.getElementById({back_id_js});
      if (b) b.href = basePath;
    }})();
"""

"""HTTP 路由注册：与 ``PallasProtocolService`` 通过参数注入耦合，便于测试与替换 UI。"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Any
from urllib.parse import quote, urlparse, urlunparse

import httpx
from fastapi import FastAPI, Form, Header, HTTPException, Query, Request
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    RedirectResponse,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from ..config import Config
    from ..service import PallasProtocolService


def register_pallas_protocol_routes(
    app: FastAPI,
    *,
    manager: PallasProtocolService,
    plugin_config: Config,
) -> None:
    from ..config import resolve_protocol_webui_base_path
    from .pages import (
        shell_font_stylesheet_link,
    )

    base = resolve_protocol_webui_base_path(plugin_config)
    page_cookie_name = "pallas_protocol_page_token"

    def _pallas_console_http_base() -> str:
        try:
            from packages.pb_webui.config import get_pallas_webui_config

            raw = (get_pallas_webui_config().pallas_webui_http_base or "").strip()
        except Exception:
            raw = ""
        if not raw:
            raw = "/pallas"
        if not raw.startswith("/"):
            raw = "/" + raw
        return raw.rstrip("/") or "/pallas"

    def _redirect_to_console_protocol(
        subpath: str = "",
        *,
        query: str = "",
    ) -> RedirectResponse:
        """协议独立 HTML 页已并入 Bot WebUI，旧书签重定向到 ``/pallas/protocol``。"""
        console_base = _pallas_console_http_base()
        dest = f"{console_base}/protocol"
        sub = (subpath or "").strip()
        if sub:
            dest += sub if sub.startswith("/") else f"/{sub}"
        q = (query or "").strip().lstrip("?")
        if q:
            dest = f"{dest}?{q}"
        return RedirectResponse(url=dest, status_code=307)

    from pallas.console.webui.console_login import (
        install_pallas_http_request_context_middleware,
    )

    install_pallas_http_request_context_middleware(app)

    b_norm = base.rstrip("/")
    if b_norm != "/protocol/napcat":

        def _redirect_protocol_napcat_bookmark(
            request: Request, rest: str
        ) -> RedirectResponse:
            """旧默认 ``/protocol/napcat`` 书签 → 当前协议管理基路径。"""
            parsed = urlparse(str(request.url))
            suffix = ("/" + rest.lstrip("/")) if (rest or "").strip() else "/"
            new_path = b_norm + suffix
            dest = urlunparse(
                (
                    parsed.scheme,
                    parsed.netloc,
                    new_path,
                    "",
                    parsed.query,
                    parsed.fragment,
                )
            )
            return RedirectResponse(url=dest, status_code=307)

        @app.get("/protocol/napcat")
        async def _legacy_protocol_napcat_root(request: Request) -> RedirectResponse:
            return _redirect_protocol_napcat_bookmark(request, "")

        @app.get("/protocol/napcat/{rest:path}")
        async def _legacy_protocol_napcat_subpath(
            request: Request, rest: str
        ) -> RedirectResponse:
            return _redirect_protocol_napcat_bookmark(request, rest)

    def _auth(
        h: str | None,
        q: str | None,
        c: str | None = None,
        *,
        request: Request | None = None,
    ) -> None:
        from pallas.console.webui.console_login import (
            current_http_request,
            extract_session_from_request,
            is_console_auth_configured,
        )

        _ = plugin_config
        req = request if request is not None else current_http_request()
        if req is None:
            raise HTTPException(status_code=500, detail="协议端鉴权缺少请求上下文")
        cookies = dict(req.cookies)
        legacy = req.cookies.get(page_cookie_name)
        if extract_session_from_request(
            cookies=cookies,
            header_token=h,
            query_token=q,
            cookie_token=(c or legacy),
        ):
            return
        if not is_console_auth_configured():
            raise HTTPException(
                status_code=503,
                detail="统一控制台鉴权未初始化，请检查 data/pallas_console/",
            )
        raise HTTPException(status_code=401, detail="未登录或会话已失效，请重新登录")

    def _ensure_page_auth(
        *,
        request: Request,
        token: str | None,
        x_pallas_protocol_token: str | None,
        next_path: str,
    ) -> RedirectResponse | None:
        try:
            cookie_token = request.cookies.get(page_cookie_name)
            _auth(x_pallas_protocol_token, token, cookie_token, request=request)
            return None
        except HTTPException as e:
            encoded_next = quote(next_path, safe="/?=&-_.~")
            detail = str(getattr(e, "detail", "") or "鉴权失败")
            if detail.startswith("未提供"):
                return RedirectResponse(
                    url=f"{base}/login?next={encoded_next}", status_code=307
                )
            reason = quote(detail, safe="")
            return RedirectResponse(
                url=f"{base}/login?next={encoded_next}&reason={reason}", status_code=307
            )

    def _resolve_login_target(next_path: str | None) -> str:
        target = (next_path or f"{base}/").strip() or f"{base}/"
        if not target.startswith(base):
            target = f"{base}/"
        return target

    def _render_login_page(*, target: str, err: str, detail: str) -> HTMLResponse:
        from pallas.console.webui.login_page import render_pallas_login_page_html

        head = shell_font_stylesheet_link(base)
        footer_note = (detail or "").strip()
        html = render_pallas_login_page_html(
            document_title="登录 · 协议端",
            surface_label="协议端",
            tagline="与 Web 控制台（/pallas）共用登录口令。",
            form_action=f"{base}/login",
            next_path=target,
            error_message=(err or "").strip(),
            head_extra_html=head,
            footer_note=footer_note,
            favicon_variant="protocol",
            shell_brand_icon_base=base,
        )
        return HTMLResponse(html)

    @app.get(f"{base}/login", response_class=HTMLResponse, response_model=None)
    async def napcat_login_page(
        next_path: str | None = Query(default=None, alias="next"),
        reason: str | None = Query(default=None),
    ):
        target = _resolve_login_target(next_path)
        err = ""
        default_reason = (reason or "").strip()
        if default_reason:
            err = default_reason
        detail = ""
        return _render_login_page(target=target, err=err, detail=detail)

    @app.post(f"{base}/login", response_class=HTMLResponse, response_model=None)
    async def napcat_login_submit(
        request: Request,
        next_path: str | None = Form(default=None, alias="next"),
        token: str = Form(...),
    ) -> RedirectResponse | HTMLResponse:
        target = _resolve_login_target(next_path)
        detail = ""
        from pallas.console.webui.console_login import (
            SESSION_COOKIE_NAME,
            SESSION_TTL_SEC,
            mint_session_token,
            verify_console_password,
        )

        if not verify_console_password(token):
            return _render_login_page(
                target=target,
                err="口令不正确",
                detail=detail,
            )
        sess = mint_session_token()
        response = RedirectResponse(url=target, status_code=303)
        response.set_cookie(
            key=SESSION_COOKIE_NAME,
            value=sess,
            max_age=SESSION_TTL_SEC,
            httponly=True,
            samesite="lax",
            secure=request.url.scheme == "https",
            path="/",
        )
        response.delete_cookie(key=page_cookie_name, path=base or "/")
        return response

    @app.post(f"{base}/logout", response_model=None)
    async def napcat_logout(request: Request) -> RedirectResponse:  # noqa: ARG001
        from pallas.console.webui.console_login import SESSION_COOKIE_NAME

        response = RedirectResponse(url=f"{base}/login", status_code=303)
        response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
        response.delete_cookie(key=page_cookie_name, path=base or "/")
        return response

    class _ChangeConsoleLoginBody(BaseModel):
        model_config = ConfigDict(extra="forbid")

        new_password: str = Field(min_length=1, max_length=256)

    @app.post(f"{base}/api/security/console-login")
    async def protocol_change_console_login(
        body: _ChangeConsoleLoginBody,
        request: Request,
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ) -> JSONResponse:
        cookie_token = request.cookies.get(page_cookie_name)
        _auth(x_pallas_protocol_token, token, cookie_token, request=request)
        from pallas.console.webui.console_login import set_shared_console_login_token

        try:
            set_shared_console_login_token(body.new_password)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        return JSONResponse({"ok": True})

    @app.get(base, response_class=HTMLResponse)
    @app.get(f"{base}/", response_class=HTMLResponse)
    async def napcat_dashboard(
        request: Request,
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        if not plugin_config.pallas_protocol_webui_enabled:
            raise HTTPException(status_code=404, detail="Pallas-Bot 协议端管理页已关闭")
        redirect = _ensure_page_auth(
            request=request,
            token=token,
            x_pallas_protocol_token=x_pallas_protocol_token,
            next_path=str(request.url.path),
        )
        if redirect is not None:
            return redirect
        return _redirect_to_console_protocol()

    @app.get(f"{base}/settings", response_class=HTMLResponse)
    async def napcat_settings_page(
        request: Request,
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        if not plugin_config.pallas_protocol_webui_enabled:
            raise HTTPException(status_code=404, detail="Pallas-Bot 协议端管理页已关闭")
        redirect = _ensure_page_auth(
            request=request,
            token=token,
            x_pallas_protocol_token=x_pallas_protocol_token,
            next_path=str(request.url.path),
        )
        if redirect is not None:
            return redirect
        return RedirectResponse(
            url=f"{_pallas_console_http_base()}/preferences",
            status_code=307,
        )

    @app.get(f"{base}/new", response_class=HTMLResponse)
    async def napcat_new_account(
        request: Request,
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        if not plugin_config.pallas_protocol_webui_enabled:
            raise HTTPException(status_code=404, detail="Pallas-Bot 协议端管理页已关闭")
        redirect = _ensure_page_auth(
            request=request,
            token=token,
            x_pallas_protocol_token=x_pallas_protocol_token,
            next_path=str(request.url.path),
        )
        if redirect is not None:
            return redirect
        return _redirect_to_console_protocol("/create")

    @app.get(f"{base}/import", response_class=HTMLResponse)
    async def napcat_import_page(
        request: Request,
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        if not plugin_config.pallas_protocol_webui_enabled:
            raise HTTPException(status_code=404, detail="Pallas-Bot 协议端管理页已关闭")
        redirect = _ensure_page_auth(
            request=request,
            token=token,
            x_pallas_protocol_token=x_pallas_protocol_token,
            next_path=str(request.url.path),
        )
        if redirect is not None:
            return redirect
        return _redirect_to_console_protocol("/import")

    @app.post(f"{base}/api/accounts/import")
    async def import_accounts(
        payload: dict[str, Any],
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        import asyncio
        from pathlib import Path

        from ..importer import run_import

        source_dir = Path(str(payload.get("source_dir", "")).strip())
        if not await asyncio.to_thread(source_dir.is_dir):
            raise HTTPException(status_code=400, detail=f"目录不存在: {source_dir}")
        dry_run = bool(payload.get("dry_run", False))
        skip_existing = bool(payload.get("skip_existing", True))
        ws_url = str(payload.get("ws_url", "") or "").strip()
        ws_token = str(payload.get("ws_token", "") or "")
        ws_name = str(payload.get("ws_name", "") or "pallas").strip() or "pallas"

        existing = {acc["id"]: acc for acc in manager.list_accounts()}
        result, new_accounts = run_import(
            source_dir,
            existing,
            dry_run=dry_run,
            skip_existing=skip_existing,
            ws_url=ws_url,
            ws_name=ws_name,
            ws_token=ws_token,
            instances_root=manager._instances_root,
        )
        if not dry_run and result.imported:
            manager.bulk_register(new_accounts)
        return {
            "imported": result.imported,
            "skipped": result.skipped,
            "failed": result.failed,
        }

    def _redirect_legacy_runtime_path(request: Request) -> RedirectResponse:
        _ = request
        return _redirect_to_console_protocol("/assets")

    @app.get(f"{base}/assets", response_class=HTMLResponse)
    async def protocol_assets_page(
        request: Request,
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        if not plugin_config.pallas_protocol_webui_enabled:
            raise HTTPException(status_code=404, detail="Pallas-Bot 协议端管理页已关闭")
        redirect = _ensure_page_auth(
            request=request,
            token=token,
            x_pallas_protocol_token=x_pallas_protocol_token,
            next_path=str(request.url.path),
        )
        if redirect is not None:
            return redirect
        return _redirect_to_console_protocol("/assets")

    @app.get(f"{base}/runtime")
    async def legacy_runtime_page_redirect(request: Request):
        """旧书签 ``…/runtime`` → ``…/assets``。"""
        return _redirect_legacy_runtime_path(request)

    @app.get(f"{base}/account/{{account_id}}/edit")
    async def napcat_edit_redirect(
        account_id: str,
        request: Request,
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        """旧书签 ``…/edit`` → 账号子路径设置页。"""
        if not plugin_config.pallas_protocol_webui_enabled:
            raise HTTPException(status_code=404, detail="Pallas-Bot 协议端管理页已关闭")
        redirect = _ensure_page_auth(
            request=request,
            token=token,
            x_pallas_protocol_token=x_pallas_protocol_token,
            next_path=str(request.url.path),
        )
        if redirect is not None:
            return redirect
        if not manager.has_account(account_id):
            raise HTTPException(status_code=404, detail="账号不存在")
        aid = quote(str(account_id), safe="")
        return _redirect_to_console_protocol(f"/account/{aid}", query="tab=settings")

    @app.get(f"{base}/account/{{account_id}}", response_class=HTMLResponse)
    async def napcat_account_workspace(
        account_id: str,
        request: Request,
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        if not plugin_config.pallas_protocol_webui_enabled:
            raise HTTPException(status_code=404, detail="Pallas-Bot 协议端管理页已关闭")
        redirect = _ensure_page_auth(
            request=request,
            token=token,
            x_pallas_protocol_token=x_pallas_protocol_token,
            next_path=str(request.url.path),
        )
        if redirect is not None:
            return redirect
        if not manager.has_account(account_id):
            raise HTTPException(status_code=404, detail="账号不存在")
        aid = quote(str(account_id), safe="")
        return _redirect_to_console_protocol(
            f"/account/{aid}",
            query=str(request.url.query or ""),
        )

    @app.get(f"{base}/api/runtime")
    async def runtime_status(
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        return manager.runtime_overview()

    @app.get(f"{base}/api/connection-hints")
    async def connection_hints(
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        return manager.connection_hints()

    @app.get(f"{base}/api/nonebot-logs")
    async def nonebot_log_tail(
        request: Request,
        lines: int = Query(default=400, ge=1, le=2000),
        scope: str = Query(default="all"),
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        cookie_token = request.cookies.get(page_cookie_name)
        _auth(x_pallas_protocol_token, token, cookie_token, request=request)
        from pallas.console.web import install_nonebot_log_sink

        install_nonebot_log_sink()

        sc = scope if scope in ("all", "webui", "protocol") else "all"

        def _load() -> dict[str, object]:
            from pallas.console.web import (
                tail_nonebot_log_entries_scoped,
                tail_nonebot_log_lines_scoped,
            )
            from pallas.api.platform import is_sharded_hub

            cap = min(lines, 220) if is_sharded_hub() else lines
            return {
                "logs": tail_nonebot_log_lines_scoped(cap, sc),
                "entries": tail_nonebot_log_entries_scoped(cap, sc),
                "scope": sc,
            }

        return await asyncio.to_thread(_load)

    @app.get(f"{base}/api/nonebot-logs/stream")
    async def nonebot_logs_stream(
        request: Request,
        scope: str = Query(default="all"),
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        cookie_token = request.cookies.get(page_cookie_name)
        _auth(x_pallas_protocol_token, token, cookie_token, request=request)
        from pallas.console.web import install_nonebot_log_sink, iter_nonebot_log_sse

        install_nonebot_log_sink()
        sc = scope if scope in ("all", "webui", "protocol") else "all"
        return StreamingResponse(
            iter_nonebot_log_sse(sc),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @app.post(f"{base}/api/runtime/download")
    async def runtime_download(
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
        tag: str | None = Query(default=None),
        target_platform: str | None = Query(default=None),
        runtime_mode: str | None = Query(default=None),
    ):
        _auth(x_pallas_protocol_token, token)
        try:
            return manager.start_runtime_download(
                tag=tag or None,
                target_platform=target_platform or None,
                runtime_mode=runtime_mode or None,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        except RuntimeError as e:
            raise HTTPException(status_code=409, detail=str(e)) from e

    @app.get(f"{base}/api/runtime/profile")
    async def runtime_profile(
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        return {"profile": manager.runtime_profile()}

    @app.put(f"{base}/api/runtime/profile")
    async def update_runtime_profile(
        payload: dict[str, Any],
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        try:
            return {"profile": await manager.update_runtime_profile(payload)}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    @app.post(f"{base}/api/runtime/docker/pull")
    async def runtime_docker_pull(
        payload: dict[str, Any] | None = None,
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        image = ""
        if isinstance(payload, dict):
            image = str(payload.get("image", "") or "").strip()
        return await manager.pull_docker_image(image or None)

    @app.get(f"{base}/api/runtime/docker/images")
    async def runtime_docker_images(
        protocol: str | None = Query(
            default=None,
            description="napcat / snowluma：仅列出当前全局配置对应仓库的本地镜像；不传则列出全部。",
        ),
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        p = str(protocol or "").strip().lower()
        if p and p not in ("napcat", "snowluma"):
            raise HTTPException(
                status_code=400, detail="protocol 仅支持 napcat、snowluma 或省略"
            )
        return await manager.list_local_docker_images(protocol=p or None)

    @app.post(f"{base}/api/runtime/docker/stop-all")
    async def runtime_docker_stop_all(
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        return await manager.stop_all_labeled_docker_containers()

    @app.post(f"{base}/api/runtime/docker/prune-stopped")
    async def runtime_docker_prune_stopped(
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        return await manager.prune_stopped_labeled_docker_containers()

    @app.get(f"{base}/api/runtime/releases")
    async def runtime_releases(
        limit: int = Query(default=10, ge=1, le=200),
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        releases = await manager.fetch_runtime_releases(limit=limit)
        return {"releases": releases}

    @app.post(f"{base}/api/runtime/rescan")
    async def runtime_rescan(
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        return manager.rescan_runtime_extract()

    @app.post(f"{base}/api/runtime/cleanup-dist")
    async def runtime_cleanup_dist(
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        return manager.cleanup_runtime_dist_caches()

    @app.get(f"{base}/api/runtime/local-inventory")
    async def runtime_local_inventory(
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        return manager.napcat_local_inventory()

    @app.post(f"{base}/api/runtime/activate-extract")
    async def runtime_activate_extract(
        payload: dict[str, Any] | None = None,
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        body = payload if isinstance(payload, dict) else {}
        folder = str(body.get("folder", "") or "").strip()
        if not folder:
            raise HTTPException(status_code=400, detail="缺少 folder")
        try:
            return manager.activate_napcat_extract(folder)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    @app.post(f"{base}/api/runtime/activate-tag")
    async def runtime_activate_tag(
        payload: dict[str, Any] | None = None,
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        body = payload if isinstance(payload, dict) else {}
        tag = str(body.get("tag", "") or "").strip()
        if not tag:
            raise HTTPException(status_code=400, detail="缺少 tag")
        try:
            return manager.activate_napcat_by_tag(tag)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    @app.get(f"{base}/api/snowluma/runtime/overview")
    async def snowluma_runtime_overview(
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        return manager.snowluma_runtime_overview()

    @app.post(f"{base}/api/snowluma/runtime/download")
    async def snowluma_runtime_download(
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
        tag: str | None = Query(default=None),
        target_platform: str | None = Query(default=None),
    ):
        _auth(x_pallas_protocol_token, token)
        try:
            return manager.start_snowluma_runtime_download(
                tag=tag or None, target_platform=target_platform
            )
        except RuntimeError as e:
            raise HTTPException(status_code=409, detail=str(e)) from e

    @app.get(f"{base}/api/snowluma/runtime/releases")
    async def snowluma_runtime_releases(
        limit: int = Query(default=10, ge=1, le=200),
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        releases = await manager.fetch_snowluma_runtime_releases(limit=limit)
        return {"releases": releases}

    @app.get(f"{base}/api/snowluma/runtime/local-inventory")
    async def snowluma_runtime_local_inventory(
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        return manager.snowluma_local_inventory()

    @app.post(f"{base}/api/snowluma/runtime/activate-extract")
    async def snowluma_runtime_activate_extract(
        payload: dict[str, Any] | None = None,
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        body = payload if isinstance(payload, dict) else {}
        folder = str(body.get("folder", "") or "").strip()
        if not folder:
            raise HTTPException(status_code=400, detail="缺少 folder")
        try:
            return manager.activate_snowluma_extract(folder)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    @app.post(f"{base}/api/snowluma/runtime/activate-tag")
    async def snowluma_runtime_activate_tag(
        payload: dict[str, Any] | None = None,
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        body = payload if isinstance(payload, dict) else {}
        tag = str(body.get("tag", "") or "").strip()
        if not tag:
            raise HTTPException(status_code=400, detail="缺少 tag")
        try:
            return manager.activate_snowluma_by_tag(tag)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    @app.get(f"{base}/api/accounts")
    async def list_accounts(
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        accounts = await asyncio.to_thread(manager.list_accounts)
        return {"accounts": accounts}

    @app.get(f"{base}/api/accounts/{{account_id}}")
    async def get_one_account(
        account_id: str,
        brief: bool = Query(
            default=False, description="列表/轮询用：跳过 SnowLuma 日志口令解析等重操作"
        ),
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        acc = await asyncio.to_thread(manager.get_account, account_id, brief=brief)
        if acc is None:
            raise HTTPException(status_code=404, detail="账号不存在")
        return {"account": acc}

    @app.post(f"{base}/api/accounts")
    async def create_account(
        payload: dict[str, Any],
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        try:
            account = manager.create_account(payload)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        return {"account": account}

    @app.put(f"{base}/api/accounts/{{account_id}}")
    async def update_account(
        account_id: str,
        payload: dict[str, Any],
        restart: bool = Query(default=True),
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        try:
            result = await manager.update_account(account_id, payload, restart=restart)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        except (RuntimeError, ValueError) as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        return result

    @app.delete(f"{base}/api/accounts/{{account_id}}")
    async def delete_account(
        account_id: str,
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        try:
            await manager.delete_account(account_id)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        return {"ok": True}

    @app.post(f"{base}/api/accounts/{{account_id}}/start")
    async def start_account(
        account_id: str,
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        try:
            account = await manager.start_account(account_id)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        return {"account": account}

    @app.post(f"{base}/api/accounts/{{account_id}}/stop")
    async def stop_account(
        account_id: str,
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        account = await manager.stop_account(account_id)
        if account is None:
            raise HTTPException(status_code=404, detail="账号不存在")
        return {"account": account}

    @app.post(f"{base}/api/accounts/{{account_id}}/restart")
    async def restart_account(
        account_id: str,
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        try:
            account = await manager.restart_account(account_id)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        return {"account": account}

    @app.post(f"{base}/api/accounts/batch")
    async def accounts_batch(
        payload: dict[str, Any],
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        body = payload if isinstance(payload, dict) else {}
        action = str(body.get("action", "") or "").strip().lower()
        raw_ids = body.get("account_ids")
        ids: list[str] | None = None
        if isinstance(raw_ids, list):
            ids = [str(x) for x in raw_ids]
        mode = body.get("mode")
        max_concurrency = body.get("max_concurrency")
        stagger_ms = body.get("stagger_ms")
        try:
            job_id = await manager.start_account_batch(
                action,
                ids,
                mode=str(mode).strip().lower() if mode is not None else None,
                max_concurrency=int(max_concurrency)
                if max_concurrency is not None
                else None,
                stagger_ms=int(stagger_ms) if stagger_ms is not None else None,
            )
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        job = manager.batch_coordinator().job_to_dict(job_id)
        return {"ok": True, "job_id": job_id, "job": job}

    @app.post(f"{base}/api/accounts/migrate-to-snowluma")
    async def migrate_accounts_to_snowluma(
        payload: dict[str, Any],
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        body = payload if isinstance(payload, dict) else {}
        raw_ids = body.get("account_ids")
        ids: list[str] | None = None
        if isinstance(raw_ids, list):
            ids = [str(x) for x in raw_ids]
        preserve = bool(body.get("preserve_napcat_data", False))
        stop_nc = bool(body.get("stop_napcat_containers", True))
        start_after = bool(body.get("start_after", False))
        stagger_ms = body.get("stagger_ms")
        max_concurrency = body.get("max_concurrency")
        try:
            result = await manager.migrate_accounts_to_snowluma(
                ids,
                preserve_napcat_data=preserve,
                stop_napcat_containers=stop_nc,
                start_after=start_after,
                stagger_ms=int(stagger_ms) if stagger_ms is not None else None,
                max_concurrency=int(max_concurrency)
                if max_concurrency is not None
                else None,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        return {"ok": True, **result}

    @app.get(f"{base}/api/snowluma/host-deps")
    async def snowluma_host_deps(
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        from ..snowluma_host_deps import host_deps_report

        return host_deps_report()

    @app.get(f"{base}/api/accounts/batch/{{job_id}}")
    async def accounts_batch_status(
        job_id: str,
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        job = manager.batch_coordinator().job_to_dict(job_id)
        if job is None:
            raise HTTPException(status_code=404, detail="批量任务不存在")
        return {"job": job}

    @app.get(f"{base}/api/accounts/batch/{{job_id}}/stream")
    async def accounts_batch_stream(
        job_id: str,
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        if manager.batch_coordinator().get_job(job_id) is None:
            raise HTTPException(status_code=404, detail="批量任务不存在")

        async def _iter():
            async for chunk in manager.batch_coordinator().subscribe_sse(job_id):
                yield chunk

        return StreamingResponse(
            _iter(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @app.post(f"{base}/api/accounts/{{account_id}}/snowluma/inject-hook")
    async def snowluma_inject_hook(
        account_id: str,
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        try:
            return await manager.snowluma_inject_hook_via_webui(account_id)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=502, detail=f"连接 SnowLuma WebUI 失败: {e}"
            ) from e

    @app.get(f"{base}/api/accounts/{{account_id}}/logs")
    async def account_logs(
        account_id: str,
        lines: int = Query(default=200, ge=1, le=2000),
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        if not manager.has_account(account_id):
            raise HTTPException(status_code=404, detail="账号不存在")
        try:
            await asyncio.wait_for(
                manager.ensure_docker_logs_if_needed(account_id), timeout=2.5
            )
        except TimeoutError:
            pass
        logs = await asyncio.to_thread(manager.tail_logs, account_id, lines)
        return {"logs": logs}

    @app.get(f"{base}/api/accounts/{{account_id}}/qrcode/meta")
    async def account_qrcode_meta(
        account_id: str,
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        if not manager.has_account(account_id):
            raise HTTPException(status_code=404, detail="账号不存在")
        return await asyncio.to_thread(manager.account_qrcode_meta, account_id)

    @app.post(f"{base}/api/accounts/{{account_id}}/qrcode/refresh")
    async def refresh_account_qrcode(
        account_id: str,
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        if not manager.has_account(account_id):
            raise HTTPException(status_code=404, detail="账号不存在")
        try:
            return await manager.refresh_account_qrcode(account_id)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    @app.get(f"{base}/api/accounts/{{account_id}}/qrcode")
    async def account_qrcode_image(
        account_id: str,
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        if not manager.has_account(account_id):
            raise HTTPException(status_code=404, detail="账号不存在")
        path = await asyncio.to_thread(manager.account_qrcode_path, account_id)
        if path is None:
            raise HTTPException(status_code=404, detail="暂无二维码文件")
        return FileResponse(
            path, media_type="image/png", filename=f"{account_id}-qrcode.png"
        )

    @app.get(f"{base}/api/accounts/{{account_id}}/configs")
    async def get_account_configs(
        account_id: str,
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        try:
            return manager.get_account_configs(account_id)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e

    @app.put(f"{base}/api/accounts/{{account_id}}/configs")
    async def update_account_configs(
        account_id: str,
        payload: dict[str, Any],
        restart: bool = Query(default=True),
        token: str | None = Query(default=None),
        x_pallas_protocol_token: str | None = Header(
            default=None, alias="X-Pallas-Protocol-Token"
        ),
    ):
        _auth(x_pallas_protocol_token, token)
        try:
            return await manager.update_account_configs(
                account_id, payload, restart=restart
            )
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e)) from e
        except RuntimeError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    _pallas_ui_static = Path(__file__).resolve().parent / "static" / "pallas_ui"
    if _pallas_ui_static.is_dir():
        app.mount(
            f"{b_norm}/_pallas_ui",
            StaticFiles(directory=str(_pallas_ui_static)),
            name="pallas_protocol_shell_ui",
        )

from types import SimpleNamespace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread

import nonebot
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.routing import WebSocketRoute

nonebot.init()

from pallas_plugin_protocol.web.routes import register_pallas_protocol_routes  # noqa: E402


class DummyManager:
    pass


class _UpstreamHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        body = f"upstream:{self.path}".encode()
        self.send_response(200)
        self.send_header("content-type", "text/plain")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, _format: str, *args) -> None:
        _ = args


class ProxyManager:
    def __init__(self, port: int) -> None:
        self.port = port

    def get_account(self, account_id: str, *, brief: bool = False) -> dict | None:
        _ = brief
        if account_id != "napcat-1":
            return None
        return {
            "protocol_backend": "napcat",
            "webui_port": self.port,
            "running": True,
        }


def make_client() -> TestClient:
    app = FastAPI()
    register_pallas_protocol_routes(
        app,
        manager=DummyManager(),
        plugin_config=SimpleNamespace(
            pallas_protocol_webui_path="",
            pallas_protocol_web_implementation="",
            pallas_protocol_webui_enabled=True,
        ),
    )
    return TestClient(app, follow_redirects=False)


def test_legacy_protocol_console_root_redirects_without_old_login() -> None:
    response = make_client().get("/protocol/console?source=bookmark")

    assert response.status_code == 307
    assert response.headers["location"] == "/pallas/protocol?source=bookmark"


def test_legacy_protocol_console_subpages_redirect_to_console_routes() -> None:
    client = make_client()

    assert (
        client.get("/protocol/console/new").headers["location"]
        == "/pallas/protocol/create"
    )
    assert (
        client.get("/protocol/console/import").headers["location"]
        == "/pallas/protocol/import"
    )
    assert (
        client.get("/protocol/console/assets").headers["location"]
        == "/pallas/protocol/assets"
    )
    assert (
        client.get("/protocol/console/settings").headers["location"]
        == "/pallas/preferences"
    )


def test_legacy_protocol_login_is_not_an_independent_html_page() -> None:
    response = make_client().get("/protocol/console/login")

    assert response.status_code == 307
    assert response.headers["location"] == "/pallas/protocol"


def test_console_instance_webui_proxies_the_registered_subpath(monkeypatch) -> None:
    monkeypatch.setattr(
        "pallas.console.webui.console_login.extract_session_from_request",
        lambda **_kwargs: "session",
    )
    server = ThreadingHTTPServer(("127.0.0.1", 0), _UpstreamHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    app = FastAPI()
    register_pallas_protocol_routes(
        app,
        manager=ProxyManager(server.server_port),
        plugin_config=SimpleNamespace(
            pallas_protocol_webui_path="",
            pallas_protocol_web_implementation="",
            pallas_protocol_webui_enabled=True,
        ),
    )
    try:
        response = TestClient(app).get(
            "/pallas/protocol/instances/napcat-1/webui/assets/app.js"
        )
    finally:
        server.shutdown()
        thread.join()

    assert response.status_code == 200
    assert response.text == "upstream:/webui/assets/app.js"


def test_console_registers_an_instance_websocket_proxy_route() -> None:
    app = FastAPI()
    register_pallas_protocol_routes(
        app,
        manager=DummyManager(),
        plugin_config=SimpleNamespace(
            pallas_protocol_webui_path="",
            pallas_protocol_web_implementation="",
            pallas_protocol_webui_enabled=True,
        ),
    )

    assert any(
        isinstance(route, WebSocketRoute)
        and route.path
        == "/pallas/protocol/instances/{account_id}/{surface}/{subpath:path}"
        for route in app.routes
    )

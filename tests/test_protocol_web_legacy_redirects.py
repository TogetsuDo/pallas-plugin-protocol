from types import SimpleNamespace

import nonebot
from fastapi import FastAPI
from fastapi.testclient import TestClient

nonebot.init()

from pallas_plugin_protocol.web.routes import register_pallas_protocol_routes  # noqa: E402


class DummyManager:
    pass


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

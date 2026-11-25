"""The YAML files load in the Dify SDK, every tool has a handler and full i18n,
and the provider validates credentials."""

from pathlib import Path

import pytest
import yaml
from dify_plugin.core.utils.class_loader import load_single_subclass_from_source
from dify_plugin.entities.tool import ToolProviderConfiguration
from dify_plugin.errors.tool import ToolProviderCredentialValidationError
from dify_plugin.interfaces.tool import Tool

from fakes import FakeResponse, FakeSession
from useapi_flow import runner
from useapi_flow.client import Client
from useapi_flow.handlers import HANDLERS, Ctx

ROOT = Path(__file__).resolve().parents[1]
LANGS = {"en_US", "zh_Hans", "ja_JP", "pt_BR"}
PROVIDER = yaml.safe_load((ROOT / "provider/google_flow_useapi.yaml").read_text())
TOOL_FILES = [ROOT / p for p in PROVIDER["tools"]]


def test_provider_loads_in_sdk():
    config = ToolProviderConfiguration(**yaml.safe_load((ROOT / "provider/google_flow_useapi.yaml").read_text()))
    assert len(config.tools) == len(HANDLERS)
    assert {c.name for c in config.credentials_schema} == {"useapi_token", "email"}


def test_manifest_fields():
    manifest = yaml.safe_load((ROOT / "manifest.yaml").read_text())
    assert manifest["author"] == "useapi" and manifest["name"] == "google_flow_useapi"
    assert manifest["version"] == "0.1.0"
    assert manifest["network"]["domains"] == ["api.useapi.net", "flow-content.google"]
    assert set(manifest["label"]) == LANGS and set(manifest["description"]) == LANGS
    for text in manifest["description"].values():
        assert "useapi.net" in text and "15" in text and "Google Flow" in text and "300" in text and "Google" in text
    assert (ROOT / "_assets" / manifest["icon"]).is_file()


def walk_i18n(node, where):
    if isinstance(node, dict):
        for key in ("label", "human_description", "human", "help", "placeholder"):
            if key in node and isinstance(node[key], dict):
                assert set(node[key]) == LANGS, (where, key, node[key])
                assert all(str(v).strip() for v in node[key].values()), (where, key)
        for key, value in node.items():
            walk_i18n(value, f"{where}.{key}")
    elif isinstance(node, list):
        for i, value in enumerate(node):
            walk_i18n(value, f"{where}[{i}]")


@pytest.mark.parametrize("path", TOOL_FILES, ids=[p.stem for p in TOOL_FILES])
def test_tool_yaml(path):
    data = yaml.safe_load(path.read_text())
    walk_i18n(data, path.stem)
    assert data["identity"]["name"] in HANDLERS
    assert data["description"]["llm"].strip()
    for p in data.get("parameters", []):
        if p["form"] == "llm":
            assert p.get("llm_description"), (path.stem, p["name"])
        if p["type"] == "select":
            assert p["options"], (path.stem, p["name"])


@pytest.mark.parametrize("path", TOOL_FILES, ids=[p.stem for p in TOOL_FILES])
def test_tool_class_loads(path):
    data = yaml.safe_load(path.read_text())
    source = data["extra"]["python"]["source"]
    cls = load_single_subclass_from_source(module_name=source[:-3].replace("/", "."), script_path=str(ROOT / source), parent_type=Tool)
    assert issubclass(cls, Tool)


def test_no_emoji_in_shipped_text():
    import re

    emoji = re.compile("[\U0001f300-\U0001faff☀-➿]")
    for path in [
        *ROOT.glob("*.md"),
        *ROOT.glob("readme/*.md"),
        *ROOT.glob("tools/*.yaml"),
        ROOT / "manifest.yaml",
        ROOT / "provider/google_flow_useapi.yaml",
    ]:
        assert not emoji.search(path.read_text(encoding="utf-8")), path


def provider_with(routes, email=None):
    from provider.google_flow_useapi import GoogleFlowUseapiProvider

    session = FakeSession(routes)
    original = runner.make_context

    def fake_context(credentials):
        return Ctx(client=Client(credentials["useapi_token"], session=session), default_email=credentials.get("email") or None)

    runner.make_context = fake_context
    try:
        GoogleFlowUseapiProvider()._validate_credentials({"useapi_token": "user:1-x", "email": email})
    finally:
        runner.make_context = original
    return session


def test_credentials_ok():
    session = provider_with([("GET", "accounts", {"a@b.com": {"health": "OK"}})], email="a@b.com")
    assert session.calls[0].path == "accounts"


def test_credentials_bad_token():
    with pytest.raises(ToolProviderCredentialValidationError, match="rejected the API token"):
        provider_with([("GET", "accounts", FakeResponse(401, {"error": "useapi.net ⁝ Unauthorized", "code": 401}))])


def test_credentials_no_account():
    with pytest.raises(ToolProviderCredentialValidationError, match="no Google account is connected to Google Flow"):
        provider_with([("GET", "accounts", {})])


def test_credentials_unknown_email():
    with pytest.raises(ToolProviderCredentialValidationError, match="not a connected Google Flow account"):
        provider_with([("GET", "accounts", {"a@b.com": {}})], email="other@b.com")


class FakeTool:
    class runtime:
        credentials = {"useapi_token": "t"}

    def create_text_message(self, text):
        return ("text", text)

    def create_json_message(self, obj):
        return ("json", obj)

    def create_variable_message(self, name, value):
        return ("var", name, value)

    def create_blob_message(self, blob, meta=None):
        return ("blob", meta)

    def create_link_message(self, link):
        return ("link", link)


def test_runner_converts_messages(monkeypatch):
    session = FakeSession([("GET", "accounts", {"a@b.com": {"health": "OK"}})])
    monkeypatch.setattr(runner, "make_context", lambda c: Ctx(client=Client("t", session=session)))
    messages = list(runner.invoke(FakeTool(), "list_accounts", {}))
    assert ("var", "emails", ["a@b.com"]) in messages
    assert messages[0][0] == "text" and "1 Google account" in messages[0][1]


def load_tool(name):
    return load_single_subclass_from_source(module_name=f"tools.{name}", script_path=str(ROOT / f"tools/{name}.py"), parent_type=Tool)


def test_real_sdk_messages_for_a_generation(monkeypatch):
    """Run a generated Tool class through the SDK's own invoke() and message models."""
    from dify_plugin.entities.tool import ToolInvokeMessage

    url = "https://flow-content.google/video/a1?Expires=1&KeyName=k&Signature=s"
    record = {
        "jobid": "j1",
        "type": "video",
        "status": "completed",
        "response": {
            "media": [
                {
                    "mediaGenerationId": "user:1-email:61-video:a1",
                    "mediaMetadata": {"mediaStatus": {"mediaGenerationStatus": "MEDIA_GENERATION_STATUS_SUCCESSFUL"}},
                    "videoUrl": url,
                }
            ]
        },
    }
    session = FakeSession(
        [
            ("POST", "videos", record),
            ("GET", "/video/", FakeResponse(200, content=b"abc", headers={"Content-Type": "video/mp4"})),
        ]
    )
    monkeypatch.setattr(runner, "make_context", lambda c: Ctx(client=Client("t", session=session)))
    tool = load_tool("generate_video").from_credentials({"useapi_token": "t"})
    messages = list(tool.invoke({"prompt": "A boat", "wait": True}))
    assert all(isinstance(m, ToolInvokeMessage) for m in messages)
    kinds = [m.type for m in messages]
    assert kinds[0] == ToolInvokeMessage.MessageType.TEXT
    assert ToolInvokeMessage.MessageType.BLOB in kinds and ToolInvokeMessage.MessageType.JSON in kinds
    variables = {m.message.variable_name: m.message.variable_value for m in messages if m.type == ToolInvokeMessage.MessageType.VARIABLE}
    assert variables["jobid"] == "j1" and variables["file_urls"] == [url]
    blob = next(m for m in messages if m.type == ToolInvokeMessage.MessageType.BLOB)
    assert blob.meta == {"mime_type": "video/mp4", "filename": "google-flow-video.mp4"}


def test_full_product_names_and_wording():
    """'Google Flow', never bare 'Flow'; 'third-party', never 'unofficial'."""
    import re

    bare = re.compile(r"(?<!Google )(?<!google-)\bFlow\b(?! Music)")
    for path in [
        *ROOT.glob("*.md"),
        *ROOT.glob("readme/*.md"),
        *ROOT.glob("tools/*.yaml"),
        ROOT / "manifest.yaml",
        ROOT / "provider/google_flow_useapi.yaml",
    ]:
        content = path.read_text(encoding="utf-8")
        assert "unofficial" not in content.lower(), path
        for line in content.splitlines():
            assert not bare.search(line), (path.name, line)
    for path in [ROOT / "useapi_flow/handlers.py", ROOT / "useapi_flow/client.py", ROOT / "provider/google_flow_useapi.py"]:
        for literal in re.findall(r'"([^"\n]*)"', path.read_text(encoding="utf-8")):
            assert not bare.search(literal), (path.name, literal)


def test_only_active_models_offered():
    offered = set()
    for path in TOOL_FILES:
        for p in yaml.safe_load(path.read_text()).get("parameters", []):
            if p["name"] == "model":
                offered |= {o["value"] for o in p["options"]}
    assert offered == {
        "veo-3.1-lite",
        "omni-flash-1.2",
        "veo-3.1-lite-low-priority",
        "nano-banana-2-lite",
        "nano-banana-2",
        "nano-banana-pro",
    }


def test_output_schema_matches_variables():
    """Every variable a tool can emit is declared in its output_schema."""
    import re

    source = (ROOT / "useapi_flow/handlers.py").read_text()
    emitted = set(re.findall(r'var\("([a-z_]+)"', source))
    declared = set()
    for path in TOOL_FILES:
        declared |= set((yaml.safe_load(path.read_text()).get("output_schema") or {}).get("properties", {}))
    assert emitted <= declared, emitted - declared

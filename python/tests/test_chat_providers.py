"""Unit tests for MultiProviderChatParser."""

from datetime import datetime
from typing import List

import pytest

from src.chat_providers import (
    ENV_VAR_NAME,
    ENV_VAR_RECURSIVE,
    MultiProviderChatParser,
)
from cligent.core.models import Chat, Message, Role


class StubProvider:
    """Simple stub that mimics limited cligent provider behaviour."""

    def __init__(self, name: str):
        self.name = name
        self.selected_messages = []
        self.list_calls: List[bool] = []
        self._store = {
            "log-a": Chat(
                messages=[
                    Message(
                        role=Role.USER,
                        content=f"Question from {name}",
                        provider=name,
                        log_uri="log-a",
                        timestamp=datetime(2025, 1, 1, 12, 0, 0),
                    )
                ]
            )
        }

    def list_logs(self, recursive: bool = True):
        self.list_calls.append(recursive)
        return [
            (
                "log-a",
                {
                    "modified": "2025-01-01T12:00:00Z",
                    "project": f"project-{self.name}",
                },
            )
        ]

    def parse(self, log_uri):
        return self._store[log_uri]

    def select(self, log_uri, indices=None):
        chat = self._store[log_uri]
        if not indices:
            self.selected_messages = []
            return
        self.selected_messages = [
            chat.messages[i] for i in indices if i < len(chat.messages)
        ]

    def clear_selection(self):
        self.selected_messages = []


@pytest.fixture(autouse=True)
def clear_env(monkeypatch):
    monkeypatch.delenv(ENV_VAR_NAME, raising=False)


def test_default_provider_loading(monkeypatch):
    monkeypatch.setattr(
        "src.chat_providers._create_parser",
        lambda provider: StubProvider(provider),
    )

    parser = MultiProviderChatParser.from_environment()

    assert parser.providers[0] == "claude-code"
    logs = parser.list_logs()
    assert logs
    log_uri, metadata = logs[0]
    assert log_uri.startswith("claude-code:")
    assert metadata["provider_label"] == "Claude"
    assert parser._parsers["claude-code"].list_calls == [True]

    chat = parser.parse(log_uri)
    assert chat.messages[0].log_uri.startswith("claude-code:")

    parser.select(log_uri, [0])
    yaml_content = parser.compose()
    assert "log_uri: 'claude-code:" in yaml_content

    decomposed = parser.decompose(yaml_content)
    assert decomposed.messages[0].provider == "claude-code"


def test_environment_provider_filter(monkeypatch):
    order = []

    def factory(provider):
        order.append(provider)
        return StubProvider(provider)

    monkeypatch.setattr("src.chat_providers._create_parser", factory)
    monkeypatch.setenv(ENV_VAR_NAME, "gemini-cli")

    parser = MultiProviderChatParser.from_environment()

    assert parser.providers == ("gemini-cli",)
    logs = parser.list_logs()
    log_uri, metadata = logs[0]
    assert log_uri.startswith("gemini-cli:")
    assert metadata["provider_label"] == "Gemini"
    assert order == ["gemini-cli"]
    assert parser._parsers["gemini-cli"].list_calls == [True]


def test_compose_with_explicit_messages(monkeypatch):
    monkeypatch.setattr(
        "src.chat_providers._create_parser",
        lambda provider: StubProvider(provider),
    )

    parser = MultiProviderChatParser.from_environment()
    logs = parser.list_logs()
    log_uri, _ = logs[0]
    chat = parser.parse(log_uri)

    yaml_content = parser.compose(*chat.messages)
    assert "Question from claude-code" in yaml_content
    assert "log_uri: 'claude-code:" in yaml_content


def test_clear_selection(monkeypatch):
    monkeypatch.setattr(
        "src.chat_providers._create_parser",
        lambda provider: StubProvider(provider),
    )

    parser = MultiProviderChatParser.from_environment()
    log_uri, _ = parser.list_logs()[0]
    parser.select(log_uri, [0])
    parser.clear_selection()

    with pytest.raises(ValueError):
        parser.compose()


def test_recursive_env_toggle(monkeypatch):
    def factory(provider):
        return StubProvider(provider)

    monkeypatch.setattr("src.chat_providers._create_parser", factory)
    monkeypatch.setenv(ENV_VAR_RECURSIVE, "0")

    parser = MultiProviderChatParser.from_environment()
    assert parser.recursive is False

    parser.list_logs()
    stub = parser._parsers[parser.providers[0]]
    assert stub.list_calls == [False]

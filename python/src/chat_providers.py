"""Multi-provider chat parser integration for Tigs."""

from __future__ import annotations

import os
import re
from dataclasses import replace
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import yaml

try:
    from cligent import create as _create_parser
    from cligent.core.models import Chat, Message, Role
except ImportError:  # pragma: no cover - cligent is a runtime dependency
    _create_parser = None  # type: ignore


KNOWN_PROVIDER_ALIASES: Dict[str, str] = {
    "claude": "claude-code",
    "claude-code": "claude-code",
    "gemini": "gemini-cli",
    "gemini-cli": "gemini-cli",
    "qwen": "qwen-code",
    "qwen-code": "qwen-code",
}

DEFAULT_PROVIDER_ORDER: Sequence[str] = (
    "claude-code",
    "gemini-cli",
    "qwen-code",
)

PROVIDER_LABELS: Dict[str, str] = {
    "claude-code": "Claude",
    "gemini-cli": "Gemini",
    "qwen-code": "Qwen",
}

ENV_VAR_NAME = "TIGS_CHAT_PROVIDERS"
ENV_VAR_RECURSIVE = "TIGS_CHAT_RECURSIVE"


class MultiProviderChatParser:
    """Aggregate chat parser that orchestrates multiple Cligent providers."""

    def __init__(self, provider_names: Optional[Iterable[str]] = None) -> None:
        self._warnings: List[str] = []
        self._errors: Dict[str, str] = {}
        self._parsers: Dict[str, object] = {}
        self._order: List[str] = []
        self._has_providers = False
        self._recursive = self._recursive_from_environment()

        if _create_parser is None:
            self._warnings.append("Cligent is not available; no chat providers loaded")
            return

        if provider_names is None:
            provider_names = self._providers_from_environment()

        unique_providers = []
        seen = set()
        for name in provider_names:
            canonical = self._canonicalize(name)
            if not canonical:
                self._warnings.append(f"Unknown provider '{name}' ignored")
                continue
            if canonical not in seen:
                unique_providers.append(canonical)
                seen.add(canonical)

        if not unique_providers:
            self._warnings.append("No valid chat providers configured")
            return

        for provider in unique_providers:
            try:
                parser = _create_parser(provider)
            except Exception as exc:  # pragma: no cover - defensive guard
                self._errors[provider] = str(exc)
                continue

            self._parsers[provider] = parser
            self._order.append(provider)

        if not self._order:
            self._warnings.append("Failed to initialize any chat providers")
        else:
            self._has_providers = True

    @classmethod
    def from_environment(cls) -> "MultiProviderChatParser":
        """Create parser honoring the TIGS_CHAT_PROVIDERS environment variable."""
        return cls()

    @property
    def warnings(self) -> Sequence[str]:
        return tuple(self._warnings)

    @property
    def errors(self) -> Dict[str, str]:
        return dict(self._errors)

    @property
    def providers(self) -> Sequence[str]:
        return tuple(self._order)

    def __bool__(self) -> bool:
        return True

    @property
    def has_providers(self) -> bool:
        return self._has_providers

    @property
    def recursive(self) -> bool:
        return self._recursive

    # ------------------------------------------------------------------
    # Public API mirroring cligent ChatParser interface
    # ------------------------------------------------------------------
    def list_logs(self) -> List[Tuple[str, Dict[str, object]]]:
        logs: List[Tuple[str, Dict[str, object]]] = []
        for provider in self._order:
            parser = self._parsers.get(provider)
            if not parser:
                continue

            list_fn = getattr(parser, "list_logs", None)
            if not callable(list_fn):
                continue

            try:
                provider_logs = list_fn(recursive=self._recursive)
            except TypeError:
                # Older adapters without the new signature
                provider_logs = list_fn()
            except Exception:  # pragma: no cover - defensive guard
                continue

            short_name = PROVIDER_LABELS.get(provider, provider.replace("-", " ").title())
            for log_uri, metadata in provider_logs:
                meta = dict(metadata or {})
                meta["provider"] = provider
                meta["provider_label"] = short_name
                meta.setdefault("modified", "")
                prefixed_uri = self._prefix_log_uri(provider, str(log_uri))
                logs.append((prefixed_uri, meta))

        logs.sort(key=lambda item: self._modified_sort_key(item[1]), reverse=True)
        return logs

    def parse(self, log_uri: str) -> Optional[Chat]:
        provider, raw_uri = self._split_prefixed(log_uri)
        parser = self._parsers.get(provider)
        if not parser:
            raise ValueError(f"No parser available for provider '{provider}'")

        parse_fn = getattr(parser, "parse", None)
        if not callable(parse_fn):
            raise AttributeError("Provider parser lacks 'parse' method")

        chat = parse_fn(raw_uri)
        if chat is None:
            return None

        converted = [self._convert_message(msg, provider) for msg in chat.messages]
        return Chat(messages=converted)

    def select(self, log_uri: str, indices: Optional[Sequence[int]] = None) -> None:
        provider, raw_uri = self._split_prefixed(log_uri)
        parser = self._parsers.get(provider)
        if not parser:
            raise ValueError(f"No parser available for provider '{provider}'")

        select_fn = getattr(parser, "select", None)
        if callable(select_fn):
            select_fn(raw_uri, list(indices) if indices is not None else None)

    def compose(self, *args) -> str:
        messages: List[Message] = []

        if args:
            for item in args:
                if isinstance(item, Message):
                    provider = self._infer_provider_from_log_uri(item.log_uri, item.provider)
                    messages.append(self._convert_message(item, provider))
                elif isinstance(item, Chat):
                    for msg in item.messages:
                        provider = self._infer_provider_from_log_uri(msg.log_uri, msg.provider)
                        messages.append(self._convert_message(msg, provider))
                else:
                    raise ValueError("compose accepts Message or Chat instances")
        else:
            for provider in self._order:
                parser = self._parsers.get(provider)
                if not parser:
                    continue
                selected_messages = getattr(parser, "selected_messages", None)
                if selected_messages:
                    messages.extend(
                        self._convert_message(msg, provider) for msg in selected_messages
                    )

        if not messages:
            raise ValueError("No messages selected for composition")

        merged = Chat(messages=sorted(messages, key=lambda m: m.timestamp or datetime.min))
        return merged.export()

    def decompose(self, tigs_yaml: str) -> Chat:
        try:
            data = yaml.safe_load(tigs_yaml)
        except yaml.YAMLError as exc:  # pragma: no cover - invalid input guard
            raise ValueError(f"Invalid YAML format: {exc}") from exc

        if not isinstance(data, dict):
            raise ValueError("YAML must contain a dictionary")

        if data.get("schema") != "tigs.chat/v1":
            raise ValueError(f"Expected schema 'tigs.chat/v1', got '{data.get('schema')}'")

        messages_data = data.get("messages")
        if not isinstance(messages_data, list):
            raise ValueError("'messages' field must be a list")

        messages: List[Message] = []
        for index, msg_data in enumerate(messages_data):
            if not isinstance(msg_data, dict):
                raise ValueError(f"Message {index} must be a dictionary")

            role_str = str(msg_data.get("role", "")).lower()
            if not role_str:
                raise ValueError(f"Message {index} must have 'role' field")

            try:
                role = Role(role_str)
            except ValueError as exc:
                raise ValueError(f"Message {index} has invalid role '{role_str}'") from exc

            content = msg_data.get("content", "")
            if isinstance(content, str):
                content_text = content.strip()
            else:
                content_text = str(content).strip()

            if content_text == "":
                content_text = ""

            timestamp = self._parse_timestamp(msg_data.get("timestamp"))
            raw_log_uri = str(msg_data.get("log_uri", ""))
            provider = self._infer_provider_from_log_uri(raw_log_uri, msg_data.get("provider"))
            log_uri = self._ensure_prefixed_log_uri(raw_log_uri, provider)

            message = Message(
                role=role,
                content=content_text,
                provider=provider,
                log_uri=log_uri,
                timestamp=timestamp,
                raw_data=msg_data,
            )
            messages.append(message)

        return Chat(messages=messages)

    def clear_selection(self) -> None:
        for parser in self._parsers.values():
            clear_fn = getattr(parser, "clear_selection", None)
            if callable(clear_fn):
                clear_fn()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _providers_from_environment(self) -> Sequence[str]:
        env_value = os.environ.get(ENV_VAR_NAME)
        if not env_value:
            return DEFAULT_PROVIDER_ORDER

        tokens = re.split(r"[\s,]+", env_value.strip())
        providers: List[str] = []
        for token in tokens:
            if not token:
                continue
            lower = token.lower()
            if lower == "all":
                providers.extend(DEFAULT_PROVIDER_ORDER)
                continue
            providers.append(lower)
        return providers

    def _recursive_from_environment(self) -> bool:
        value = os.environ.get(ENV_VAR_RECURSIVE)
        if value is None:
            return True

        normalized = value.strip().lower()
        if normalized in {"0", "false", "no", "off"}:
            return False
        if normalized in {"1", "true", "yes", "on"}:
            return True

        # Unexpected value - keep default and warn
        self._warnings.append(
            f"Unrecognized {ENV_VAR_RECURSIVE} value '{value}', defaulting to recursive logs"
        )
        return True

    def _canonicalize(self, provider: str) -> Optional[str]:
        if not provider:
            return None
        return KNOWN_PROVIDER_ALIASES.get(provider.lower(), provider.lower())

    def _prefix_log_uri(self, provider: str, log_uri: str) -> str:
        if log_uri.startswith(f"{provider}:"):
            return log_uri
        return f"{provider}:{log_uri}"

    def _ensure_prefixed_log_uri(self, log_uri: str, provider: str) -> str:
        log = log_uri or ""
        if provider and log.startswith(f"{provider}:"):
            return log
        if provider:
            return self._prefix_log_uri(provider, log)
        return log

    def _split_prefixed(self, prefixed: str) -> Tuple[str, str]:
        if ":" not in prefixed:
            if self._order:
                return self._order[0], prefixed
            raise ValueError(
                "Log URI must include provider prefix (e.g. 'claude-code:session')"
            )
        provider, raw = prefixed.split(":", 1)
        canonical = self._canonicalize(provider)
        if canonical not in self._parsers:
            raise ValueError(f"Unknown provider prefix '{provider}'")
        return canonical, raw

    def _modified_sort_key(self, metadata: Dict[str, object]) -> datetime:
        value = metadata.get("modified")
        if isinstance(value, datetime):
            return value
        if isinstance(value, str) and value:
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                pass
        return datetime.min

    def _convert_message(self, message: Message, provider_hint: Optional[str]) -> Message:
        provider = self._canonicalize(provider_hint or message.provider or "")
        if provider not in self._parsers:
            provider = self.providers[0] if self.providers else provider_hint or ""

        log_uri = self._ensure_prefixed_log_uri(message.log_uri, provider)

        if message.provider == provider and message.log_uri == log_uri:
            return message

        return replace(message, provider=provider, log_uri=log_uri)

    def _infer_provider_from_log_uri(
        self, log_uri: str, provider_hint: Optional[str]
    ) -> str:
        if log_uri and ":" in log_uri:
            prefix = log_uri.split(":", 1)[0]
            canonical = self._canonicalize(prefix)
            if canonical in self._parsers or canonical in KNOWN_PROVIDER_ALIASES.values():
                return canonical

        if provider_hint:
            canonical = self._canonicalize(str(provider_hint))
            if canonical in self._parsers or canonical in KNOWN_PROVIDER_ALIASES.values():
                return canonical

        if self._order:
            return self._order[0]
        return self._canonicalize(provider_hint or "claude-code") or "claude-code"

    def _parse_timestamp(self, timestamp_value: object) -> Optional[datetime]:
        if not timestamp_value:
            return None
        if isinstance(timestamp_value, datetime):
            return timestamp_value
        if isinstance(timestamp_value, str):
            ts = timestamp_value.strip()
            if ts.endswith("Z"):
                ts = ts.replace("Z", "+00:00")
            try:
                return datetime.fromisoformat(ts)
            except ValueError:
                return None
        return None


def get_chat_parser() -> MultiProviderChatParser:
    """Convenience helper used by TUI modules."""
    return MultiProviderChatParser.from_environment()

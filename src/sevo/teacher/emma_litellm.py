"""Emma — live teacher adapter (LiteLLM gateway), INERT BY DEFAULT.

This is the bridge to the *real* Emma that will eventually teach Sèvo the
official French curriculum. It uses the local LiteLLM gateway (local models,
zero per-token cost) to generate varied, curriculum-aligned exercise items. The
brain still learns through its procedural engine and is graded deterministically
by the oracle — the model only adds variety and coverage, it never grades.

Safety contract (mirrors the Talki fleet's live-edge pattern):

* **Inert by default.** No network call happens unless BOTH
  ``SEVO_EMMA_LIVE=1`` is set AND ``LITELLM_URL`` is configured. Otherwise the
  adapter raises a clear error telling the operator how to enable it.
* **No Anthropic billing (Q-012 / R-303).** Any ``ANTHROPIC_*`` env var is
  stripped from the process view before a transport is built, so a leaked key
  from a parent Claude Code session can never switch the gateway to per-token
  Anthropic billing.
* **Bounded.** The HTTP transport has a hard timeout.
* **Offline-testable.** A transport can be injected (``FakeTransport``) so the
  whole wiring is proven without touching the network.

Enable a real run (operator, on an explicit GPU window):

    export LITELLM_URL=http://<gateway-host>:4000
    export LITELLM_MASTER_KEY=sk-...           # the gateway key, NOT an API key
    export SEVO_EMMA_LIVE=1
    PYTHONPATH=src python3 -c "from sevo.teacher.emma_litellm import EmmaLiteLLM; \
        print(EmmaLiteLLM().generate_french_tasks('fr.CE1.pluriel_reguliers', 6))"
"""
from __future__ import annotations

import json
import os

from ..curriculum.fr_cp_ce1 import NODES_FR, _make

LLM_KEYS_TO_STRIP = ("ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN")
DEFAULT_MODEL = "chat-fast"
TIMEOUT_S = 30


def _safe_env() -> dict:
    """Process env with any Anthropic credentials removed (Q-012 / R-303)."""
    env = dict(os.environ)
    for k in LLM_KEYS_TO_STRIP:
        env.pop(k, None)
    return env


class Transport:
    """Abstract chat transport. ``chat(messages) -> str`` (assistant content)."""

    def chat(self, messages: list[dict]) -> str:  # pragma: no cover - interface
        raise NotImplementedError


class FakeTransport(Transport):
    """Deterministic transport for tests — returns a canned JSON word list."""

    def __init__(self, words: list[str]) -> None:
        self.words = words
        self.calls: list[list[dict]] = []

    def chat(self, messages: list[dict]) -> str:
        self.calls.append(messages)
        return json.dumps(self.words, ensure_ascii=False)


class LiteLLMTransport(Transport):
    """HTTP transport to a LiteLLM gateway. Built only when a live run is enabled."""

    def __init__(self, url: str, master_key: str, model: str) -> None:
        self.url = url.rstrip("/")
        self.master_key = master_key
        self.model = model

    def chat(self, messages: list[dict]) -> str:  # pragma: no cover - needs network
        import urllib.request

        _safe_env()  # defensive: ensure no Anthropic creds linger in this scope
        body = json.dumps({"model": self.model, "messages": messages, "temperature": 0.7}).encode()
        req = urllib.request.Request(
            f"{self.url}/v1/chat/completions",
            data=body,
            headers={"Authorization": f"Bearer {self.master_key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            data = json.loads(resp.read())
        return data["choices"][0]["message"]["content"]


class EmmaLiteLLM:
    def __init__(self, transport: Transport | None = None, model: str = DEFAULT_MODEL) -> None:
        self.model = model
        # An injected transport (e.g. FakeTransport) bypasses the env gate so the
        # wiring is testable offline. A None transport requires an explicit live run.
        self._transport = transport

    @staticmethod
    def is_enabled() -> bool:
        return os.environ.get("SEVO_EMMA_LIVE") == "1" and bool(os.environ.get("LITELLM_URL"))

    def _ensure_transport(self) -> Transport:
        if self._transport is not None:
            return self._transport
        if not self.is_enabled():
            raise RuntimeError(
                "EmmaLiteLLM is inert. Set SEVO_EMMA_LIVE=1 and LITELLM_URL to run live, "
                "or inject a transport (FakeTransport) for offline use."
            )
        env = _safe_env()
        self._transport = LiteLLMTransport(
            url=env["LITELLM_URL"],
            master_key=env.get("LITELLM_MASTER_KEY", ""),
            model=self.model,
        )
        return self._transport

    def generate_french_tasks(self, node_id: str, n: int) -> list:
        """Ask the model for ``n`` curriculum-aligned French nouns, then turn
        them into gradable tasks (answers computed deterministically by the
        curriculum, never by the model)."""
        if node_id not in NODES_FR:
            raise ValueError(f"unknown French node: {node_id}")
        spec = NODES_FR[node_id]
        transport = self._ensure_transport()
        system = (
            "Tu es Emma, enseignante de CP/CE1. Réponds UNIQUEMENT par un tableau "
            "JSON de noms communs français au singulier, sans phrase autour."
        )
        user = (
            f"Donne {n} noms communs français adaptés à la notion « {spec['title']} » "
            f"(catégorie {spec['category']}). Format: [\"mot1\", \"mot2\", ...]"
        )
        raw = transport.chat([{"role": "system", "content": system},
                              {"role": "user", "content": user}])
        words = _parse_words(raw)
        return [_make(node_id, w) for w in words[:n]]


def _parse_words(raw: str) -> list[str]:
    raw = raw.strip()
    try:
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(w).strip() for w in data if str(w).strip()]
    except json.JSONDecodeError:
        pass
    # Fallback: comma/space separated.
    return [w.strip(" .\"'[]") for w in raw.replace("\n", ",").split(",") if w.strip(" .\"'[]")]

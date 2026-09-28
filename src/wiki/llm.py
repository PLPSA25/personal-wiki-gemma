"""Talk to the local language model (Ollama). Only this machine is allowed in local mode.

The rest of the harness depends on the small `LanguageModel` interface, so tests can use a fake
model and a different runtime could be plugged in without touching ask/chat/ingest.
"""

from __future__ import annotations

import json
import socket
import time
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlparse

from .errors import ModelError, WikiError

DEFAULT_MODEL = "gemma4:e2b"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_NUM_CTX = 8192  # context window we ask for (the model supports far more; memory is the limit)

_LOCAL_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


@dataclass(frozen=True)
class Reply:
    text: str
    model: str
    prompt_tokens: int
    output_tokens: int
    seconds: float  # wall-clock time of the call
    load_seconds: float  # time Ollama spent loading the model into memory (0 when already loaded)


class LanguageModel(Protocol):
    name: str

    def chat(self, messages: list[dict], *, temperature: float, max_tokens: int, seed: int | None = None,
             response_format: dict | None = None, on_token: Callable[[str], None] | None = None) -> Reply: ...

    def identity(self) -> dict: ...


class _NoRedirects(urllib.request.HTTPRedirectHandler):
    """A local server has no reason to redirect; refuse rather than follow a redirect off this machine."""

    def redirect_request(self, *args, **kwargs):
        return None


def require_local_url(url: str) -> str:
    """Return `url` if it points at this machine, otherwise raise. Local mode must never leave the computer."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or parsed.hostname not in _LOCAL_HOSTS:
        raise WikiError(
            f"'{url}' is not a local address. Local mode only talks to this computer "
            f"(127.0.0.1 or localhost); no cloud fallback is available."
        )
    return url.rstrip("/")


class OllamaClient:
    """Minimal Ollama client using only the standard library (no proxy, no redirects)."""

    def __init__(self, base_url: str = DEFAULT_OLLAMA_URL, model: str = DEFAULT_MODEL,
                 timeout: float = 300.0, num_ctx: int = DEFAULT_NUM_CTX):
        self.base_url = require_local_url(base_url)
        self.name = model
        self.timeout = timeout
        self.num_ctx = num_ctx
        # An empty ProxyHandler stops HTTP_PROXY settings from routing local calls elsewhere.
        self._opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirects())

    def chat(self, messages: list[dict], *, temperature: float, max_tokens: int, seed: int | None = None,
             response_format: dict | None = None, on_token: Callable[[str], None] | None = None) -> Reply:
        """`response_format` is an optional JSON schema; Ollama then only produces JSON that matches it.

        With `on_token`, the reply is streamed and each piece of text is passed to it as it arrives.
        """
        options = {"temperature": temperature, "num_predict": max_tokens, "num_ctx": self.num_ctx}
        if seed is not None:
            options["seed"] = seed
        # think=False: Gemma's hidden "thinking" is slower and its text would pollute answers and citations.
        payload = {"model": self.name, "messages": messages, "stream": on_token is not None, "think": False,
                   "options": options}
        if response_format is not None:
            payload["format"] = response_format
        started = time.perf_counter()
        data = self._request("/api/chat", payload, on_token)
        message = data.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise ModelError("The model server returned an unexpected reply (no message text).")
        return Reply(
            text=message["content"].strip(),
            model=str(data.get("model", self.name)),
            prompt_tokens=int(data.get("prompt_eval_count", 0)),
            output_tokens=int(data.get("eval_count", 0)),
            seconds=time.perf_counter() - started,
            load_seconds=float(data.get("load_duration", 0)) / 1e9,
        )

    def identity(self) -> dict:
        """Exact model identity for evidence cards. Best effort: fields that cannot be read are left out."""
        info: dict = {"runtime": "ollama", "model": self.name}
        for path, payload in (("/api/version", None), ("/api/show", {"model": self.name}), ("/api/tags", None)):
            try:
                data = self._request(path, payload)
            except ModelError:
                continue
            if path == "/api/version":
                info["ollama_version"] = data.get("version")
            elif path == "/api/show":
                details = data.get("details", {})
                info["quantization"] = details.get("quantization_level")
                info["parameter_size"] = details.get("parameter_size")
                info["family"] = details.get("family")
            else:
                for entry in data.get("models", []):
                    if entry.get("name") == self.name:
                        info["digest"] = entry.get("digest")
        return info

    def _request(self, path: str, payload: dict | None, on_token: Callable[[str], None] | None = None) -> dict:
        body = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            self.base_url + path, data=body, headers={"Content-Type": "application/json"},
            method="GET" if body is None else "POST",
        )
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                if on_token is not None:
                    return _read_stream(response, on_token)
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            if error.code == 404:
                raise ModelError(
                    f"Model '{self.name}' is not installed. Download it once while online with: ollama pull {self.name}"
                ) from error
            raise ModelError(f"The model server answered with an error ({error.code} {error.reason}).") from error
        except urllib.error.URLError as error:
            if isinstance(error.reason, (socket.timeout, TimeoutError)):
                raise ModelError(f"The model did not answer within {self.timeout:.0f} seconds.") from error
            raise ModelError(
                f"Cannot reach the local model server at {self.base_url}. Start it with: ollama serve"
            ) from error
        except (socket.timeout, TimeoutError) as error:
            raise ModelError(f"The model did not answer within {self.timeout:.0f} seconds.") from error
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ModelError("The model server returned something that is not valid JSON.") from error


def _read_stream(response, on_token: Callable[[str], None]) -> dict:
    """Read Ollama's line-by-line JSON stream, forwarding text as it arrives; return the final summary record."""
    pieces: list[str] = []
    final: dict = {}
    for raw in response:
        line = raw.decode("utf-8").strip()
        if not line:
            continue
        chunk = json.loads(line)
        if "error" in chunk:
            raise ModelError(f"The model reported an error: {chunk['error']}")
        piece = chunk.get("message", {}).get("content", "")
        if piece:
            pieces.append(piece)
            on_token(piece)
        if chunk.get("done"):
            final = chunk
    final["message"] = {"role": "assistant", "content": "".join(pieces)}
    return final

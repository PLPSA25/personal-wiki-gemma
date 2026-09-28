import json
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from wiki.errors import WikiError
from wiki.llm import OllamaClient, require_local_url

RECEIVED = []


class Handler(BaseHTTPRequestHandler):
    """A throwaway local server that imitates the few Ollama endpoints we use."""

    def log_message(self, *args):
        pass

    def _send(self, code, body, headers=None):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/api/version":
            self._send(200, {"version": "9.9.9"})
        elif self.path == "/api/tags":
            self._send(200, {"models": [{"name": "gemma4:e2b", "digest": "abc123"}]})
        else:
            self._send(404, {})

    def do_POST(self):
        payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        RECEIVED.append((self.path, payload))
        model = payload.get("model")
        if model == "missing":
            self._send(404, {"error": "model not found"})
        elif model == "slow":
            time.sleep(1.0)
            self._send(200, {})
        elif model == "redirect":
            self._send(302, b"", {"Location": "http://example.com/"})
        elif model == "garbage":
            self._send(200, b"<html>not json</html>")
        elif model == "nomessage":
            self._send(200, {"done": True})
        elif self.path == "/api/show":
            self._send(200, {"details": {"quantization_level": "Q4_K_M", "parameter_size": "5.1B", "family": "gemma4"}})
        else:
            self._send(200, {"model": model, "message": {"role": "assistant", "content": "  hello [S1]  "},
                             "prompt_eval_count": 50, "eval_count": 7, "load_duration": 2_500_000_000})


@pytest.fixture(scope="module")
def server_url():
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.daemon_threads = True
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()


def test_chat_returns_text_and_timings_and_sends_expected_options(server_url):
    RECEIVED.clear()
    reply = OllamaClient(server_url, "gemma4:e2b", num_ctx=4096).chat(
        [{"role": "user", "content": "hi"}], temperature=0.1, max_tokens=99, seed=7)
    assert (reply.text, reply.prompt_tokens, reply.output_tokens, reply.load_seconds) == ("hello [S1]", 50, 7, 2.5)
    _, payload = RECEIVED[-1]
    assert payload["stream"] is False and payload["think"] is False
    assert payload["options"] == {"temperature": 0.1, "num_predict": 99, "num_ctx": 4096, "seed": 7}


def test_identity_reports_version_quantization_and_digest(server_url):
    info = OllamaClient(server_url, "gemma4:e2b").identity()
    assert info["ollama_version"] == "9.9.9" and info["quantization"] == "Q4_K_M" and info["digest"] == "abc123"


def test_missing_model_says_how_to_download_it(server_url):
    with pytest.raises(WikiError, match="ollama pull missing"):
        OllamaClient(server_url, "missing").chat([], temperature=0, max_tokens=1)


def test_server_that_is_not_running_says_how_to_start_it():
    with socket.socket() as probe:  # find a port nothing listens on (Windows takes ~2 s to refuse it)
        probe.bind(("127.0.0.1", 0))
        free_port = probe.getsockname()[1]
    with pytest.raises(WikiError, match="ollama serve"):
        OllamaClient(f"http://127.0.0.1:{free_port}", "gemma4:e2b", timeout=15).chat([], temperature=0, max_tokens=1)


def test_slow_model_times_out_with_a_clear_message(server_url):
    with pytest.raises(WikiError, match="did not answer"):
        OllamaClient(server_url, "slow", timeout=0.2).chat([], temperature=0, max_tokens=1)


def test_redirects_are_not_followed(server_url):
    with pytest.raises(WikiError, match="error"):
        OllamaClient(server_url, "redirect").chat([], temperature=0, max_tokens=1)


@pytest.mark.parametrize("model, message", [("garbage", "not valid JSON"), ("nomessage", "unexpected reply")])
def test_malformed_replies_are_reported_not_crashed_on(server_url, model, message):
    with pytest.raises(WikiError, match=message):
        OllamaClient(server_url, model).chat([], temperature=0, max_tokens=1)


@pytest.mark.parametrize("url", [
    "http://127.0.0.1:11434", "http://localhost:11434", "http://[::1]:11434", "http://127.0.0.1:11434/",
])
def test_local_addresses_are_accepted(url):
    assert require_local_url(url) == url.rstrip("/")


@pytest.mark.parametrize("url", [
    "http://example.com", "https://api.openai.com/v1", "http://192.168.1.20:11434", "http://127.0.0.1.evil.com",
    "http://localhost.evil.com:11434", "file:///etc/passwd", "ftp://127.0.0.1", "127.0.0.1:11434", "",
])
def test_non_local_addresses_are_refused(url):
    with pytest.raises(WikiError, match="not a local address"):
        require_local_url(url)

"""The ChaseOS Cloud route against a local stand-in gateway. These prove the contract, not model quality."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Event

import pytest

from chaser_agent.agent.reasoners import CLOUD_KEY_ENV, ChaseOSCloudReasoner, ReasonerUnavailable
from chaser_agent.agent.service import build_runtime


class Gateway:
    """Answers each request with the next queued (status, body) and records what it was sent."""

    def __init__(self, answers: list[tuple[int, dict]]) -> None:
        self.answers = list(answers)
        self.requests: list[dict] = []
        gateway = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
                gateway.requests.append({"path": self.path, "auth": self.headers.get("Authorization"), "agent": self.headers.get("User-Agent"), "harness": self.headers.get("X-ChaseOS-Agent-Harness"), "body": body})
                status, payload = gateway.answers.pop(0)
                data = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args: object) -> None:
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"

    def close(self) -> None:
        self.server.shutdown()


def answer(text: str) -> tuple[int, dict]:
    return 200, {"model": "chaseos/balanced", "choices": [{"message": {"role": "assistant", "content": text}}], "usage": {"prompt_tokens": 1200, "completion_tokens": 80, "cached_input_tokens": 0},
            "chaseos": {"actual_credits": 9, "resolved_model": "chaseos/balanced", "pricing": {"pricing_profile": "agent_harness"}, "routing": {"attempt_count": 1}}}


@pytest.fixture
def gateway_factory():
    made: list[Gateway] = []

    def make(*answers: tuple[int, dict]) -> Gateway:
        made.append(Gateway(list(answers)))
        return made[-1]

    yield make
    for gateway in made:
        gateway.close()


def test_sends_system_and_transcript_with_the_key_and_a_named_client(gateway_factory) -> None:
    gateway = gateway_factory(answer('{"thought": "ok", "actions": []}'))
    reasoner = ChaseOSCloudReasoner("test-key", base_url=gateway.url)
    reply = reasoner.complete("RULES", "TRANSCRIPT", timeout=10, cancel=Event())
    sent = gateway.requests[0]
    assert sent["path"] == "/v1/chat/completions"
    assert sent["auth"] == "Bearer test-key"
    assert "Python-urllib" not in sent["agent"]
    assert sent["body"]["messages"] == [{"role": "system", "content": "RULES"}, {"role": "user", "content": "TRANSCRIPT"}]
    assert sent["body"]["response_format"] == {"type": "json_object"}
    assert reply.route == "chaseos-cloud" and reply.model == "chaseos/balanced" and reply.text.startswith("{")
    assert reply.credits == 9
    assert sent["harness"] == "chaser"
    assert reply.usage == {"prompt_tokens": 1200, "completion_tokens": 80, "cached_input_tokens": 0, "credits": 9,
                           "pricing_profile": "agent_harness", "resolved_model": "chaseos/balanced", "attempts": 1}


def test_retries_one_gateway_error_and_never_more(gateway_factory) -> None:
    gateway = gateway_factory((502, {}), answer("second time"))
    assert ChaseOSCloudReasoner("k", base_url=gateway.url).complete("s", "t", timeout=20, cancel=Event()).text == "second time"
    gateway = gateway_factory((503, {}), (503, {}), answer("never reached"))
    with pytest.raises(ReasonerUnavailable) as caught:
        ChaseOSCloudReasoner("k", base_url=gateway.url).complete("s", "t", timeout=20, cancel=Event())
    assert caught.value.code == "route_error" and len(gateway.requests) == 2


def test_out_of_credits_stops_the_turn_without_retrying(gateway_factory) -> None:
    gateway = gateway_factory((402, {"error": {"available": 0}}))
    with pytest.raises(ReasonerUnavailable) as caught:
        ChaseOSCloudReasoner("k", base_url=gateway.url).complete("s", "t", timeout=10, cancel=Event())
    assert caught.value.code == "out_of_credits" and len(gateway.requests) == 1


def test_a_refused_key_and_an_empty_reply_say_so(gateway_factory) -> None:
    gateway = gateway_factory((401, {}), answer("   "))
    reasoner = ChaseOSCloudReasoner("k", base_url=gateway.url)
    with pytest.raises(ReasonerUnavailable) as refused:
        reasoner.complete("s", "t", timeout=10, cancel=Event())
    with pytest.raises(ReasonerUnavailable) as empty:
        reasoner.complete("s", "t", timeout=10, cancel=Event())
    assert (refused.value.code, empty.value.code) == ("not_authorised", "bad_output")


def test_without_a_key_it_is_unavailable_and_sends_nothing() -> None:
    reasoner = ChaseOSCloudReasoner("")
    assert reasoner.status()["available"] is False
    with pytest.raises(ReasonerUnavailable) as caught:
        reasoner.complete("s", "t", timeout=5, cancel=Event())
    assert caught.value.code == "not_configured"


def test_the_key_leaves_the_environment_so_launched_tools_never_inherit_it() -> None:
    environ = {CLOUD_KEY_ENV: "secret-value", "OTHER": "x"}
    reasoner = ChaseOSCloudReasoner.from_environment(environ)
    assert CLOUD_KEY_ENV not in environ and reasoner.status()["available"] is True
    assert "secret-value" not in json.dumps(reasoner.status())


def test_cloud_is_the_first_route_auto_tries(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv(CLOUD_KEY_ENV, "k")
    runtime = build_runtime(tmp_path)
    assert list(runtime.reasoners)[0] == "chaseos-cloud"
    assert CLOUD_KEY_ENV not in __import__("os").environ


def test_a_reply_without_usage_fields_records_none_rather_than_guessing(gateway_factory) -> None:
    gateway = gateway_factory((200, {"choices": [{"message": {"content": "plain"}}]}))
    reply = ChaseOSCloudReasoner("k", base_url=gateway.url).complete("s", "t", timeout=10, cancel=Event())
    assert reply.credits is None and reply.usage is None


def test_model_can_be_chosen_from_the_environment():
    reasoner = ChaseOSCloudReasoner.from_environment({"CHASEOS_CLOUD_KEY": "k", "CHASEOS_CLOUD_MODEL": "@cf/zai-org/glm-5.3"})
    assert reasoner.model == "@cf/zai-org/glm-5.3"
    assert ChaseOSCloudReasoner.from_environment({"CHASEOS_CLOUD_KEY": "k"}).model == "chaseos/balanced"


def test_a_route_that_is_down_moves_on_to_the_next_chaseos_route(gateway_factory) -> None:
    # 12 Nov 2026: chaseos/balanced answered 502 and 503 while chaseos/deep and fast answered.
    down = {"error": {"code": "provider_temporarily_unavailable", "message": "The upstream provider failed. You were not charged."}}
    gateway = gateway_factory((503, down), (502, {}), answer('{"thought": "ok", "actions": []}'))
    reasoner = ChaseOSCloudReasoner("k", base_url=gateway.url, fallback=("chaseos/deep", "chaseos/fast"))
    reply = reasoner.complete("s", "t", timeout=20, cancel=Event())
    assert reply.text.startswith("{")
    assert [r["body"]["model"] for r in gateway.requests] == ["chaseos/balanced", "chaseos/balanced", "chaseos/deep"]
    assert all(r["body"]["response_format"] == {"type": "json_object"} for r in gateway.requests)


def test_every_route_down_says_what_the_gateway_said(gateway_factory) -> None:
    down = {"error": {"message": "The upstream provider failed. You were not charged."}}
    gateway = gateway_factory((409, down), (409, down), (409, down))
    with pytest.raises(ReasonerUnavailable) as caught:
        ChaseOSCloudReasoner("k", base_url=gateway.url, fallback=("chaseos/deep", "chaseos/fast")).complete("s", "t", timeout=20, cancel=Event())
    assert caught.value.code == "route_error" and "HTTP 409" in str(caught.value) and "You were not charged" in str(caught.value)
    assert [r["body"]["model"] for r in gateway.requests] == ["chaseos/balanced", "chaseos/deep", "chaseos/fast"]


def test_out_of_credits_never_moves_to_another_route(gateway_factory) -> None:
    gateway = gateway_factory((402, {"error": {"available": 0}}))
    with pytest.raises(ReasonerUnavailable) as caught:
        ChaseOSCloudReasoner("k", base_url=gateway.url, fallback=("chaseos/deep",)).complete("s", "t", timeout=10, cancel=Event())
    assert caught.value.code == "out_of_credits" and len(gateway.requests) == 1


def test_the_fallback_routes_come_from_the_environment_with_a_default():
    assert ChaseOSCloudReasoner.from_environment({"CHASEOS_CLOUD_KEY": "k"}).fallback == ("chaseos/deep", "chaseos/fast")
    assert ChaseOSCloudReasoner.from_environment({"CHASEOS_CLOUD_KEY": "k", "CHASEOS_CLOUD_FALLBACK": ""}).fallback == ()
    assert ChaseOSCloudReasoner.from_environment({"CHASEOS_CLOUD_KEY": "k", "CHASEOS_CLOUD_MODEL": "chaseos/deep"}).fallback == ("chaseos/fast",)

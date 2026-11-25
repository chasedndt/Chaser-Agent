"""The route ladder and its policy guard: which route may answer which job, the hand-over to
ChaseOS Cloud when an allowance runs out, the receipt, and a plan sign-in staying on this computer.

Stand-in routes and a local stand-in gateway prove the rules, not model quality.
"""

from __future__ import annotations

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Event

import pytest

from chaser_agent.agent import AgentRuntime, Toolbox, WorkflowSpec
from chaser_agent.agent import routes
from chaser_agent.agent.reasoners import (
    API_KEY_ENV, CLOUD_KEY_ENV, ApiKeyReasoner, ChaseOSCloudReasoner, CodexPlanReasoner, ReasonerReply, ReasonerUnavailable,
    provider_for, says_limit,
)

FAKE_CODEX = [sys.executable, str(Path(__file__).with_name("fake_codex.py"))]
SECRET = "plan-session-secret-7f3a"
FINAL = json.dumps({"thought": "done", "actions": [{"type": "final", "answer": "Done."}]})


class Route:
    """A stand-in route of a given kind. It answers, or stops with a given code."""

    def __init__(self, reasoner_id: str, kind: str, provider: str, *, fail: str | None = None, available: bool = True, credits: int | None = None) -> None:
        self.reasoner_id, self.label, self.route_kind, self.provider = reasoner_id, reasoner_id, kind, provider
        self.model = f"{reasoner_id}-model"
        self.fail, self.available, self.credits = fail, available, credits
        self.calls = 0

    def status(self) -> dict:
        return {"id": self.reasoner_id, "available": self.available, "reason": None if self.available else "not signed in"}

    def complete(self, system: str, transcript: str, *, timeout: float, cancel: Event) -> ReasonerReply:
        self.calls += 1
        if self.fail:
            raise ReasonerUnavailable(self.fail, f"{self.reasoner_id} stopped")
        usage = {"prompt_tokens": 100, "completion_tokens": 10}
        return ReasonerReply(FINAL, self.reasoner_id, self.model, 0.01, self.credits, usage)


def codex() -> Route:
    return Route("codex-plan", "plan", "openai")


def claude() -> Route:
    return Route("claude-cli", "plan", "anthropic")


def key(provider: str = "openai", **kwargs) -> Route:
    return Route("own-api-key", "api_key", provider, **kwargs)


def cloud(**kwargs) -> Route:
    return Route("chaseos-cloud", "cloud", "chaseos", credits=7, **kwargs)


def info(route: Route) -> routes.RouteInfo:
    return routes.route_info(route)


# --- the guard: every job kind against every route -----------------------------------------------------------------

ROUTES = {
    "chatgpt_plan": Route("codex-plan", "plan", "openai"),
    "claude_plan": Route("claude-cli", "plan", "anthropic"),
    "undeclared": Route("someone-elses", "unknown", "unknown"),
    "api_key": Route("own-api-key", "api_key", "openai"),
    "anthropic_key": Route("anthropic-key", "api_key", "anthropic"),
    "local": Route("ollama", "local", "ollama"),
    "cloud": Route("chaseos-cloud", "cloud", "chaseos"),
    "bridge": Route("bridge", "bridge", "external"),
}
JOBS = {
    "own_interactive": routes.Job("owner", True, "own"),
    "own_headless": routes.Job("owner", False, "own"),
    "client_interactive": routes.Job("client", True, "own"),
    "client_headless": routes.Job("client", False, "own"),
    "sale_headless": routes.Job("sale", False, "own"),
    "own_on_hosted": routes.Job("owner", True, "hosted"),
}
# Written out by hand from section 8 of the Cloud strategy, so the test does not restate the code.
ALLOWED = {
    "own_interactive":    {"chatgpt_plan", "claude_plan", "undeclared", "api_key", "anthropic_key", "local", "cloud", "bridge"},
    "own_headless":       {"chatgpt_plan", "undeclared", "api_key", "anthropic_key", "local", "cloud", "bridge"},
    "client_interactive": {"api_key", "anthropic_key", "local", "cloud"},
    "client_headless":    {"api_key", "anthropic_key", "local", "cloud"},
    "sale_headless":      {"api_key", "anthropic_key", "local", "cloud"},
    "own_on_hosted":      {"api_key", "anthropic_key", "local", "cloud", "bridge"},
}


@pytest.mark.parametrize("job_name", JOBS)
@pytest.mark.parametrize("route_name", ROUTES)
def test_the_guard_allows_each_route_only_for_the_jobs_section_8_names(job_name: str, route_name: str) -> None:
    decision = routes.check(JOBS[job_name], info(ROUTES[route_name]))
    assert decision.allowed is (route_name in ALLOWED[job_name])
    assert decision.reason and decision.explanation


def test_each_refusal_names_its_rule() -> None:
    assert routes.check(JOBS["client_interactive"], info(ROUTES["chatgpt_plan"])).reason == "plan_not_for_client_work"
    assert routes.check(JOBS["sale_headless"], info(ROUTES["chatgpt_plan"])).reason == "plan_not_for_client_work"
    assert routes.check(JOBS["own_headless"], info(ROUTES["claude_plan"])).reason == "claude_plan_interactive_only"
    assert routes.check(JOBS["own_on_hosted"], info(ROUTES["chatgpt_plan"])).reason == "plan_needs_own_machine"
    assert routes.check(JOBS["client_headless"], info(ROUTES["bridge"])).reason == "bridge_owner_only"
    assert routes.check(JOBS["own_headless"], info(ROUTES["chatgpt_plan"])).reason == "own_plan_own_work"
    assert routes.check(JOBS["client_headless"], info(ROUTES["cloud"])).reason == "chaseos_cloud"


def test_a_route_that_declares_nothing_is_treated_as_a_personal_sign_in() -> None:
    class Bare:
        reasoner_id = "bare"

    assert routes.route_info(Bare()).kind == "unknown"
    assert not routes.check(JOBS["client_headless"], routes.route_info(Bare())).allowed


def test_a_job_comes_from_the_caller_and_the_workflow_and_the_machine_from_the_service() -> None:
    assert routes.Job.from_request(None) == routes.Job("owner", False, "own")
    assert routes.Job.from_request({"work_for": "owner"}, workflow_work_for="client").work_for == "client"
    assert routes.Job.from_request({"work_for": "sale"}, workflow_work_for="client").work_for == "sale"
    with pytest.raises(ValueError):
        routes.Job.from_request({"machine": "own"})
    with pytest.raises(ValueError):
        routes.Job.from_request({"work_for": "friend"})
    with pytest.raises(ValueError):
        routes.Job.from_request({"interactive": "yes"})


# --- the ladder ----------------------------------------------------------------------------------------------------

def pick(job: routes.Job, *rows: Route, **kwargs) -> routes.Choice:
    return routes.choose({row.reasoner_id: row for row in rows}, job, **kwargs)


def test_own_work_takes_the_plan_first_then_a_key_then_cloud() -> None:
    assert pick(JOBS["own_headless"], cloud(), key(), codex()).route.reasoner_id == "codex-plan"
    assert pick(JOBS["own_headless"], cloud(), key(), Route("codex-plan", "plan", "openai", available=False)).route.reasoner_id == "own-api-key"
    assert pick(JOBS["own_headless"], cloud(), key(available=False)).route.reasoner_id == "chaseos-cloud"


def test_client_work_never_lands_on_a_plan_even_when_the_plan_is_ready() -> None:
    choice = pick(JOBS["client_interactive"], codex(), claude(), cloud())
    assert choice.route.reasoner_id == "chaseos-cloud"
    assert {row["reason"] for row in choice.passed_over} == {"plan_not_for_client_work"}
    assert pick(JOBS["sale_headless"], codex(), key(), cloud()).route.reasoner_id == "own-api-key"


def test_a_claude_plan_takes_interactive_work_only() -> None:
    assert pick(JOBS["own_interactive"], claude(), cloud()).route.reasoner_id == "claude-cli"
    headless = pick(JOBS["own_headless"], claude(), cloud())
    assert headless.route.reasoner_id == "chaseos-cloud"
    assert headless.passed_over[0]["reason"] == "claude_plan_interactive_only"


def test_an_anthropic_api_key_may_run_headless_and_client_work() -> None:
    assert pick(JOBS["client_headless"], claude(), key("anthropic")).route.reasoner_id == "own-api-key"


def test_the_owners_preferred_route_goes_first_but_still_meets_the_guard() -> None:
    preferred = Route("owner-selected", "unknown", "unknown")
    assert pick(JOBS["own_headless"], codex(), cloud(), preferred, preferred="owner-selected").route.reasoner_id == "owner-selected"
    assert pick(JOBS["client_headless"], codex(), cloud(), preferred, preferred="owner-selected").route.reasoner_id == "chaseos-cloud"


def test_a_route_asked_for_by_name_is_refused_outright_rather_than_swapped() -> None:
    with pytest.raises(routes.NoRoute) as refused:
        pick(JOBS["client_headless"], codex(), cloud(), requested="codex-plan")
    assert refused.value.code == "plan_not_for_client_work"


def test_with_nothing_allowed_and_ready_the_pick_says_why() -> None:
    with pytest.raises(routes.NoRoute) as none:
        pick(JOBS["client_headless"], codex(), cloud(available=False))
    assert none.value.code == "no_route"
    assert "plan_not_for_client_work" in none.value.message and "not signed in" in none.value.message


def test_a_fallback_only_moves_to_a_later_tier() -> None:
    rows = {r.reasoner_id: r for r in (codex(), claude(), key(), cloud())}
    after_plan = routes.choose(rows, JOBS["own_interactive"], after_tier=0, exclude=frozenset({"codex-plan"}))
    assert after_plan.route.reasoner_id == "own-api-key"  # not the other plan
    after_key = routes.choose(rows, JOBS["own_interactive"], after_tier=1, exclude=frozenset({"own-api-key"}))
    assert after_key.route.reasoner_id == "chaseos-cloud"
    with pytest.raises(routes.NoRoute):
        routes.choose(rows, JOBS["own_interactive"], after_tier=2, exclude=frozenset({"chaseos-cloud"}))


# --- the loop: limit-hit fallback and the receipt ------------------------------------------------------------------

def runtime_with(tmp_path: Path, *rows: Route, workflow: WorkflowSpec | None = None) -> AgentRuntime:
    runtime = AgentRuntime(tmp_path, toolbox=Toolbox(), reasoners=list(rows))
    runtime.add_workflow(workflow or WorkflowSpec("general", "General", "Help.", frozenset()))
    return runtime


def run(runtime: AgentRuntime, **kwargs) -> tuple[dict, list[dict]]:
    snapshot = runtime.create_session("Sort my notes.", **kwargs)
    runtime.wait(snapshot["id"], 20)
    return runtime.snapshot(snapshot["id"]), runtime.events(snapshot["id"])


def of(events: list[dict], kind: str) -> list[dict]:
    return [row["data"] for row in events if row["type"] == kind]


@pytest.mark.parametrize("code", sorted(routes.LIMIT_CODES))
def test_a_plan_that_hits_its_limit_hands_the_job_to_cloud_and_says_so(tmp_path: Path, code: str) -> None:
    plan, gateway = Route("codex-plan", "plan", "openai", fail=code), cloud()
    snapshot, events = run(runtime_with(tmp_path, plan, gateway))
    assert snapshot["status"] == "finished" and plan.calls == 1 and gateway.calls == 1
    assert of(events, "route_chosen")[0]["reasoner"] == "codex-plan"
    moved = of(events, "route_fallback")[0]
    assert moved["reasoner"] == "chaseos-cloud" and moved["fallback_from"]["code"] == code
    assert snapshot["steps_used"] == 1  # the stopped call isn't charged to the budget
    assert snapshot["route"]["reasoner"] == "chaseos-cloud"


def test_an_api_key_out_of_credit_also_hands_over_to_cloud(tmp_path: Path) -> None:
    snapshot, events = run(runtime_with(tmp_path, key(fail="out_of_credits"), cloud()), job={"work_for": "client"})
    assert snapshot["status"] == "finished"
    assert [row["reasoner"] for row in of(events, "route_chosen") + of(events, "route_fallback")] == ["own-api-key", "chaseos-cloud"]


def test_a_fault_that_is_not_a_used_up_allowance_stops_the_turn(tmp_path: Path) -> None:
    gateway = cloud()
    snapshot, events = run(runtime_with(tmp_path, Route("codex-plan", "plan", "openai", fail="route_error"), gateway))
    assert snapshot["status"] == "failed" and gateway.calls == 0 and not of(events, "route_fallback")


def test_cloud_out_of_credits_is_the_end_of_the_ladder(tmp_path: Path) -> None:
    snapshot, _ = run(runtime_with(tmp_path, cloud(fail="out_of_credits")))
    assert snapshot["status"] == "failed" and "stopped" in snapshot["error"]


def test_the_receipt_records_route_provider_model_reason_and_cost(tmp_path: Path) -> None:
    snapshot, events = run(runtime_with(tmp_path, codex(), cloud()), job={"work_for": "client", "interactive": True})
    chosen = of(events, "route_chosen")[0]
    assert chosen | {"passed_over": None} == {
        "reasoner": "chaseos-cloud", "kind": "cloud", "provider": "chaseos", "model": "chaseos-cloud-model",
        "reason": "chaseos_cloud", "explanation": chosen["explanation"], "passed_over": None,
        "job": {"work_for": "client", "interactive": True, "machine": "own"},
    }
    assert chosen["passed_over"] == [{"reasoner": "codex-plan", "kind": "plan", "reason": "plan_not_for_client_work"}]
    reply = of(events, "reasoner_reply")[0]
    assert (reply["route"], reply["route_kind"], reply["provider"], reply["model"], reply["guard_reason"]) == (
        "chaseos-cloud", "cloud", "chaseos", "chaseos-cloud-model", "chaseos_cloud")
    assert reply["cost"] == {"basis": "chaseos_credits", "credits": 7, "prompt_tokens": 100, "completion_tokens": 10}
    finished = of(events, "turn_finished")[0]
    assert finished["route"]["reason"] == "chaseos_cloud"
    assert finished["cost"] == {"credits": 7, "prompt_tokens": 100, "completion_tokens": 10, "bases": ["chaseos_credits"]}
    assert snapshot["job"]["work_for"] == "client" and snapshot["cost"]["credits"] == 7


def test_a_plan_reply_costs_the_plan_allowance_and_a_key_reply_its_tokens(tmp_path: Path) -> None:
    _, events = run(runtime_with(tmp_path / "plan", codex()))
    assert of(events, "reasoner_reply")[0]["cost"] == {"basis": "plan_allowance", "billed_by": "openai"}
    _, events = run(runtime_with(tmp_path / "key", key("anthropic")))
    assert of(events, "reasoner_reply")[0]["cost"] == {"basis": "provider_tokens", "billed_by": "anthropic", "prompt_tokens": 100, "completion_tokens": 10}


def test_a_refused_job_leaves_a_receipt_of_what_was_passed_over(tmp_path: Path) -> None:
    snapshot, events = run(runtime_with(tmp_path, claude()))
    assert snapshot["status"] == "failed"
    refused = of(events, "route_refused")[0]
    assert refused["code"] == "no_route" and refused["passed_over"][0]["reason"] == "claude_plan_interactive_only"


def test_a_client_workflow_cannot_be_run_as_the_owners_own_work(tmp_path: Path) -> None:
    client = WorkflowSpec("desk", "Desk", "Review.", frozenset(), triggers=("review",), work_for="client")
    runtime = runtime_with(tmp_path, codex(), cloud())
    runtime.add_workflow(client)
    snapshot = runtime.create_session("Review this tender.", job={"work_for": "owner", "interactive": True})
    runtime.wait(snapshot["id"], 20)
    assert runtime.snapshot(snapshot["id"])["job"]["work_for"] == "client"
    assert runtime.snapshot(snapshot["id"])["route"]["reasoner"] == "chaseos-cloud"


def test_a_hosted_service_never_uses_a_plan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CHASER_AGENT_MACHINE", "hosted")
    snapshot, _ = run(runtime_with(tmp_path, codex(), cloud()), job={"interactive": True})
    assert snapshot["job"]["machine"] == "hosted" and snapshot["route"]["reasoner"] == "chaseos-cloud"
    monkeypatch.setenv("CHASER_AGENT_MACHINE", "somewhere")
    with pytest.raises(ValueError):
        runtime_with(tmp_path / "x", cloud())


# --- the ChatGPT plan through Codex: its sign-in stays with Codex --------------------------------------------------

def test_codex_plan_runs_codex_on_its_chatgpt_sign_in_with_no_keys_in_its_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    log = tmp_path / "codex.jsonl"
    monkeypatch.setenv("FAKE_CODEX_LOG", str(log))
    for name in ("OPENAI_API_KEY", "CODEX_API_KEY", "OPENAI_BASE_URL", API_KEY_ENV, CLOUD_KEY_ENV):
        monkeypatch.setenv(name, "must-not-pass")
    route = CodexPlanReasoner(model="gpt-test", command=FAKE_CODEX)
    assert route.status()["available"] is True
    reply = route.complete("RULES", "TRANSCRIPT", timeout=30, cancel=Event())
    assert reply.route == "codex-plan" and reply.model == "gpt-test" and "ChatGPT plan" in reply.text
    rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    for row in rows:
        assert not {"OPENAI_API_KEY", "CODEX_API_KEY", "OPENAI_BASE_URL", API_KEY_ENV, CLOUD_KEY_ENV} & set(row["env"])
    run_args = rows[-1]["args"]
    assert run_args[0] == "exec" and 'forced_login_method="chatgpt"' in run_args and "--model" in run_args


def test_codex_signed_in_with_an_api_key_is_not_a_plan(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FAKE_CODEX_MODE", "apikey")
    state = CodexPlanReasoner(command=FAKE_CODEX).status()
    assert state["available"] is False and "API key" in state["reason"] and "sk-" not in state["reason"]
    assert CodexPlanReasoner(command=[]).status()["available"] is False


def test_codex_at_its_limit_says_so_without_repeating_anything_codex_printed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FAKE_CODEX_MODE", "limit")
    with pytest.raises(ReasonerUnavailable) as stopped:
        CodexPlanReasoner(command=FAKE_CODEX).complete("R", "T", timeout=30, cancel=Event())
    assert stopped.value.code == "plan_limit" and SECRET not in str(stopped.value)
    monkeypatch.setenv("FAKE_CODEX_MODE", "broken")
    with pytest.raises(ReasonerUnavailable) as broken:
        CodexPlanReasoner(command=FAKE_CODEX).complete("R", "T", timeout=30, cancel=Event())
    assert broken.value.code == "route_error" and SECRET not in str(broken.value)


def test_the_plan_programs_limit_wording_is_recognised() -> None:
    assert says_limit("You've hit your usage limit. Upgrade to Pro")
    assert says_limit("Claude AI usage limit reached|1764000000")
    assert says_limit("5-hour limit reached ∙ resets 3pm")
    assert says_limit("stream error: exceeded retry limit, last status: 429 Too Many Requests")
    assert says_limit("HTTP 429")
    assert not says_limit("model not found")
    assert not says_limit("request 4290 failed")


# --- the own-API-key route --------------------------------------------------------------------------------------------

class Gateway:
    def __init__(self, answers: list[tuple[int, dict]]) -> None:
        self.answers, self.requests = list(answers), []
        gateway = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:  # noqa: N802
                raw = self.rfile.read(int(self.headers["Content-Length"]))
                gateway.requests.append({"path": self.path, "headers": dict(self.headers), "raw": raw.decode("utf-8")})
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


def ok(text: str = FINAL, credits: int | None = None) -> tuple[int, dict]:
    body = {"model": "served-model", "choices": [{"message": {"content": text}}], "usage": {"prompt_tokens": 50, "completion_tokens": 5}}
    if credits is not None:
        body["chaseos"] = {"actual_credits": credits}
    return 200, body


@pytest.fixture
def gateways():
    made: list[Gateway] = []

    def make(*answers: tuple[int, dict]) -> Gateway:
        made.append(Gateway(list(answers)))
        return made[-1]

    yield make
    for gateway in made:
        gateway.server.shutdown()


def test_an_own_key_calls_the_providers_endpoint_with_that_key_only(gateways) -> None:
    gateway = gateways(ok())
    route = ApiKeyReasoner("own-key-1", model="their-model", base_url=gateway.url + "/v1", provider="openrouter")
    reply = route.complete("R", "T", timeout=10, cancel=Event())
    sent = gateway.requests[0]
    assert sent["path"] == "/v1/chat/completions" and sent["headers"]["Authorization"] == "Bearer own-key-1"
    assert "X-ChaseOS-Agent-Harness" not in sent["headers"]
    assert json.loads(sent["raw"])["model"] == "their-model"
    assert reply.route == "own-api-key" and reply.usage["prompt_tokens"] == 50 and reply.credits is None


@pytest.mark.parametrize(("status", "body", "code"), [
    (402, {}, "out_of_credits"),
    (429, {"error": {"code": "insufficient_quota", "message": "no quota"}}, "out_of_credits"),
    (429, {"error": {"code": "rate_limit_exceeded"}}, "rate_limited"),
    (401, {}, "not_authorised"),
    (400, {"error": {"message": "bad"}}, "route_error"),
])
def test_an_own_key_tells_a_used_up_allowance_from_a_fault(gateways, status: int, body: dict, code: str) -> None:
    route = ApiKeyReasoner("k", model="m", base_url=gateways((status, body)).url)
    with pytest.raises(ReasonerUnavailable) as stopped:
        route.complete("R", "T", timeout=10, cancel=Event())
    assert stopped.value.code == code


def test_an_own_key_is_taken_out_of_the_environment_and_needs_a_model() -> None:
    environ = {API_KEY_ENV: "own-key", "CHASER_API_BASE_URL": "https://api.anthropic.com/v1/"}
    route = ApiKeyReasoner.from_environment(environ)
    assert API_KEY_ENV not in environ and route.provider == "anthropic"
    assert route.status()["available"] is False and "CHASER_API_MODEL" in route.status()["reason"]
    assert provider_for("https://api.openai.com/v1") == "openai" and provider_for("https://llm.example.net/v1") == "llm.example.net"


# --- end to end: a plan at its limit hands over to Cloud, and nothing of the plan's sign-in travels ----------------

def test_plan_limit_to_cloud_sends_cloud_only_the_task_and_keeps_secrets_off_the_receipt(tmp_path: Path, gateways, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FAKE_CODEX_MODE", "limit")
    gateway = gateways(ok(credits=4))
    plan = CodexPlanReasoner(command=FAKE_CODEX)
    runtime = runtime_with(tmp_path, plan, ChaseOSCloudReasoner("cloud-key", base_url=gateway.url, fallback=()))
    snapshot, events = run(runtime)
    assert snapshot["status"] == "finished" and snapshot["route"]["fallback_from"]["code"] == "plan_limit"
    sent = gateway.requests[0]
    assert sent["headers"]["Authorization"] == "Bearer cloud-key"
    assert SECRET not in sent["raw"] and "codex" not in json.dumps(sent["headers"]).lower()
    receipt = (tmp_path / "agent" / "sessions" / snapshot["id"] / "events.jsonl").read_text(encoding="utf-8")
    assert SECRET not in receipt and "cloud-key" not in receipt
    assert of(events, "reasoner_reply")[0]["cost"]["credits"] == 4


# --- the real entry points: build_runtime's ladder, the HTTP service and `chaser_agent.cli ask` ----------------------

@pytest.fixture
def service(tmp_path: Path, gateways, monkeypatch: pytest.MonkeyPatch):
    from chaser_agent.agent.service import build_runtime
    from chaser_agent.local_http import create_server, load_or_create_token

    monkeypatch.setattr("chaser_agent.local_http.assert_private_runtime_path", lambda _path: None)
    monkeypatch.setattr("chaser_agent.agent_cli.read_private_control_token", lambda folder: (Path(folder) / "control-token").read_text(encoding="ascii").strip())
    gateway = gateways(ok(credits=3), ok(credits=3))
    monkeypatch.setenv(CLOUD_KEY_ENV, "cloud-key")
    monkeypatch.setenv("CHASEOS_CLOUD_BASE_URL", gateway.url)
    monkeypatch.setenv("CHASEOS_CLOUD_FALLBACK", "")
    monkeypatch.delenv(API_KEY_ENV, raising=False)
    runtime = build_runtime(tmp_path)
    runtime.reasoners["codex-plan"].command = FAKE_CODEX
    token, _ = load_or_create_token(tmp_path)
    server = create_server(data_dir=tmp_path, token=token, port=0, agent=runtime)
    threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()
    yield tmp_path, server.server_port, runtime, gateway
    server.shutdown()
    server.server_close()


def test_build_runtime_lays_out_the_ladder_and_takes_the_keys_out_of_the_environment(service) -> None:
    import os

    _, _, runtime, _ = service
    assert [r.reasoner_id for r in routes.ladder(runtime.reasoners.values())] == ["codex-plan", "claude-cli", "own-api-key", "chaseos-cloud"]
    assert CLOUD_KEY_ENV not in os.environ


def test_the_cli_runs_client_work_on_cloud_and_prints_the_route(service, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    from chaser_agent.cli import main

    data_dir, port, runtime, gateway = service
    code = main(["ask", "--data-dir", str(data_dir), "--port", str(port), "--for", "client", "Summarise this tender."])
    printed = capsys.readouterr().out
    assert code == 0, printed
    assert "[route] chaseos-cloud · cloud · chaseos · chaseos_cloud" in printed
    session = runtime.list_sessions()[0]
    assert runtime.snapshot(session["id"])["job"] == {"work_for": "client", "interactive": True, "machine": "own"}
    assert len(gateway.requests) == 1


def test_the_cli_runs_own_headless_work_on_the_plan_until_its_limit_then_on_cloud(service, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    from chaser_agent.cli import main

    data_dir, port, runtime, gateway = service
    monkeypatch.setenv("FAKE_CODEX_MODE", "ok")
    assert main(["ask", "--data-dir", str(data_dir), "--port", str(port), "--headless", "Sort my notes."]) == 0
    assert "[route] codex-plan · plan · openai · own_plan_own_work" in capsys.readouterr().out
    assert not gateway.requests
    monkeypatch.setenv("FAKE_CODEX_MODE", "limit")
    assert main(["ask", "--data-dir", str(data_dir), "--port", str(port), "--headless", "Sort my notes again."]) == 0
    printed = capsys.readouterr().out
    assert "[route] codex-plan stopped (plan_limit), so chaseos-cloud took over · chaseos_cloud" in printed
    assert SECRET not in printed and len(gateway.requests) == 1


def test_the_status_page_names_each_routes_rung(tmp_path: Path) -> None:
    import time

    runtime = runtime_with(tmp_path, codex(), cloud())
    runtime.status()
    for _ in range(200):
        if runtime._status_cache["checked_at"]:
            break
        time.sleep(0.05)
    rows = {row["id"]: row for row in runtime.status()["reasoners"]["routes"]}
    assert (rows["codex-plan"]["kind"], rows["codex-plan"]["provider"]) == ("plan", "openai")
    assert rows["chaseos-cloud"]["kind"] == "cloud"


def test_a_reply_refused_for_its_format_still_counts_toward_the_cost(tmp_path: Path) -> None:
    class Sloppy(Route):
        def complete(self, system, transcript, *, timeout, cancel):
            self.calls += 1
            text = "not json" if self.calls == 1 else FINAL
            return ReasonerReply(text, self.reasoner_id, self.model, 0.01, 2, {"prompt_tokens": 10, "completion_tokens": 1})

    snapshot, _ = run(runtime_with(tmp_path, Sloppy("chaseos-cloud", "cloud", "chaseos")))
    assert snapshot["status"] == "finished" and snapshot["cost"]["credits"] == 4

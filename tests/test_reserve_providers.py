"""Reserve providers: up to four backups tried in order when the main key or provider fails, recorded in the receipt."""

from __future__ import annotations

import json
from threading import Event

import pytest

from chaser_agent import chaser_cli, chaser_home
from chaser_agent.agent import AgentRuntime, Toolbox, WorkflowSpec
from chaser_agent.agent.reasoners import ReasonerReply, ReasonerUnavailable, ReserveChain
from chaser_agent.agent.service import ordered_routes

FINAL = json.dumps({"thought": "t", "actions": [{"type": "final", "answer": "Done."}]})


class Route:
    def __init__(self, rid: str, *, fails: str | None = None, available: bool = True) -> None:
        self.reasoner_id, self.label, self.fails, self.available, self.calls = rid, rid.title(), fails, available, 0

    def status(self):
        return {"id": self.reasoner_id, "label": self.label, "available": self.available, "reason": None if self.available else "no key"}

    def complete(self, system, transcript, *, timeout, cancel):
        self.calls += 1
        if self.fails:
            raise ReasonerUnavailable(self.fails, f"{self.label} said {self.fails}")
        return ReasonerReply(FINAL, self.reasoner_id, "m", 0.1)


def test_a_dead_main_key_moves_to_the_first_reserve_and_says_why() -> None:
    main, first, second = Route("cloud", fails="not_authorised"), Route("openrouter"), Route("openai")
    reply = ReserveChain(main, [first, second]).complete("s", "t", timeout=5, cancel=Event())
    assert reply.route == "openrouter" and second.calls == 0
    assert reply.fallbacks == ("Cloud: Cloud said not_authorised",)


@pytest.mark.parametrize("code", ["out_of_credits", "plan", "route_error", "timeout", "bad_output"])
def test_every_kind_of_failure_moves_on(code: str) -> None:
    assert ReserveChain(Route("cloud", fails=code), [Route("groq")]).complete("s", "t", timeout=5, cancel=Event()).route == "groq"


def test_a_cancel_never_moves_on() -> None:
    reserve = Route("groq")
    with pytest.raises(ReasonerUnavailable) as caught:
        ReserveChain(Route("cloud", fails="cancelled"), [reserve]).complete("s", "t", timeout=5, cancel=Event())
    assert caught.value.code == "cancelled" and reserve.calls == 0


def test_an_unavailable_reserve_is_skipped_and_all_failing_lists_each_reason() -> None:
    chain = ReserveChain(Route("cloud", fails="route_error"), [Route("openai", available=False), Route("groq", fails="timeout")])
    with pytest.raises(ReasonerUnavailable) as caught:
        chain.complete("s", "t", timeout=5, cancel=Event())
    text = str(caught.value.message)
    assert "Cloud said route_error" in text and "Openai: no key" in text and "Groq said timeout" in text


def test_status_is_available_when_only_a_reserve_is_and_lists_them() -> None:
    state = ReserveChain(Route("cloud", available=False), [Route("groq")]).status()
    assert state["available"] and "Reserve Groq will answer" in state["reason"] and state["reserves"][0]["available"]


def test_no_more_than_four_reserves() -> None:
    assert len(ReserveChain(Route("a"), [Route(str(i)) for i in range(6)]).reserves) == 4


def test_the_receipt_records_that_a_reserve_answered(tmp_path) -> None:
    chain = ReserveChain(Route("cloud", fails="plan"), [Route("groq")])
    agent = AgentRuntime(tmp_path, toolbox=Toolbox(), reasoners=[chain])
    agent.add_workflow(WorkflowSpec("general", "General", "Help.", frozenset(), max_steps=3))
    session = agent.create_session("hi")
    agent.wait(session["id"])
    reply = next(e["data"] for e in agent.events(session["id"]) if e["type"] == "reasoner_reply")
    assert reply["route"] == "groq" and reply["fallbacks"] == ["Cloud: Cloud said plan"]


def test_settings_reserves_wrap_the_main_route_with_keys_from_the_store_only() -> None:
    settings = {**chaser_home.defaults(), "provider": "openrouter", "model": "openrouter/auto",
                "reserves": [{"provider": "ollama", "model": "llama3.2"}, {"provider": "chaseos-cloud", "model": "chaseos/fast"}, {"provider": "bridge"}]}
    first = ordered_routes(settings=settings)[0]
    assert isinstance(first, ReserveChain) and first.reasoner_id == "openrouter"
    assert [r.reasoner_id for r in first.reserves] == ["ollama", "chaseos-cloud"] and first.reserves[1].model == "chaseos/fast"
    assert "key" not in json.dumps(settings["reserves"])
    assert not isinstance(ordered_routes(settings=chaser_home.defaults())[0], ReserveChain)


def test_reserve_remove_and_clear(capsys) -> None:
    chaser_home.save({"reserves": [{"provider": "groq", "model": "a"}, {"provider": "ollama", "model": "b"}]})
    assert chaser_cli.main(["model", "reserve", "remove", "1"]) == 0
    assert chaser_home.load()["reserves"] == [{"provider": "ollama", "model": "b"}]
    assert chaser_cli.main(["model", "reserve", "list"]) == 0 and "Ollama" in capsys.readouterr().out
    assert chaser_cli.main(["model", "reserve", "clear"]) == 0 and chaser_home.load()["reserves"] == []

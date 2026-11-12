"""Choosing how Chaser thinks: the provider list, keys per provider, the general route, and the new screens."""

from __future__ import annotations

import os

import pytest

from chaser_agent import chaser_cli, chaser_home, model_providers, terminal_theme, terminal_ui
from chaser_agent.agent.reasoners import ChaseOSCloudReasoner, OpenAICompatibleReasoner
from chaser_agent.agent.service import ordered_routes


def test_chaseos_cloud_leads_the_list_and_every_provider_is_reachable() -> None:
    assert model_providers.CATALOGUE[0].id == "chaseos-cloud"
    ids = [p.id for p in model_providers.CATALOGUE]
    assert len(ids) == len(set(ids))
    for provider in model_providers.CATALOGUE:
        if provider.kind == "openai" and provider.id != "custom":
            assert provider.base_url.startswith(("https://", "http://127.0.0.1")), provider.id
    assert model_providers.get("nonsense").id == "chaseos-cloud"


def test_the_chosen_provider_describes_itself_and_uses_its_own_address() -> None:
    settings = {**chaser_home.defaults(), "provider": "openrouter", "model": "openrouter/auto"}
    provider, model, base = model_providers.chosen(settings)
    assert (provider.label, model, base) == ("OpenRouter", "openrouter/auto", "https://openrouter.ai/api/v1")
    assert model_providers.describe(settings) == "OpenRouter · openrouter/auto"
    custom = {**settings, "provider": "custom", "base_url": "http://gateway.local/v1/", "model": "m"}
    assert model_providers.chosen(custom)[2] == "http://gateway.local/v1"


def test_a_key_in_the_providers_variable_wins_and_none_means_none() -> None:
    assert model_providers.load_key("openai", {"OPENAI_API_KEY": " sk-test-123456 "}) == ("sk-test-123456", "environment")
    assert model_providers.load_key("groq", {}) == ("", "none")


@pytest.mark.skipif(os.name != "nt", reason="keys are saved with Windows' per-user encryption")
def test_a_provider_key_is_saved_encrypted_and_never_in_plain_text() -> None:
    model_providers.save_key("deepseek", "sk-test-abcdefgh")
    raw = (chaser_home.home() / "keys" / "deepseek.dpapi").read_text(encoding="ascii")
    assert "sk-test" not in raw and "sk-test".encode("utf-16-le").hex() not in raw
    assert model_providers.load_key("deepseek", {}) == ("sk-test-abcdefgh", "saved")
    assert model_providers.forget_key("deepseek") and model_providers.load_key("deepseek", {}) == ("", "none")


def test_the_general_route_says_what_is_missing_and_calls_the_providers_own_endpoint() -> None:
    route = OpenAICompatibleReasoner("openai", "OpenAI", base_url="https://api.openai.com/v1/", model="", key="")
    assert route.status()["available"] is False and "chaser model" in route.status()["reason"]
    local = OpenAICompatibleReasoner("ollama", "Ollama", base_url="http://127.0.0.1:11434/v1", model="llama", needs_key=False)
    assert local.status()["available"] is True
    assert local._endpoint() == "http://127.0.0.1:11434/v1/chat/completions" and "Authorization" not in local._headers()
    assert ChaseOSCloudReasoner("k" * 12)._endpoint().endswith("/api/cloud/v1/chat/completions")


def test_the_route_taken_from_the_environment_leaves_it() -> None:
    environ = {"GROQ_API_KEY": "gsk-test-123456"}
    route = OpenAICompatibleReasoner.from_settings({**chaser_home.defaults(), "provider": "groq", "model": "x"}, environ)
    assert route.status()["available"] and "GROQ_API_KEY" not in environ and route.key_source == "environment"


def test_the_chosen_provider_comes_first_so_auto_uses_it() -> None:
    first = lambda provider: ordered_routes(settings={**chaser_home.defaults(), "provider": provider, "model": "m"})[0].reasoner_id  # noqa: E731
    assert first("openrouter") == "openrouter" and first("claude-cli") == "claude-cli" and first("") == "chaseos-cloud"
    assert [r.reasoner_id for r in ordered_routes(settings=chaser_home.defaults())][-1] == "bridge"


def test_chaser_model_set_saves_without_asking(capsys) -> None:
    assert chaser_cli.main(["model", "set", "ollama", "--model", "llama3.2"]) == 0
    assert chaser_home.load()["provider"] == "ollama" and chaser_home.load()["model"] == "llama3.2"
    assert "Ollama" in capsys.readouterr().out


def test_help_lists_every_command_the_parser_has(capsys) -> None:
    assert chaser_cli.main(["help"]) == 0
    text = capsys.readouterr().out
    parser = chaser_cli.build_parser()
    commands = next(a for a in parser._subparsers._group_actions).choices  # noqa: SLF001
    missing = [name for name in commands if name not in {"tui", "reasoner", "agent-status", "decide"} and f"chaser {name}" not in text]
    assert not missing, missing


def test_the_frame_fits_its_width_with_colour_and_the_words_survive_without() -> None:
    lines = terminal_theme.box(["hello", terminal_theme.paint("teal", "teal")], 30, title=terminal_theme.gradient("Chaser"))
    assert {terminal_theme.visible(line) for line in lines} == {30}
    assert terminal_theme.paint("x", "warn", colour=False) == "x" and terminal_theme.visible("\033[1;38;2;1;2;3mab\033[0m") == 2
    assert terminal_theme.code("39e6d2", full=False) == "\033[38;5;{}m".format(terminal_theme._cube("39e6d2"))


def test_groups_show_as_headings_and_the_footer_names_its_keys() -> None:
    items = [terminal_ui.Item("c", "Chat", group="Work"), terminal_ui.Item("m", "Model", "auto", "Set up")]
    text = terminal_ui.render("", items, 0, [], lambda t, _tone: t, footer="? all commands   q quit")
    assert "WORK" in text and "SET UP" in text and "? all commands" in text


def test_sign_ins_and_harnesses_sit_under_advanced_and_first_run_offers_keys_only() -> None:
    groups = {p.id: model_providers.group(p) for p in model_providers.CATALOGUE}
    assert groups["chaseos-cloud"] == "Recommended" and groups["claude-cli"] == groups["bridge"] == "Advanced"
    assert groups["ollama"] == "On this computer" and groups["openrouter"] == "Bring your own key"
    offered = {p.id for p in model_providers.byok()}
    assert "claude-cli" not in offered and "bridge" not in offered and "chaseos-cloud" not in offered and {"openai", "ollama"} <= offered


def test_first_run_asks_what_powers_chaser_with_two_choices(monkeypatch: pytest.MonkeyPatch) -> None:
    seen = []

    def pick(title, items, **kwargs):
        seen.append([i.label for i in items])
        return "2" if len(seen) == 1 else None

    monkeypatch.setattr(terminal_ui, "select", pick)
    monkeypatch.setattr(chaser_cli, "interactive_terminal", lambda: True)
    chaser_cli.step_power(chaser_home.defaults())
    assert seen[0] == ["ChaseOS Cloud", "Bring your own key (BYOK)"]
    assert "Claude (Claude Code sign-in)" not in seen[1] and "OpenRouter" in seen[1]


def test_get_a_key_opens_the_account_page(monkeypatch: pytest.MonkeyPatch) -> None:
    opened = []
    monkeypatch.setattr(terminal_ui, "select", lambda *a, **k: "2")
    monkeypatch.setattr(chaser_cli, "interactive_terminal", lambda: True)
    monkeypatch.setattr(chaser_cli, "confirm", lambda *a, **k: False)
    monkeypatch.setattr("webbrowser.open", lambda url: opened.append(url) or True)
    monkeypatch.setattr(chaser_cli.cloud_key, "describe", lambda *a, **k: {"source": "none"})
    assert chaser_cli.cloud_key_step(chaser_home.defaults()) is False and opened == ["https://chaseos.ai/account"]


def test_a_409_reads_as_a_plan_problem_and_the_route_stops_saying_ready() -> None:
    from chaser_agent import cloud_key
    from threading import Event

    from chaser_agent.agent.reasoners import ReasonerUnavailable

    assert "plan or allowance" in cloud_key.PLAN_PROBLEM and "chaser key add" in cloud_key.PLAN_PROBLEM
    route = ChaseOSCloudReasoner("k" * 12)
    route._post = lambda body, timeout: (409, {"error": {"message": "This key has no allowance left on its plan"}})
    with pytest.raises(ReasonerUnavailable) as caught:
        route.complete("s", "t", timeout=5, cancel=Event())
    assert caught.value.code == "plan" and route.status()["available"] is False and "plan or allowance" in route.status()["reason"]
    route.set_key("n" * 12)
    assert route.status()["available"] is True


def test_a_remembered_refusal_still_lets_a_try_through_and_success_clears_it() -> None:
    from threading import Event

    route = ChaseOSCloudReasoner("k" * 12)
    route._post = lambda body, timeout: (409, {"error": {"code": "plan_allowance_exceeded"}})
    with pytest.raises(Exception):
        route.complete("s", "t", timeout=5, cancel=Event())
    assert route.status()["available"] is False
    route._post = lambda body, timeout: (200, {"choices": [{"message": {"content": "{}"}}]})
    route.complete("s", "t", timeout=5, cancel=Event())
    assert route.status()["available"] is True
    route.refused, route.refused_at = "old", 0.0
    assert route.status()["available"] is True  # forgotten after ten minutes

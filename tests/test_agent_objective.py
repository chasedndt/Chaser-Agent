"""The objective check: a turn that hasn't achieved what was asked may not stop early.

Scripted replies stand in for the model, so each case is exact. The tools are real registrations
whose outputs say what a search found.
"""

from __future__ import annotations

import json
from pathlib import Path

from chaser_agent.agent import AgentRuntime, AgentTool, Toolbox, WorkflowSpec
from chaser_agent.agent import objective
from chaser_agent.agent.reasoners import ScriptedReasoner


def reply(thought: str, *actions: dict) -> str:
    return json.dumps({"thought": thought, "actions": list(actions)})


def tool(tool_id: str, /, **args: object) -> dict:
    return {"type": "tool", "tool": tool_id, "args": args}


def final(answer: str) -> dict:
    return {"type": "final", "answer": answer}


def ask(question: str) -> dict:
    return {"type": "ask_human", "question": question, "kind": "missing_information"}


def runtime(data_dir: Path, replies: list[str], *, check: bool = True) -> AgentRuntime:
    toolbox = Toolbox()
    graph = {"HarborDesk": [{"reference": "apps#harbordesk", "title": "HarborDesk"}]}

    def search(args: dict, _context: object) -> dict:
        query = str(args.get("query", ""))
        hits = [] if args.get("namespace") == "Wrong" else graph.get(query, [])
        return {"query": query, "results": hits}

    def node(args: dict, _context: object) -> dict:
        return {"reference": args["reference"], "text": "HarborDesk is Example Co's go-between between readers and independent writers."}

    toolbox.register(AgentTool("graph_search", "Search.", {"properties": {"query": {"type": "string"}, "namespace": {"type": "string"}}, "required": ["query"]}, "read_only", search))
    toolbox.register(AgentTool("graph_node", "Read.", {"properties": {"reference": {"type": "string"}}, "required": ["reference"]}, "read_only", node))
    rt = AgentRuntime(data_dir, toolbox=toolbox, reasoners=[ScriptedReasoner(replies)])
    rt.add_workflow(WorkflowSpec("general", "Knowledge", "Help.", frozenset({"graph_search", "graph_node"}), max_steps=10, objective_check=check))
    return rt


def run(rt: AgentRuntime, message: str) -> dict:
    session = rt.create_session(message)
    rt.wait(session["id"])
    return rt.snapshot(session["id"])


def test_asking_after_one_empty_search_is_sent_back_to_work(tmp_path: Path) -> None:
    rt = runtime(tmp_path, [
        reply("Search it.", tool("graph_search", query="HarborDesk", namespace="Wrong")),
        reply("Nothing found.", ask("Could you give me more context?")),
        reply("Search everywhere.", tool("graph_search", query="HarborDesk")),
        reply("Read it.", tool("graph_node", reference="apps#harbordesk")),
        reply("Done.", final("HarborDesk is Example Co's go-between between readers and writers.")),
    ])
    snap = run(rt, "What is HarborDesk?")
    assert snap["status"] == "finished"
    assert snap["objective"]["met"] is True
    events = rt.events(snap["id"])
    checks = [e["data"] for e in events if e["type"] == "objective_checked"]
    assert [c["decision"] for c in checks] == ["retry", "stop"]
    assert "came back empty" in " ".join(checks[0]["shortfalls"])
    assert not any(e["type"] == "question_asked" for e in events)


def test_a_turn_that_never_gets_there_says_it_failed(tmp_path: Path) -> None:
    rt = runtime(tmp_path, [reply("Guess.", final("It is probably a desk.")) for _ in range(3)])
    snap = run(rt, "What is HarborDesk?")
    assert snap["status"] == "finished"
    assert snap["objective"]["met"] is False
    assert snap["objective"]["score"] < objective.THRESHOLD
    finished = [e["data"] for e in rt.events(snap["id"]) if e["type"] == "turn_finished"][-1]
    assert finished["objective"]["met"] is False


def test_workflows_without_the_check_are_unchanged(tmp_path: Path) -> None:
    rt = runtime(tmp_path, [reply("Guess.", final("It is probably a desk."))], check=False)
    snap = run(rt, "What is HarborDesk?")
    assert snap["status"] == "finished" and snap["objective"] is None


def test_score_rewards_evidence_and_penalises_giving_up() -> None:
    goal = "What is HarborDesk?\n\n---\nContext from Chat: unrelated words"
    assert objective.key_terms(goal) == {"harbor", "desk"}
    empty = [{"role": "observation", "tool": "graph_search", "status": "ok", "text": json.dumps({"results": []})}]
    gave_up = objective.assess(goal, empty, ending="ask", answer="More context?")
    assert gave_up.features["deferred_early"] == 1.0 and not gave_up.met
    evidence = [
        {"role": "observation", "tool": "graph_search", "status": "ok", "text": json.dumps({"results": [{"title": "HarborDesk"}]})},
        {"role": "observation", "tool": "graph_node", "status": "ok", "text": "HarborDesk keeps harbor desk."},
    ]
    done = objective.assess(goal, evidence, ending="final", answer="HarborDesk is Example Co's harbor desk service.")
    assert done.met and done.score > gave_up.score
    expected = objective.sigmoid(objective.BIAS + sum(objective.WEIGHTS[k] * v for k, v in done.features.items()))
    assert abs(done.score - expected) < 1e-12


def test_route_text_keeps_attached_context_from_choosing_the_workflow(tmp_path: Path) -> None:
    rt = runtime(tmp_path, [reply("Done.", final("ok"))], check=False)
    rt.add_workflow(WorkflowSpec("reviews", "Reviews", "Review.", frozenset(), triggers=("draft review",)))
    message = "What is this business?\n\n---\nAttached: draft reviews now follow the page"
    assert rt.route_workflow(message).workflow_id == "reviews"
    snap = rt.create_session(message, route_text="What is this business?", start=False)
    assert snap["workflow"] == "general"

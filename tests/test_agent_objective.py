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


PAGE = objective.Requirement(r"(?i)harbor\s?desk", "web_fetch", r"example\.com", "read the product's own page")


def runtime_with_page(data_dir: Path, replies: list[str]) -> AgentRuntime:
    rt = runtime(data_dir, replies)
    fetched: list[str] = []

    def fetch(args: dict, _context: object) -> dict:
        fetched.append(args["url"])
        return {"url": args["url"], "text": "HarborDesk is the go-between for readers and independent writers."}

    rt.toolbox.register(AgentTool("web_fetch", "Fetch.", {"properties": {"url": {"type": "string"}}, "required": ["url"]}, "read_only", fetch))
    rt.add_workflow(WorkflowSpec("general", "Knowledge", "Help.", frozenset({"graph_search", "graph_node", "web_fetch"}), max_steps=10,
                                 objective_check=True, objective_requires=(PAGE,)))
    return rt


def test_a_required_source_must_be_read_before_the_turn_can_stop(tmp_path: Path) -> None:
    rt = runtime_with_page(tmp_path, [
        reply("Search.", tool("graph_search", query="HarborDesk")),
        reply("Read.", tool("graph_node", reference="apps#harbordesk")),
        reply("Done.", final("HarborDesk is Example Co's go-between between readers and writers.")),
        reply("Read its page.", tool("web_fetch", url="https://example.com/harbordesk/")),
        reply("Done.", final("HarborDesk is Example Co's go-between between readers and independent writers.")),
    ])
    snap = run(rt, "What is HarborDesk?")
    checks = [e["data"] for e in rt.events(snap["id"]) if e["type"] == "objective_checked"]
    assert [c["decision"] for c in checks] == ["retry", "stop"]
    assert "product's own page" in checks[0]["shortfalls"][0]
    assert checks[0]["features"]["required_missing"] == 1.0 and checks[0]["score"] < objective.THRESHOLD
    assert snap["objective"]["met"] is True and snap["objective"]["features"]["required_missing"] == 0.0


def test_a_requirement_only_applies_to_requests_it_names(tmp_path: Path) -> None:
    verdict = objective.assess("What is the weather?", [], ending="final", answer="x", requires=(PAGE,))
    assert verdict.features["required_missing"] == 0.0
    missing = objective.assess("What is HarborDesk?", [], ending="final", answer="x", requires=(PAGE,), calls=[
        {"tool": "web_fetch", "args": {"url": "https://other.example.org/"}, "status": "ok"}])
    assert missing.features["required_missing"] == 1.0


# --- Claim check against the authoritative source, and the best attempt ---

IDENTITY = objective.Requirement(
    r"(?i)harbor\s?desk", r"graph_node|web_fetch", r"#business:|example\.com",
    "read HarborDesk's business record or page",
    contradicts=r"(?i)shipping orders|\bHarborDesk (?:publishes|sells|submits work)\b",
    source="HarborDesk's business record (a go-between for readers and independent writers that never publishes)",
)
WRONG = "HarborDesk is a project that manages shipping orders and a desk queue."
RIGHT = "HarborDesk is the go-between for readers and independent writers; it never publishes."


def identity_runtime(data_dir: Path, replies: list[str]) -> AgentRuntime:
    rt = runtime(data_dir, replies)
    rt.toolbox.register(AgentTool("web_fetch", "Fetch.", {"properties": {"url": {"type": "string"}}, "required": ["url"]}, "read_only",
                                  lambda args, _c: {"url": args["url"], "text": RIGHT}))
    rt.add_workflow(WorkflowSpec("general", "Knowledge", "Help.", frozenset({"graph_search", "graph_node", "web_fetch"}), max_steps=12,
                                 objective_check=True, objective_requires=(IDENTITY,)))
    return rt


def test_the_harbordesk_failure_cannot_stop_until_the_claim_is_corrected(tmp_path: Path) -> None:
    rt = identity_runtime(tmp_path, [
        reply("Search.", tool("graph_search", query="HarborDesk")),
        reply("Read.", tool("graph_node", reference="apps#business:harbordesk")),
        reply("Answer.", final(WRONG)),
        reply("Correct it.", final(RIGHT)),
    ])
    snap = run(rt, "What is HarborDesk?")
    checks = [e["data"] for e in rt.events(snap["id"]) if e["type"] == "objective_checked"]
    assert [c["decision"] for c in checks] == ["retry", "stop"]
    assert checks[0]["met"] is False and "shipping orders" in checks[0]["shortfalls"][0]
    assert snap["final_answer"] == RIGHT and snap["objective"]["met"] is True


def test_a_contradiction_still_fails_the_turn_when_retries_run_out(tmp_path: Path) -> None:
    rt = identity_runtime(tmp_path, [
        reply("Search.", tool("graph_search", query="HarborDesk")),
        reply("Read.", tool("graph_node", reference="apps#business:harbordesk")),
    ] + [reply("Answer.", final(WRONG)) for _ in range(3)])
    snap = run(rt, "What is HarborDesk?")
    assert snap["status"] == "finished" and snap["objective"]["met"] is False
    assert snap["objective"]["calibrated"] is False and snap["objective"]["basis"].startswith("process heuristic")


def test_the_business_record_or_the_page_both_count_as_the_source(tmp_path: Path) -> None:
    by_record = objective.assess("What is HarborDesk?", [], ending="final", answer=RIGHT, requires=(IDENTITY,),
                                 calls=[{"tool": "graph_node", "args": {"reference": "apps#business:x"}, "status": "ok"}])
    by_page = objective.assess("What is HarborDesk?", [], ending="final", answer=RIGHT, requires=(IDENTITY,),
                               calls=[{"tool": "web_fetch", "args": {"url": "https://example.com/harbordesk/"}, "status": "ok"}])
    build_only = objective.assess("What is HarborDesk?", [], ending="final", answer=RIGHT, requires=(IDENTITY,),
                                  calls=[{"tool": "graph_node", "args": {"reference": "apps#implementation:x"}, "status": "ok"}])
    assert by_record.features["required_missing"] == 0.0 == by_page.features["required_missing"]
    assert build_only.features["required_missing"] == 1.0


def test_when_retries_run_out_it_keeps_the_best_attempt_not_the_last(tmp_path: Path) -> None:
    # The product's record is never read, so every attempt fails the identity requirement. The first,
    # a finished answer, scores about 0.35; the two later questions, asked early, score far lower.
    rt = identity_runtime(tmp_path, [
        reply("Search.", tool("graph_search", query="HarborDesk")),
        reply("Read a build record.", tool("graph_node", reference="apps#implementation:harbordesk")),
        reply("Answer.", final(RIGHT)),
        reply("Ask.", ask("What do you mean?")),
        reply("Ask.", ask("Which one?")),
    ])
    snap = run(rt, "What is HarborDesk?")
    checks = [e["data"] for e in rt.events(snap["id"]) if e["type"] == "objective_checked"]
    assert [c["decision"] for c in checks] == ["retry", "retry", "stop"]
    assert snap["status"] == "finished" and snap["final_answer"] == RIGHT
    assert snap["objective"]["chosen_from_earlier_attempt"] is True and snap["objective"]["met"] is False


def test_every_required_source_is_a_gate_even_when_the_score_is_high() -> None:
    page = objective.Requirement(r"(?i)harbor\s?desk", "web_fetch", r"example\.com", "read the product's own page")
    calls = [{"tool": "graph_search", "args": {"query": "HarborDesk"}, "status": "ok"},
             {"tool": "graph_node", "args": {"reference": "apps#business:x"}, "status": "ok"}]
    turn = [{"role": "observation", "tool": "graph_search", "status": "ok", "text": json.dumps({"results": [{"t": 1}]})},
            {"role": "observation", "tool": "graph_node", "status": "ok", "text": RIGHT}]
    verdict = objective.assess("What is HarborDesk?", turn, ending="final", answer=RIGHT, calls=calls, requires=(page, IDENTITY))
    assert verdict.score >= objective.THRESHOLD and verdict.met is False
    assert verdict.features["required_missing"] == 0.5


# --- The opt-in claim verifier: sources read this turn, contradictions only, quotes checked ---

RECORD_TEXT = "HarborDesk reviews go to independent writers; it never publishes or sells."
SLIP = "The review tells the reader whether the draft fits."


def verifier_runtime(data_dir: Path, replies: list[str], verifier) -> AgentRuntime:
    rt = runtime(data_dir, replies)
    rt.toolbox._tools["graph_node"] = AgentTool("graph_node", "Read.", {"properties": {"reference": {"type": "string"}}, "required": ["reference"]},
                                                "read_only", lambda args, _c: {"reference": args["reference"], "text": RECORD_TEXT})
    rt.add_workflow(WorkflowSpec("general", "Knowledge", "Help.", frozenset({"graph_search", "graph_node"}), max_steps=12,
                                 objective_check=True, objective_verifier=verifier))
    return rt


def finds_slip(goal, answer, sources, complete):
    if SLIP in answer:
        return [{"sentence": SLIP, "source_quote": "reviews go to independent writers"}]
    return []


def test_a_contradicted_sentence_sends_the_turn_back_with_the_source_quote(tmp_path: Path) -> None:
    good = "HarborDesk is the go-between for readers and independent writers; reviews go to the writer."
    rt = verifier_runtime(tmp_path, [
        reply("Search.", tool("graph_search", query="HarborDesk")),
        reply("Read.", tool("graph_node", reference="apps#harbordesk")),
        reply("Answer.", final("HarborDesk is the go-between. " + SLIP)),
        reply("Fix.", final(good)),
    ], finds_slip)
    snap = run(rt, "What is HarborDesk?")
    checks = [e["data"] for e in rt.events(snap["id"]) if e["type"] == "objective_checked"]
    assert [c["decision"] for c in checks] == ["retry", "stop"]
    assert checks[0]["verified"] == {"checked": True, "contradictions": 1}
    assert "reviews go to independent writers" in checks[0]["shortfalls"][-1]
    assert snap["final_answer"] == good and snap["objective"]["verified"]["contradictions"] == 0


def test_an_invented_quote_or_sentence_is_ignored() -> None:
    turn = [{"role": "observation", "tool": "graph_node", "status": "ok", "text": RECORD_TEXT}]
    made_up = lambda *a: [{"sentence": SLIP, "source_quote": "the review always goes to the reader"},
                          {"sentence": "A sentence that is not in the answer.", "source_quote": "never publishes or sells"}]
    findings, error = objective.verify_claims(made_up, "q", SLIP, turn, None)
    assert findings == [] and error == ""


def test_a_broken_verifier_does_not_stop_the_agent() -> None:
    turn = [{"role": "observation", "tool": "graph_node", "status": "ok", "text": RECORD_TEXT}]
    def broken(*a):
        raise TimeoutError("model slow")
    findings, error = objective.verify_claims(broken, "q", SLIP, turn, None)
    assert findings == [] and "TimeoutError" in error


def test_no_sources_means_no_verification_call() -> None:
    called = []
    findings, _ = objective.verify_claims(lambda *a: called.append(1) or [], "q", "answer", [], None)
    assert findings == [] and called == []

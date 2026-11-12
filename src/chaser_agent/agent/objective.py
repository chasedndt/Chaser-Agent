"""Did this turn achieve what was asked? A small logistic score, checked before the agent stops.

A model will happily stop after one empty search and hand the job back ("could you give me more
context?"), or write a fluent answer with nothing read behind it. Both look finished. This scores
the turn from what actually happened in it, not from the model's own claim:

    score = sigmoid(b + w . x)

x is a short vector of observed facts: whether a search found anything, whether a record was
read, how many searches came back empty, how much of the request the answer and the evidence
cover, how many tools failed, and whether the agent is asking the person before it has really
tried. w and b are set by hand to start with (WEIGHTS below), so every decision is explainable
term by term; they are meant to be refitted later from the owner's own accept/reject history.

The terms follow the task-verification failures in Cemri et al., "Why Do Multi-Agent LLM Systems
Fail?" (arXiv 2503.13657): premature termination (FM-3.1) is what deferred_early and the stop gate
catch, no or incomplete verification (FM-3.2) is what found/read/coverage/required_missing measure,
and being unaware of termination conditions (FM-1.5) is what the threshold makes explicit. Its
opposite failure, not asking for clarification (FM-2.2), is why a question is still allowed once the
tools have really been tried.

Below THRESHOLD, with retries and budget left, the agent is not allowed to stop: it is told which
terms pulled the score down and what to try next, and the loop continues. When it does stop, the
score and whether the objective was met are recorded with the turn, so a failure says it failed.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from typing import Any

THRESHOLD = 0.6
MAX_RETRIES = 2
# Each feature lies in [0, 1]. Positive weights reward evidence; negative ones penalise giving up.
WEIGHTS: dict[str, float] = {
    "found": 1.2,             # some search returned at least one result
    "read": 1.6,              # a record or document was actually read
    "coverage": 1.4,          # share of the request's key words present in the answer and evidence
    "answered": 0.8,          # the turn ends in an answer rather than a question
    "empty_searches": -0.9,   # searches that came back empty, scaled to at most three
    "failures": -0.8,         # tool calls that failed or were refused, scaled to at most three
    "deferred_early": -2.2,   # asking the person after fewer than three tool calls
    "required_missing": -4.0, # share of the workflow's required sources for this request not read
}
BIAS = -1.6
SEARCH = re.compile(r"search|find|scan|list")
READ = re.compile(r"node|read|segment|recall|fetch|open")
STOP_WORDS = frozenset(
    "about after again also and any are ask can could does each for from have how into its just know like "
    "make more most much need only other over please show some such tell than that the their them then there "
    "these they this those through two use very what when where which while who why will with would you your "
    # Words about the asking, not the subject: "search my knowledge graph ... in two sentences".
    "search find look graph knowledge sentence sentences short brief briefly summary summarise explain describe "
    "give list record records note notes".split()
)


def sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-value))


def key_terms(goal: str) -> set[str]:
    """The words that carry the request: the person's own text, not attached context."""
    own = goal.split("\n\n---\n", 1)[0]
    spaced = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", own)
    return {word for word in re.findall(r"[a-z0-9]{4,}", spaced.lower()) if word not in STOP_WORDS}


def _result_count(text: str) -> int | None:
    try:
        value = json.loads(text)
    except (TypeError, ValueError):
        return None
    if isinstance(value, dict):
        for key in ("results", "hits", "items", "matches"):
            if isinstance(value.get(key), list):
                return len(value[key])
    if isinstance(value, list):
        return len(value)
    return None


@dataclass(frozen=True)
class Verdict:
    score: float
    met: bool
    features: dict[str, float]
    shortfalls: tuple[str, ...]

    def as_record(self) -> dict[str, Any]:
        # The score is a process heuristic with hand-set weights. It is not a probability that the
        # answer is correct: calibration needs held-out human verdicts (Guo et al. 2017, sec. 4), and
        # a confident-looking self-check can still pass a wrong answer (Kadavath et al. 2022, sec. 6.1).
        return {"score": round(self.score, 3), "met": self.met, "threshold": THRESHOLD,
                "features": {k: round(v, 3) for k, v in self.features.items()}, "shortfalls": list(self.shortfalls),
                "basis": "process heuristic, hand-set weights", "calibrated": False}


@dataclass(frozen=True)
class Requirement:
    """When a request matches `when`, the turn must include a successful call to a tool matching
    `tool` (a regular expression over the tool name) whose arguments match `args` before it may stop:
    for example, reading a product's own record or page.

    `contradicts`, when set, is a claim the authoritative source denies. An answer that makes it
    cannot stop, whatever its score. This is a narrow, source-backed claim check in the spirit of
    CRITIC (Gou et al. 2023): verification against an external source rather than the model's own
    critique, which that paper found adds little on its own. It catches only the claims written into it."""
    when: str
    tool: str
    args: str
    describe: str
    contradicts: str = ""
    source: str = "the authoritative source"

    def applies(self, goal: str) -> bool:
        return bool(re.search(self.when, goal))

    def satisfied(self, calls: list[dict[str, Any]]) -> bool:
        return any(re.fullmatch(self.tool, str(call.get("tool") or "")) and call.get("status") == "ok"
                   and re.search(self.args, json.dumps(call.get("args") or {}, ensure_ascii=False)) for call in calls)

    def contradiction(self, answer: str) -> str | None:
        if not self.contradicts:
            return None
        match = re.search(self.contradicts, answer or "")
        return match.group(0) if match else None


def assess(goal: str, turn: list[dict[str, Any]], *, ending: str, answer: str = "",
           calls: list[dict[str, Any]] | None = None, requires: tuple[Requirement, ...] = ()) -> Verdict:
    """Score one turn. `turn` is the transcript since the person's last message; `ending` is
    'final' or 'ask'."""
    observations = [row for row in turn if row.get("role") == "observation"]
    searches = [row for row in observations if SEARCH.search(str(row.get("tool", "")))]
    reads = [row for row in observations if READ.search(str(row.get("tool", ""))) and row.get("status") == "ok"]
    counts = [_result_count(str(row.get("text", ""))) for row in searches if row.get("status") == "ok"]
    found = any(count for count in counts if count)
    empty = sum(1 for count in counts if count == 0)
    failed = sum(1 for row in observations if row.get("status") not in ("ok", None))
    terms = key_terms(goal)
    seen = (answer + " " + " ".join(str(row.get("text", ""))[:4000] for row in observations)).lower()
    coverage = (sum(1 for term in terms if term in seen) / len(terms)) if terms else 1.0
    features = {
        "found": 1.0 if found else 0.0,
        "read": 1.0 if reads else 0.0,
        "coverage": coverage,
        "answered": 1.0 if ending == "final" else 0.0,
        "empty_searches": min(empty, 3) / 3,
        "failures": min(failed, 3) / 3,
        "deferred_early": 1.0 if ending == "ask" and len(observations) < 3 else 0.0,
        "required_missing": 0.0,
    }
    applicable = [req for req in requires if req.applies(goal)]
    unread = [req for req in applicable if not req.satisfied(calls or [])]
    contradicted = []
    for req in applicable:
        said = req.contradiction(answer if ending == "final" else "")
        if said:
            contradicted.append((req, said))
    failing = {id(req) for req in unread} | {id(req) for req, _ in contradicted}
    if applicable:
        features["required_missing"] = len(failing) / len(applicable)
    score = sigmoid(BIAS + sum(WEIGHTS[name] * value for name, value in features.items()))
    shortfalls = [f"required for this request and not done yet: {req.describe}" for req in unread]
    shortfalls += [f'the answer contradicts {req.source}: it says "{said}". Check that claim against the source and correct it'
                   for req, said in contradicted]
    if not found and searches:
        shortfalls.append("every search came back empty: search again without a namespace, with other spellings or the words split apart")
    if not searches and not reads:
        shortfalls.append("nothing was looked up: search for the subject first")
    if found and not reads:
        shortfalls.append("results were found but none was read: read the best record before answering")
    if coverage < 0.6 and terms:
        missing = sorted(term for term in terms if term not in seen)[:6]
        shortfalls.append("the answer and evidence don't cover: " + ", ".join(missing))
    if features["deferred_early"]:
        shortfalls.append("you are asking the person before trying the tools you have")
    # Required sources and contradicted claims are gates, not just weights: with several requirements the
    # share-of-unmet term alone let a turn skip one and still pass (seen live on 12 Nov 2026 at 0.756).
    return Verdict(score, score >= THRESHOLD and not unread and not contradicted, features, tuple(shortfalls))


def retry_note(verdict: Verdict, attempt: int) -> str:
    reasons = "; ".join(verdict.shortfalls) or "the evidence is too thin"
    return (f"Objective check {attempt}/{MAX_RETRIES}: this turn scores {verdict.score:.2f}, below {THRESHOLD:.2f}, "
            f"so it is not finished. What is missing: {reasons}. Keep working with your tools; only ask the person "
            "something they alone can answer.")

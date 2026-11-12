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
    """Overflow-free for any finite value, the sign-split form of Lin, Lin and Weng (2007, pp. 5-6). With the
    current weights z only spans about -9.5 to 3.4, but learned weights may not stay in that range."""
    if value >= 0:
        return 1.0 / (1.0 + math.exp(-value))
    e = math.exp(value)
    return e / (1.0 + e)


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
    verified: dict[str, Any] | None = None

    def as_record(self) -> dict[str, Any]:
        # The score is a process heuristic with hand-set weights. It is not a probability that the
        # answer is correct: calibration needs held-out human verdicts (Guo et al. 2017, sec. 4), and
        # a confident-looking self-check can still pass a wrong answer (Kadavath et al. 2022, sec. 6.1).
        return {"score": round(self.score, 3), "met": self.met, "threshold": THRESHOLD,
                "features": {k: round(v, 3) for k, v in self.features.items()}, "shortfalls": list(self.shortfalls),
                "basis": "process heuristic, hand-set weights", "calibrated": False,
                **({"verified": self.verified} if self.verified is not None else {})}


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
    # A turn can read every required source and still answer about a different subject it also read. `names` is a
    # pattern a final answer must contain when this requirement applies, so an answer has to name the subject the
    # request is about; `subject` is how the shortfall names it.
    names: str = ""
    subject: str = ""
    # `each`: `when` captures references (group 1) and every one must be read, not just any call matching `args`,
    # so a record attached by reference alone is read before the answer rather than some other record.
    each: bool = False

    def applies(self, goal: str) -> bool:
        return bool(re.search(self.when, goal))

    def unmet(self, goal: str, calls: list[dict[str, Any]]) -> list[str]:
        """What this requirement still needs for `goal`, as shortfall descriptions; empty when satisfied."""
        if not self.each:
            return [] if self.satisfied(calls) else [self.describe]
        wanted = list(dict.fromkeys(match.group(1) for match in re.finditer(self.when, goal)))
        done = [json.dumps(call.get("args") or {}, ensure_ascii=False) for call in calls
                if re.fullmatch(self.tool, str(call.get("tool") or "")) and call.get("status") == "ok"]
        return [self.describe.format(ref=ref) for ref in wanted if not any(ref in args for args in done)]

    def off_subject(self, answer: str) -> bool:
        return bool(self.names) and bool(answer) and not re.search(self.names, answer)

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
    needs = [(req, req.unmet(goal, calls or [])) for req in applicable]
    unread = [(req, missing) for req, missing in needs if missing]
    final_answer = answer if ending == "final" else ""
    contradicted = []
    for req in applicable:
        said = req.contradiction(final_answer)
        if said:
            contradicted.append((req, said))
    off_subject = [req for req in applicable if req.off_subject(final_answer)]
    failing = {id(req) for req, _ in unread} | {id(req) for req, _ in contradicted} | {id(req) for req in off_subject}
    if applicable:
        features["required_missing"] = len(failing) / len(applicable)
    score = sigmoid(BIAS + sum(WEIGHTS[name] * value for name, value in features.items()))
    shortfalls = [f"required for this request and not done yet: {text}" for _, missing in unread for text in missing]
    shortfalls += [f'the answer contradicts {req.source}: it says "{said}". Check that claim against the source and correct it'
                   for req, said in contradicted]
    shortfalls += [f"the answer never names {req.subject or 'the subject the request is about'}: answer about it, "
                   "not about another record you read" for req in off_subject]
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
    return Verdict(score, score >= THRESHOLD and not unread and not contradicted and not off_subject, features,
                   tuple(shortfalls))


SOURCE_TOOLS = re.compile(r"^(graph_node|web_fetch|read_document|graph_source_segments)$")


def _normal(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip().lower()


def verify_claims(verifier: Any, goal: str, answer: str, turn: list[dict[str, Any]], complete: Any) -> tuple[list[dict[str, str]], str]:
    """Run a workflow's claim verifier on a passing final answer and keep only checkable findings.

    The verifier sees the sources this turn actually read and returns sentences of the answer that the sources
    contradict, each with a supporting quote. A finding counts only if its sentence is in the answer and its quote
    is in the sources, so a verifier can't invent an objection or a source (the evidence-quoting guard suggested by
    Self-RAG's support check, Asai et al. 2023). Contradictions only, not "not mentioned": CRITIC (Gou et al. 2023,
    Tables 6-7) shows corrections also break correct answers. Returns (findings, error)."""
    sources = [str(row.get("text") or "")[:12000] for row in turn
               if row.get("role") == "observation" and row.get("status") == "ok" and SOURCE_TOOLS.match(str(row.get("tool") or ""))]
    if not sources:
        return [], ""
    try:
        raw = verifier(goal, answer, sources, complete) or []
    except Exception as exc:  # noqa: BLE001 - a broken verifier must not stop the agent
        return [], f"{type(exc).__name__}: {exc}"[:200]
    joined, said = _normal(" ".join(sources)), _normal(answer)
    kept = []
    for item in raw[:6]:
        if not isinstance(item, dict):
            continue
        sentence, quote = str(item.get("sentence") or "").strip(), str(item.get("source_quote") or "").strip()
        if len(_normal(quote)) >= 12 and _normal(sentence) and _normal(sentence) in said and _normal(quote) in joined:
            kept.append({"sentence": sentence[:300], "source_quote": quote[:300]})
    return kept, ""


def with_contradictions(verdict: Verdict, findings: list[dict[str, str]], error: str = "") -> Verdict:
    shortfalls = list(verdict.shortfalls) + [
        f'the sources contradict "{f["sentence"]}": they say "{f["source_quote"]}". Correct that sentence from the source'
        for f in findings]
    record_extra = {"checked": True, "contradictions": len(findings), **({"error": error} if error else {})}
    features = dict(verdict.features)
    return Verdict(verdict.score, verdict.met and not findings, features, tuple(shortfalls), record_extra)


def retry_note(verdict: Verdict, attempt: int) -> str:
    reasons = "; ".join(verdict.shortfalls) or "the evidence is too thin"
    return (f"Objective check {attempt}/{MAX_RETRIES}: this turn scores {verdict.score:.2f}, below {THRESHOLD:.2f}, "
            f"so it is not finished. What is missing: {reasons}. Keep working with your tools; only ask the person "
            "something they alone can answer.")

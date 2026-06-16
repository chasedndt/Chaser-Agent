from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

ATOM = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
ARXIV_API_BASE = "https://export.arxiv.org/api/query"


@dataclass(frozen=True)
class PaperRecord:
    paper_id: str
    title: str
    authors: list[str]
    published_date: str
    source: str
    primary_url: str
    pdf_url: str | None
    categories: list[str]
    abstract: str
    source_query: str

    def to_chase_schema(self) -> dict[str, Any]:
        topic_tags = infer_topic_tags(f"{self.title}\n{self.abstract}")
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "authors": self.authors,
            "published_date": self.published_date,
            "source": self.source,
            "primary_url": self.primary_url,
            "pdf_url": self.pdf_url,
            "code_url": None,
            "institution_tags": [],
            "topic_tags": topic_tags,
            "categories": self.categories,
            "abstract": self.abstract,
            "claims": [],
            "benchmarks": [],
            "datasets": [],
            "implementation_ideas": [],
            "risk_flags": [],
            "reproducibility": {
                "code_available": False,
                "data_available": False,
                "benchmark_public": False,
                "environment_reproducible": "unknown",
            },
            "scores": {
                "domain_fit": 0,
                "empirical_strength": 0,
                "reproducibility": 0,
                "implementability": 0,
                "evalability": 0,
                "safety_reliability": 0,
                "novelty": 0,
                "total": 0,
            },
            "decision": "unread",
            "source_query": self.source_query,
            "notes": "",
        }


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def arxiv_base_id(url_or_id: str) -> str:
    match = re.search(r"(\d{4}\.\d{4,5})(?:v\d+)?", url_or_id)
    if not match:
        raise ValueError(f"could not parse arXiv id from {url_or_id!r}")
    return match.group(1)


def canonical_abs_url(base_id: str) -> str:
    return f"https://arxiv.org/abs/{base_id}"


def canonical_pdf_url(base_id: str) -> str:
    return f"https://arxiv.org/pdf/{base_id}"


def parse_date(value: str) -> str:
    return value.split("T", 1)[0]


def infer_topic_tags(text: str) -> list[str]:
    lowered = text.lower()
    tags: list[str] = []
    checks = {
        "agent_harness": ["harness", "agent runtime", "agent framework"],
        "self_evolution": ["self-improv", "self improv", "evolution", "trace-driven", "trajectory"],
        "coding_agents": ["coding agent", "software engineering", "swe-bench", "program repair"],
        "computer_use": ["computer use", "browser agent", "web agent", "gui agent", "osworld"],
        "memory_context": ["memory", "context", "retrieval", "prompt compression"],
        "evals": ["benchmark", "eval", "evaluation", "bench"],
        "tool_use": ["tool use", "tool-use", "function calling", "mcp"],
    }
    for tag, needles in checks.items():
        if any(needle in lowered for needle in needles):
            tags.append(tag)
    return tags


def parse_arxiv_atom(xml_text: str, source_query: str) -> list[PaperRecord]:
    root = ET.fromstring(xml_text)
    records: list[PaperRecord] = []
    for entry in root.findall("atom:entry", ATOM):
        raw_id = clean_text(entry.findtext("atom:id", default="", namespaces=ATOM))
        base_id = arxiv_base_id(raw_id)
        title = clean_text(entry.findtext("atom:title", default="", namespaces=ATOM))
        abstract = clean_text(entry.findtext("atom:summary", default="", namespaces=ATOM))
        published = clean_text(entry.findtext("atom:published", default="", namespaces=ATOM))
        authors = [clean_text(node.findtext("atom:name", default="", namespaces=ATOM)) for node in entry.findall("atom:author", ATOM)]
        authors = [author for author in authors if author]
        categories = []
        for category in entry.findall("atom:category", ATOM):
            term = category.attrib.get("term")
            if term and term not in categories:
                categories.append(term)
        records.append(
            PaperRecord(
                paper_id=f"arxiv:{base_id}",
                title=title,
                authors=authors,
                published_date=parse_date(published),
                source="arxiv_api",
                primary_url=canonical_abs_url(base_id),
                pdf_url=canonical_pdf_url(base_id),
                categories=categories,
                abstract=abstract,
                source_query=source_query,
            )
        )
    return records


def parse_rss_date(value: str) -> str:
    if not value:
        return ""
    return parsedate_to_datetime(value).date().isoformat()


def parse_arxiv_rss(xml_text: str, source_query: str) -> list[PaperRecord]:
    root = ET.fromstring(xml_text)
    records: list[PaperRecord] = []
    for item in root.findall("./channel/item"):
        link = clean_text(item.findtext("link", default=""))
        base_id = arxiv_base_id(link)
        records.append(
            PaperRecord(
                paper_id=f"arxiv:{base_id}",
                title=clean_text(item.findtext("title", default="")),
                authors=[],
                published_date=parse_rss_date(clean_text(item.findtext("pubDate", default=""))),
                source="arxiv_rss",
                primary_url=canonical_abs_url(base_id),
                pdf_url=canonical_pdf_url(base_id),
                categories=[],
                abstract=clean_text(item.findtext("description", default="")),
                source_query=source_query,
            )
        )
    return records


def title_hash(title: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def dedupe_records(records: list[PaperRecord]) -> list[PaperRecord]:
    by_key: dict[str, PaperRecord] = {}
    for record in records:
        key = record.paper_id or hashlib.sha256(record.title.lower().encode("utf-8")).hexdigest()
        by_key[key] = record
    return sorted(by_key.values(), key=lambda item: (item.published_date, item.paper_id), reverse=True)


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def write_manifest(out_dir: Path, manifest: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_dir.joinpath("manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_fixture_ingest(fixture_path: Path, out_root: Path, source_query: str) -> dict[str, Any]:
    xml_text = fixture_path.read_text(encoding="utf-8")
    return write_ingest_outputs(xml_text, out_root, source_query=source_query, fetch_mode="fixture")


def write_ingest_outputs(xml_text: str, out_root: Path, source_query: str, fetch_mode: str) -> dict[str, Any]:
    stamp = utc_stamp()
    run_dir = out_root / f"arxiv-ingest-{stamp}"
    if run_dir.exists():
        for index in range(1, 1000):
            candidate = out_root / f"arxiv-ingest-{stamp}-{index:03d}"
            if not candidate.exists():
                run_dir = candidate
                break
    raw_dir = run_dir / "raw"
    normalized_dir = run_dir / "normalized"
    raw_dir.mkdir(parents=True, exist_ok=False)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    raw_path = raw_dir / "arxiv_api.xml"
    raw_path.write_text(xml_text, encoding="utf-8")
    raw_records = parse_arxiv_atom(xml_text, source_query=source_query)
    deduped = dedupe_records(raw_records)
    raw_jsonl = normalized_dir / "raw_records.jsonl"
    papers_jsonl = normalized_dir / "papers.jsonl"
    write_jsonl(raw_jsonl, [asdict(record) for record in raw_records])
    write_jsonl(papers_jsonl, [record.to_chase_schema() for record in deduped])
    manifest = {
        "status": "pass",
        "phase": "phase_1b_primary_source_ingestion",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "fetch_mode": fetch_mode,
        "source": "arxiv_api",
        "source_query": source_query,
        "raw_count": len(raw_records),
        "deduped_count": len(deduped),
        "raw_path": raw_path.as_posix(),
        "raw_records_jsonl": raw_jsonl.as_posix(),
        "papers_jsonl": papers_jsonl.as_posix(),
        "control_plane": {
            "parent": "ChaseOS",
            "authority": "public research source read + local artifacts only",
            "no_candidate_implementation": True,
            "no_branch_or_pr_automation": True,
            "no_provider_or_credential_activation": True,
            "no_canonical_promotion": True,
        },
    }
    write_manifest(run_dir, manifest)
    return manifest


def write_rss_outputs(xml_text: str, out_root: Path, source_query: str, fetch_mode: str) -> dict[str, Any]:
    stamp = utc_stamp()
    run_dir = out_root / f"arxiv-rss-ingest-{stamp}"
    if run_dir.exists():
        for index in range(1, 1000):
            candidate = out_root / f"arxiv-rss-ingest-{stamp}-{index:03d}"
            if not candidate.exists():
                run_dir = candidate
                break
    raw_dir = run_dir / "raw"
    normalized_dir = run_dir / "normalized"
    raw_dir.mkdir(parents=True, exist_ok=False)
    normalized_dir.mkdir(parents=True, exist_ok=True)
    raw_path = raw_dir / "arxiv_rss.xml"
    raw_path.write_text(xml_text, encoding="utf-8")
    raw_records = parse_arxiv_rss(xml_text, source_query=source_query)
    deduped = dedupe_records(raw_records)
    raw_jsonl = normalized_dir / "raw_records.jsonl"
    papers_jsonl = normalized_dir / "papers.jsonl"
    write_jsonl(raw_jsonl, [asdict(record) for record in raw_records])
    write_jsonl(papers_jsonl, [record.to_chase_schema() for record in deduped])
    manifest = {
        "status": "pass",
        "phase": "phase_1b_primary_source_ingestion",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "fetch_mode": fetch_mode,
        "source": "arxiv_rss",
        "source_query": source_query,
        "raw_count": len(raw_records),
        "deduped_count": len(deduped),
        "raw_path": raw_path.as_posix(),
        "raw_records_jsonl": raw_jsonl.as_posix(),
        "papers_jsonl": papers_jsonl.as_posix(),
        "control_plane": {
            "parent": "ChaseOS",
            "authority": "public research source read + local artifacts only",
            "no_candidate_implementation": True,
            "no_branch_or_pr_automation": True,
            "no_provider_or_credential_activation": True,
            "no_canonical_promotion": True,
        },
    }
    write_manifest(run_dir, manifest)
    return manifest


def run_batch_fixture_ingest(fixture_path: Path, out_root: Path, queries: list[dict[str, Any]]) -> dict[str, Any]:
    xml_text = fixture_path.read_text(encoding="utf-8")
    stamp = utc_stamp()
    run_dir = out_root / f"arxiv-batch-ingest-{stamp}"
    if run_dir.exists():
        for index in range(1, 1000):
            candidate = out_root / f"arxiv-batch-ingest-{stamp}-{index:03d}"
            if not candidate.exists():
                run_dir = candidate
                break
    raw_dir = run_dir / "raw"
    normalized_dir = run_dir / "normalized"
    raw_dir.mkdir(parents=True, exist_ok=False)
    normalized_dir.mkdir(parents=True, exist_ok=True)

    all_records: list[PaperRecord] = []
    for query in queries:
        name = query["name"]
        raw_path = raw_dir / f"{name}.xml"
        raw_path.write_text(xml_text, encoding="utf-8")
        all_records.extend(parse_arxiv_atom(xml_text, source_query=query["search_query"]))

    deduped = dedupe_records(all_records)
    raw_records_jsonl = normalized_dir / "raw_records.jsonl"
    consolidated_papers_jsonl = normalized_dir / "papers.jsonl"
    write_jsonl(raw_records_jsonl, [asdict(record) for record in all_records])
    write_jsonl(consolidated_papers_jsonl, [record.to_chase_schema() for record in deduped])
    manifest = {
        "status": "pass",
        "phase": "phase_1b_primary_source_ingestion",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "fetch_mode": "fixture_batch",
        "query_count": len(queries),
        "raw_count": len(all_records),
        "deduped_count": len(deduped),
        "raw_records_jsonl": raw_records_jsonl.as_posix(),
        "consolidated_papers_jsonl": consolidated_papers_jsonl.as_posix(),
        "control_plane": {
            "parent": "ChaseOS",
            "authority": "public research source read + local artifacts only",
            "no_candidate_implementation": True,
            "no_branch_or_pr_automation": True,
            "no_provider_or_credential_activation": True,
            "no_canonical_promotion": True,
        },
    }
    write_manifest(run_dir, manifest)
    return manifest


def build_arxiv_query_url(search_query: str, max_results: int) -> str:
    params = {
        "search_query": search_query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": str(max_results),
    }
    return f"{ARXIV_API_BASE}?{urllib.parse.urlencode(params)}"


def fetch_arxiv(search_query: str, max_results: int, timeout: int = 30) -> str:
    url = build_arxiv_query_url(search_query, max_results=max_results)
    return fetch_url(url, timeout=timeout)


def fetch_url(url: str, timeout: int = 30) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "Chaser-Agent-Research-Intake/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:  # nosec B310: bounded public research source read
        return response.read().decode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 1B bounded arXiv API/RSS research ingestion.")
    parser.add_argument("--fixture", type=Path, help="Parse a local arXiv Atom fixture instead of fetching network data.")
    parser.add_argument("--rss-url", help="Fetch an arXiv RSS/Atom category feed URL instead of using the search API.")
    parser.add_argument("--query", default='cat:cs.AI AND (agent harness OR tool use OR computer use)', help="arXiv search_query value or RSS source label.")
    parser.add_argument("--max-results", type=int, default=25, help="Maximum arXiv records to fetch for one bounded run.")
    parser.add_argument("--out", type=Path, default=Path("research_intake/data"), help="Output root for raw/normalized artifacts.")
    args = parser.parse_args()

    if args.fixture:
        manifest = run_fixture_ingest(args.fixture, args.out, source_query=args.query)
    elif args.rss_url:
        xml_text = fetch_url(args.rss_url)
        manifest = write_rss_outputs(xml_text, args.out, source_query=args.query, fetch_mode="arxiv_rss")
    else:
        xml_text = fetch_arxiv(args.query, max_results=args.max_results)
        manifest = write_ingest_outputs(xml_text, args.out, source_query=args.query, fetch_mode="arxiv_api")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0 if manifest["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

import json
from pathlib import Path

from research_intake.ingest import (
    PaperRecord,
    dedupe_records,
    parse_arxiv_atom,
    parse_arxiv_rss,
    run_batch_fixture_ingest,
    run_fixture_ingest,
)


ARXIV_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2606.14249v1</id>
    <updated>2026-06-12T00:00:00Z</updated>
    <published>2026-06-12T00:00:00Z</published>
    <title>HarnessX: A Composable Agent Harness Foundry</title>
    <summary>We introduce typed harness primitives and trace-driven evolution.</summary>
    <author><name>Ada Lovelace</name></author>
    <author><name>Grace Hopper</name></author>
    <arxiv:primary_category term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.SE" scheme="http://arxiv.org/schemas/atom"/>
    <link href="http://arxiv.org/abs/2606.14249v1" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/2606.14249v1" rel="related" type="application/pdf"/>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2606.14249v2</id>
    <updated>2026-06-13T00:00:00Z</updated>
    <published>2026-06-12T00:00:00Z</published>
    <title>HarnessX: A Composable Agent Harness Foundry</title>
    <summary>Duplicate version should dedupe by base arXiv id.</summary>
    <author><name>Ada Lovelace</name></author>
    <arxiv:primary_category term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
    <category term="cs.AI" scheme="http://arxiv.org/schemas/atom"/>
    <link href="http://arxiv.org/abs/2606.14249v2" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/2606.14249v2" rel="related" type="application/pdf"/>
  </entry>
</feed>
"""
ARXIV_RSS_FIXTURE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <item>
      <title>TokenPilot: Context Management for LLM Agents</title>
      <link>https://arxiv.org/abs/2606.17016</link>
      <description>Context management framework for long-horizon LLM agents.</description>
      <pubDate>Mon, 15 Jun 2026 00:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""


def test_parse_arxiv_atom_normalizes_chase_paper_record():
    records = parse_arxiv_atom(ARXIV_FIXTURE, source_query="agent harness")

    assert records[0] == PaperRecord(
        paper_id="arxiv:2606.14249",
        title="HarnessX: A Composable Agent Harness Foundry",
        authors=["Ada Lovelace", "Grace Hopper"],
        published_date="2026-06-12",
        source="arxiv_api",
        primary_url="https://arxiv.org/abs/2606.14249",
        pdf_url="https://arxiv.org/pdf/2606.14249",
        categories=["cs.AI", "cs.SE"],
        abstract="We introduce typed harness primitives and trace-driven evolution.",
        source_query="agent harness",
    )


def test_dedupe_records_prefers_latest_version_for_same_arxiv_id():
    records = parse_arxiv_atom(ARXIV_FIXTURE, source_query="agent harness")

    deduped = dedupe_records(records)

    assert len(deduped) == 1
    assert deduped[0].paper_id == "arxiv:2606.14249"
    assert deduped[0].abstract == "Duplicate version should dedupe by base arXiv id."


def test_fixture_ingest_writes_raw_normalized_and_papers_jsonl(tmp_path):
    fixture = tmp_path / "fixture.xml"
    fixture.write_text(ARXIV_FIXTURE, encoding="utf-8")

    manifest = run_fixture_ingest(fixture, tmp_path / "out", source_query="agent harness")

    assert manifest["status"] == "pass"
    assert manifest["raw_count"] == 2
    assert manifest["deduped_count"] == 1
    assert manifest["control_plane"]["no_candidate_implementation"] is True

    papers_path = Path(manifest["papers_jsonl"])
    rows = [json.loads(line) for line in papers_path.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["paper_id"] == "arxiv:2606.14249"
    assert rows[0]["reproducibility"]["environment_reproducible"] == "unknown"
    assert rows[0]["decision"] == "unread"


def test_parse_arxiv_rss_normalizes_feed_item():
    records = parse_arxiv_rss(ARXIV_RSS_FIXTURE, source_query="rss:cs.AI")

    assert records[0].paper_id == "arxiv:2606.17016"
    assert records[0].title == "TokenPilot: Context Management for LLM Agents"
    assert records[0].source == "arxiv_rss"
    assert records[0].published_date == "2026-06-15"
    assert records[0].pdf_url == "https://arxiv.org/pdf/2606.17016"


def test_batch_fixture_ingest_consolidates_multiple_queries(tmp_path):
    fixture = tmp_path / "fixture.xml"
    fixture.write_text(ARXIV_FIXTURE, encoding="utf-8")

    queries = [
        {"name": "agent_harness_core", "search_query": "agent harness", "max_results": 100},
        {"name": "memory_context_tools", "search_query": "context management", "max_results": 100},
    ]
    manifest = run_batch_fixture_ingest(fixture, tmp_path / "out", queries=queries)

    assert manifest["status"] == "pass"
    assert manifest["query_count"] == 2
    assert manifest["raw_count"] == 4
    assert manifest["deduped_count"] == 1
    assert Path(manifest["consolidated_papers_jsonl"]).exists()

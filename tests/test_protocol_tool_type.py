"""A tool named in "type", the shape ChaseOS Cloud's models sent on 12 Nov 2026, is read as the tool call."""

import pytest

from chaser_agent.agent.protocol import ReplyRejected, ToolAction, parse_reply


def test_a_tool_named_in_type_is_read_as_that_tool_call() -> None:
    reply = parse_reply('{"thought":"Searching","actions":[{"type":"graph_search","args":{"query":"missed appointments","limit":5}}]}')
    assert reply.actions == (ToolAction("graph_search", {"query": "missed appointments", "limit": 5}),)


def test_the_proper_shape_still_works_and_a_tool_without_args_gets_none() -> None:
    assert parse_reply('{"thought":"t","actions":[{"type":"tool","tool":"workspace_list","args":{}}]}').actions == (ToolAction("workspace_list", {}),)
    assert parse_reply('{"thought":"t","actions":[{"type":"workspace_list"}]}').actions == (ToolAction("workspace_list", {}),)


def test_anything_else_unknown_is_still_refused_and_the_refusal_shows_the_right_shape() -> None:
    for bad in ('{"type":"graph_search","query":"x"}', '{"type":"Graph Search","args":{}}', '{"type":"graph_search","args":"x"}'):
        with pytest.raises(ReplyRejected) as caught:
            parse_reply('{"thought":"t","actions":[' + bad + ']}')
        assert caught.value.reason_code in ("invalid_action", "invalid_field")
    with pytest.raises(ReplyRejected) as caught:
        parse_reply('{"thought":"t","actions":[{"type":"Graph Search","args":{}}]}')
    assert '"type": "tool", "tool": "<name>"' in caught.value.message

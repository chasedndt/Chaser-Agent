from chaser_agent.schemas import SourceInput, SourceCard
from chaser_agent.summary.source_card import build_source_card

def test_source_card_schema_works():
    source=SourceInput(id="test", title="Test", text="Raw source stays separate from reviewed memory.")
    card=build_source_card(source)
    assert isinstance(card, SourceCard)
    assert card.source_id == "test"
    assert "Raw source" in card.summary
    assert card.uncertainty_labels
    assert card.memory_candidates

from .schemas import SourceInput
from .summary.source_card import build_source_card

def main() -> None:
    sample = SourceInput(id="cli_sample", title="CLI Sample", text="Raw source text stays separate from reviewed memory.")
    card = build_source_card(sample)
    print(card.summary)

if __name__ == "__main__":
    main()

def score_required_includes(output_text: str, must_include: list[str]) -> tuple[bool, float]:
    if not must_include:
        return True, 1.0
    lowered=output_text.lower()
    hits=sum(1 for item in must_include if item.lower() in lowered)
    score=hits/len(must_include)
    return hits == len(must_include), score


def find_forbidden_phrases(output_text: str, must_not_include: list[str]) -> list[str]:
    lowered=output_text.lower()
    return [item for item in must_not_include if item.lower() in lowered]

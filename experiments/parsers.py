from typing import List


def parse_yes_no(text: str, yes_tokens: List[str] = None, no_tokens: List[str] = None) -> int:
    if not text:
        return 2
    t = text.strip().lower()
    # coarse heuristics compatible with legacy
    if yes_tokens is None:
        yes_tokens = ["yes"]
    if no_tokens is None:
        no_tokens = ["no"]
    tokens = t.replace("\n", " ").replace("\r", " ").replace(",", " ").replace(".", " ")
    parts = [p.strip() for p in tokens.split(" ") if p.strip()]
    saw_no = False
    for p in parts:
        if p in yes_tokens:
            return 0
        if p in no_tokens:
            saw_no = True
    return 1 if saw_no else 2


def parse_contradiction(text: str) -> int:
    if not text:
        return 2
    # Remove punctuation to isolate words
    t = text.replace("\n", "").replace("\r", "").replace(",", " ").replace(":", " ").replace("*", " ").replace("'", " ").replace(".", " ")
    t = t.strip().lower()
    parts = [p for p in t.split(" ") if p]
    if not parts:
        return 2
    last = parts[-1]
    if last in ["contradiction", "contradictory", "false", "wrong"]:
        return 0
    if last in ["satisfiable", "true", "satisfied", "unknown", "uncertain"]:
        return 1
    return 2
def parse_both(text: str, yes_tokens: List[str] = None, no_tokens: List[str] = None) -> int:
    """Accept either yes/no or contradiction/satisfiable family.
    Returns 0 for YES or CONTRADICTION, 1 for NO or SATISFIABLE, else 2.
    """
    if not text:
        return 2
    # Fast path: try yes/no first
    yn = parse_yes_no(text, yes_tokens, no_tokens)
    if yn in (0, 1):
        return yn
    # Then try contradiction tokens by last word
    t = text.replace("\n", "").replace("\r", "").replace(",", " ").replace(":", " ").replace("*", " ").replace("'", " ").replace(".", " ")
    t = t.strip().lower()
    parts = [p for p in t.split(" ") if p]
    if not parts:
        return 2
    last = parts[-1]
    if last in ["contradiction", "contradictory", "false", "wrong"]:
        return 0
    if last in ["satisfiable", "true", "satisfied", "unknown", "uncertain"]:
        return 1
    return 2




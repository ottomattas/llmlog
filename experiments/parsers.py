from typing import List


def parse_yes_no(text: str, yes_tokens: List[str] = None, no_tokens: List[str] = None) -> int:
    if not text:
        return 2
    t = text.strip().lower()
    if yes_tokens is None:
        yes_tokens = ["yes"]
    if no_tokens is None:
        no_tokens = ["no"]
    # Normalize common formatting and punctuation that often wraps the final token
    for ch in ["\n", "\r", ",", ".", ":", ";", "!", "?", "(", ")", "[", "]", "{", "}", "'", '"', "`", "*", "_"]:
        t = t.replace(ch, " ")
    parts = [p.strip() for p in t.split(" ") if p.strip()]
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
    t = text.lower()
    # Normalize common punctuation/formatting
    for ch in ["\n", "\r", ",", ".", ":", ";", "!", "?", "(", ")", "[", "]", "{", "}", "'", '"', "`", "*", "_"]:
        t = t.replace(ch, " ")
    parts = [p for p in t.split(" ") if p]
    if not parts:
        return 2
    # Prefer last decisive token in the text
    decisive = None
    for p in reversed(parts[-10:]):  # scan last few tokens
        if p in ["contradiction", "contradictory", "false", "wrong"]:
            decisive = 0
            break
        if p in ["satisfiable", "true", "satisfied", "unknown", "uncertain"]:
            if decisive is None:
                decisive = 1
                # continue scanning in case a later decisive 0 appears
    if decisive is not None:
        return decisive
    # Fallback to last token
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




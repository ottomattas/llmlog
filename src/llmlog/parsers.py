from __future__ import annotations

from typing import List, Optional


_PUNCT_TO_SPACE = ["\n", "\r", ",", ".", ":", ";", "!", "?", "(", ")", "[", "]", "{", "}", "'", '"', "`", "*", "_"]


def _tokenize(text: str) -> List[str]:
    """Tokenize a model response into lowercase word tokens.

    We intentionally keep this tokenizer very simple and stable so:
    - prompts can require a single answer token on the last line
    - runs can include arbitrary reasoning traces above the final answer
    - parsing remains robust even if the reasoning contains keywords like "contradiction"
    """
    if not text:
        return []
    t = text.strip().lower()
    for ch in _PUNCT_TO_SPACE:
        t = t.replace(ch, " ")
    return [p.strip() for p in t.split(" ") if p.strip()]


def _last_matching_token(tokens: List[str], choices: List[str]) -> Optional[str]:
    """Return the last token (nearest the end) that matches one of `choices`."""
    if not tokens:
        return None
    choice_set = {c.strip().lower() for c in (choices or []) if str(c).strip()}
    if not choice_set:
        return None
    for tok in reversed(tokens):
        if tok in choice_set:
            return tok
    return None


def parse_yes_no(text: str, yes_tokens: Optional[List[str]] = None, no_tokens: Optional[List[str]] = None) -> int:
    """Return 0 for yes, 1 for no, 2 for unclear.

    Characterization target: experiments/parsers.py
    """
    if yes_tokens is None:
        yes_tokens = ["yes"]
    if no_tokens is None:
        no_tokens = ["no"]
    parts = _tokenize(text)

    # Prefer the last decisive token to support long reasoning traces above
    # a single final answer token on the last line.
    tok = _last_matching_token(parts, yes_tokens + no_tokens)
    if tok is None:
        return 2
    if tok in {t.lower() for t in yes_tokens}:
        return 0
    if tok in {t.lower() for t in no_tokens}:
        return 1
    return 2


def parse_contradiction(text: str) -> int:
    """Return 0 for contradiction/unsat, 1 for satisfiable/true/unknown-ish, 2 for unclear.

    Characterization target: experiments/parsers.py
    """
    parts = _tokenize(text)
    if not parts:
        return 2

    contradiction_tokens = ["contradiction", "contradictory", "false", "wrong"]
    satisfiable_tokens = ["satisfiable", "true", "satisfied", "unknown", "uncertain"]

    tok = _last_matching_token(parts, contradiction_tokens + satisfiable_tokens)
    if tok is None:
        return 2
    if tok in set(contradiction_tokens):
        return 0
    if tok in set(satisfiable_tokens):
        return 1
    return 2


def parse_both(text: str, yes_tokens: Optional[List[str]] = None, no_tokens: Optional[List[str]] = None) -> int:
    """Accept either yes/no or contradiction/satisfiable family.

    Returns 0 for YES or CONTRADICTION, 1 for NO or SATISFIABLE, else 2.
    Characterization target: experiments/parsers.py
    """
    # Prefer the last decisive token among either family.
    if yes_tokens is None:
        yes_tokens = ["yes"]
    if no_tokens is None:
        no_tokens = ["no"]

    parts = _tokenize(text)
    if not parts:
        return 2

    contradiction_tokens = ["contradiction", "contradictory", "false", "wrong"]
    satisfiable_tokens = ["satisfiable", "true", "satisfied", "unknown", "uncertain"]

    tok = _last_matching_token(parts, yes_tokens + no_tokens + contradiction_tokens + satisfiable_tokens)
    if tok is None:
        return 2
    if tok in {t.lower() for t in yes_tokens}:
        return 0
    if tok in {t.lower() for t in no_tokens}:
        return 1
    if tok in set(contradiction_tokens):
        return 0
    if tok in set(satisfiable_tokens):
        return 1
    return 2




from __future__ import annotations

from typing import List, Optional


def parse_yes_no(text: str, yes_tokens: Optional[List[str]] = None, no_tokens: Optional[List[str]] = None) -> int:
    """Return 0 for yes, 1 for no, 2 for unclear.

    Characterization target: experiments/parsers.py
    """
    if not text:
        return 2
    t = text.strip().lower()
    if yes_tokens is None:
        yes_tokens = ["yes"]
    if no_tokens is None:
        no_tokens = ["no"]
    # Normalize punctuation/formatting so "yes." and similar parse cleanly.
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
    """Return 0 for contradiction/unsat, 1 for satisfiable/true/unknown-ish, 2 for unclear.

    Characterization target: experiments/parsers.py
    """
    if not text:
        return 2
    t = text.lower()
    for ch in ["\n", "\r", ",", ".", ":", ";", "!", "?", "(", ")", "[", "]", "{", "}", "'", '"', "`", "*", "_"]:
        t = t.replace(ch, " ")
    parts = [p for p in t.split(" ") if p]
    if not parts:
        return 2
    decisive = None
    for p in reversed(parts[-10:]):
        if p in ["contradiction", "contradictory", "false", "wrong"]:
            decisive = 0
            break
        if p in ["satisfiable", "true", "satisfied", "unknown", "uncertain"]:
            if decisive is None:
                decisive = 1
    if decisive is not None:
        return decisive
    last = parts[-1]
    if last in ["contradiction", "contradictory", "false", "wrong"]:
        return 0
    if last in ["satisfiable", "true", "satisfied", "unknown", "uncertain"]:
        return 1
    return 2


def parse_both(text: str, yes_tokens: Optional[List[str]] = None, no_tokens: Optional[List[str]] = None) -> int:
    """Accept either yes/no or contradiction/satisfiable family.

    Returns 0 for YES or CONTRADICTION, 1 for NO or SATISFIABLE, else 2.
    Characterization target: experiments/parsers.py
    """
    if not text:
        return 2
    yn = parse_yes_no(text, yes_tokens, no_tokens)
    if yn in (0, 1):
        return yn
    t = (
        text.replace("\n", "")
        .replace("\r", "")
        .replace(",", " ")
        .replace(":", " ")
        .replace("*", " ")
        .replace("'", " ")
        .replace(".", " ")
    )
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



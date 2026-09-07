#!/usr/bin/env python3
"""Normalize Chinese academic typography without flattening semantic tokens."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class SemanticToken:
    kind: str
    text: str
    break_after: bool = False


_CJK = r"\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff"
_CITATION = re.compile(r"\[(\d+(?:\s*[-–—,;，、]\s*\d+)*)\]")
_UNICODE_CITATION = re.compile(r"[⁰¹²³⁴⁵⁶⁷⁸⁹]+(?:[˒,，–—-][⁰¹²³⁴⁵⁶⁷⁸⁹]+)*")
_SUPERSCRIPT_MAP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹˒", "0123456789,")
_SCIENTIFIC = re.compile(
    r"(?<!\w)([+\-−]?\d+(?:\.\d+)?)\s*[×xX*]\s*10\s*(?:\^|\*\*)?\s*([+\-−]?\d+)"
)
_STAT_SCI = re.compile(
    r"(?i)(?<![A-Za-z0-9_])(?:p|t|f|z|r|rs|β|χ²)\s*(?:\([^)]*\))?\s*(?:=|<|>|≤|≥)\s*"
    r"[+\-−]?\d+(?:\.\d+)?\s*[×xX*]\s*10\s*(?:\^|\*\*)?\s*[+\-−]?\d+"
)
_STAT_GROUP = re.compile(
    r"(?i)(?<![A-Za-z0-9_])(?:β\s*\[\s*SE\s*\]|p|t|f|z|r|rs|χ²|df|95%\s*CI)"
    r"\s*(?:\([^)]*\))?\s*(?:=|<|>|≤|≥)\s*[+\-−]?\d+(?:\.\d+)?(?!\s*[×xX*])"
)
_UNIT_GROUP = re.compile(
    r"(?i)(?<!\w)([+\-−]?\d+(?:\.\d+)?)\s*(Hz|kHz|MHz|ms|s|min|h|dB|mV|μV|mm|cm|kg|g)\b"
)
_PERCENT = re.compile(r"(?<!\w)([+\-−]?\d+(?:\.\d+)?)\s+%")
_PROTECTED = re.compile(
    r"SWS\s*[×xX*]\s*REM|%\s*Δ\s*Error|95%\s*CI|REM|NREM|SWS|TMR|"
    r"(?:[A-Z]-Nap|CB|E-Nap)",
    re.IGNORECASE,
)


def normalize_citation(value: str) -> str:
    """Return a comma-separated Nature-style citation payload with en-dash ranges."""
    value = re.sub(r"\s+", "", value)
    value = value.replace("；", ",").replace(";", ",").replace("，", ",").replace("、", ",")
    value = value.replace("—", "–").replace("-", "–")
    return value


def source_citation_groups(source_text: str) -> list[str]:
    """Extract publisher-style citation groups attached to English prose words."""
    groups: list[str] = []
    pattern = re.compile(
        r"(?<=[A-Za-z)])(\d{1,3}(?:\s*[,;]\s*\d{1,3}|\s*[–—-]\s*\d{1,3})*)(?=[.,;:)\s]|$)"
    )
    for match in pattern.finditer(source_text):
        if (
            match.start()
            and source_text[match.start() - 1] in "TtFfVv"
            and (match.start() < 2 or not source_text[match.start() - 2].isalpha())
        ):
            continue
        group = normalize_citation(match.group(1))
        if group not in groups:
            groups.append(group)
    return groups


def normalize_inline_citations(translated_text: str, source_text: str) -> str:
    """Mark source-supported plain Chinese inline citation numbers for raised rendering."""
    text = translated_text
    for group in sorted(source_citation_groups(source_text), key=len, reverse=True):
        variants = {group, group.replace("–", "-"), group.replace(",", "，")}
        for variant in sorted(variants, key=len, reverse=True):
            pattern = re.compile(
                rf"(?<=[{_CJK}）】])(?<![\[⁰¹²³⁴⁵⁶⁷⁸⁹]){re.escape(variant)}(?=[{_CJK}，。；：！？、（）【】\s]|$)"
            )
            text, count = pattern.subn(f"[{group}]", text, count=1)
            if count:
                break
    return text


def normalize_chinese_text(text: str) -> str:
    """Apply conservative CJK spacing, punctuation and numeric typography rules."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("－", "−")
    text = re.sub(r"补充表\s*\[(\d+)\]", r"补充表\1", text)
    text = re.sub(r"(表|图)\s+\[(\d+)\]", r"\1\2", text)
    text = re.sub(r"(?<!\d)-(?=\d)", "−", text)
    text = _SCIENTIFIC.sub(
        lambda m: f"{m.group(1).replace('-', '−')} × 10{m.group(2).replace('-', '−')}", text
    )
    text = _PERCENT.sub(r"\1%", text)
    text = _UNIT_GROUP.sub(lambda m: f"{m.group(1)} {m.group(2)}", text)
    text = re.sub(r"SWS\s*[xX*]\s*REM", "SWS×REM", text)
    text = re.sub(r"%\s*Δ\s*Error", "%ΔError", text, flags=re.IGNORECASE)
    text = re.sub(r"95%\s*CI", "95% CI", text, flags=re.IGNORECASE)
    text = re.sub(r"β\s*\[\s*SE\s*\]", "β[SE]", text, flags=re.IGNORECASE)
    text = re.sub(r"（\s*", "（", text)
    text = re.sub(r"\s*）", "）", text)
    text = re.sub(r"\(\s*([A-Za-z][A-Za-z0-9+−-]*)\s*\)", r"（\1）", text)
    text = re.sub(rf"(?<=[{_CJK}）】])[ \t]+(?=[{_CJK}，。；：！？、（）【】])", "", text)
    text = re.sub(rf"(?<=[（【])[ \t]+(?=[{_CJK}A-Za-z0-9%])", "", text)
    text = re.sub(rf"(?<=[，。；：！？、）】])[ \t]+(?=[{_CJK}])", "", text)
    text = re.sub(rf"(?<=[{_CJK}，。；：！？、）】])[ \t]+(?=[A-Za-zΑ-ω])", "", text)
    text = re.sub(rf"(?<=[A-Za-zΑ-ω])[ \t]+(?=[{_CJK}，。；：！？、（【])", "", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text


def semantic_tokens(text: str) -> list[SemanticToken]:
    """Tokenize normalized text while keeping citations and scientific notation atomic."""
    text = normalize_chinese_text(text)
    patterns = [("CITATION", _CITATION), ("CITATION_SUP", _UNICODE_CITATION),
                ("STAT", _STAT_SCI), ("SCIENTIFIC", _SCIENTIFIC), ("STAT", _STAT_GROUP),
                ("PROTECTED", _PROTECTED), ("UNIT", _UNIT_GROUP)]
    tokens: list[SemanticToken] = []
    position = 0
    while position < len(text):
        if text[position] == "\n":
            tokens.append(SemanticToken("BREAK", "\n", True))
            position += 1
            continue
        match_kind = None
        match = None
        for kind, pattern in patterns:
            candidate = pattern.match(text, position)
            if candidate and (match is None or candidate.end() > match.end()):
                match_kind, match = kind, candidate
        if match is not None:
            if match_kind == "CITATION":
                payload = normalize_citation(match.group(1))
            elif match_kind == "CITATION_SUP":
                payload = normalize_citation(match.group(0).translate(_SUPERSCRIPT_MAP))
            else:
                payload = match.group(0)
            tokens.append(SemanticToken("CITATION" if match_kind == "CITATION_SUP" else match_kind or "TEXT", payload))
            position = match.end()
            continue
        char = text[position]
        if char.isspace():
            end = position + 1
            while end < len(text) and text[end] in " \t":
                end += 1
            tokens.append(SemanticToken("SPACE", " "))
            position = end
        else:
            kind = "PUNCTUATION" if char in "，。；：！？、（）【】《》" else "TEXT"
            tokens.append(SemanticToken(kind, char))
            position += 1
    return tokens


def visible_text(tokens: list[SemanticToken]) -> str:
    return "".join(token.text for token in tokens if token.kind != "BREAK")

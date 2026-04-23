from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Literal, Tuple

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry

from recognizers.invoice import InvoiceNumberRecognizer
from recognizers.sl_nic import SriLankanNICRecognizer
from recognizers.sl_phone import SriLankanPhoneRecognizer
from report import DetectionRow


TokenStyle = Literal["brackets", "angle"]


@dataclass(frozen=True)
class CleanResult:
    original_text: str
    redacted_text: str
    token_to_value: Dict[str, str]
    detection_rows: List[DetectionRow]

    def restore(self, llm_output: str) -> str:
        restored = llm_output
        # Replace longest tokens first to avoid accidental partial overlaps.
        for token in sorted(self.token_to_value.keys(), key=len, reverse=True):
            restored = restored.replace(token, self.token_to_value[token])
        return restored


class PromptCleaner:
    """
    Detects PII/IDs with Presidio, replaces them with stable tokens, and supports restoration.

    Token format is designed to be hard for LLMs to "normalize" (paired delimiters + uppercase).
    """

    def __init__(
        self,
        language: str = "en",
        entities: Iterable[str] | None = None,
        token_style: TokenStyle = "brackets",
    ) -> None:
        self._language = language
        self._entities = list(entities) if entities else None
        self._token_style = token_style

        registry = RecognizerRegistry()
        registry.load_predefined_recognizers()
        registry.add_recognizer(SriLankanNICRecognizer())
        registry.add_recognizer(InvoiceNumberRecognizer())
        registry.add_recognizer(SriLankanPhoneRecognizer())

        self._analyzer = AnalyzerEngine(registry=registry)

    def _token_for(self, entity_type: str, i: int) -> str:
        if self._token_style == "angle":
            return f"<<{entity_type}_{i}>>"
        return f"[[{entity_type}_{i}]]"

    def clean(self, text: str) -> CleanResult:
        findings = self._analyzer.analyze(
            text=text,
            language=self._language,
            entities=self._entities,
            score_threshold=0.35,
        )

        # Presidio can return overlapping findings (e.g., EMAIL_ADDRESS and URL inside it).
        # We must pick a non-overlapping set or redaction will corrupt the text.
        # Strategy: prefer higher score, then longer span.
        candidates = sorted(
            findings,
            key=lambda r: (-float(r.score), -(r.end - r.start), r.start, r.end, r.entity_type),
        )

        selected: List[Tuple[int, int, str, float]] = []
        selected_results = []
        for r in candidates:
            span = (r.start, r.end)
            overlaps = any(not (span[1] <= s[0] or span[0] >= s[1]) for s in selected)
            if overlaps:
                continue
            selected.append(span)
            selected_results.append(r)

        # Ensure stable ordering for token assignment and replacement.
        findings_sorted = sorted(selected_results, key=lambda r: (r.start, r.end, r.entity_type))

        token_to_value: Dict[str, str] = {}
        rows: List[DetectionRow] = []

        # Track duplicates: same substring may appear multiple times.
        # We assign tokens per finding, not per unique value, to make restoration unambiguous.
        for idx, r in enumerate(findings_sorted, start=1):
            token = self._token_for(r.entity_type, idx)
            value = text[r.start : r.end]

            token_to_value[token] = value

            rows.append(
                DetectionRow(
                    entity_type=r.entity_type,
                    start=r.start,
                    end=r.end,
                    score=float(r.score),
                    text=value,
                    token=token,
                )
            )

        if not findings_sorted:
            return CleanResult(
                original_text=text,
                redacted_text=text,
                token_to_value={},
                detection_rows=[],
            )

        # Manual replacement is required because Presidio operators apply per entity type,
        # but we need unique tokens per match.
        # Perform replacements from end to start to keep spans valid.
        redacted = text
        for row in sorted(rows, key=lambda x: (x.start, x.end), reverse=True):
            redacted = redacted[: row.start] + row.token + redacted[row.end :]

        # Note: We intentionally don't do a naive "value not in redacted" check here,
        # because the same substring might legitimately appear elsewhere in the text
        # (e.g., repeated names). Use the detection report to verify coverage.

        return CleanResult(
            original_text=text,
            redacted_text=redacted,
            token_to_value=token_to_value,
            detection_rows=rows,
        )


_TOKEN_RE = re.compile(r"\[\[[A-Z_]+_\d+\]\]|\<\<[A-Z_]+_\d+\>\>")


def contains_tokens(text: str) -> bool:
    return _TOKEN_RE.search(text) is not None


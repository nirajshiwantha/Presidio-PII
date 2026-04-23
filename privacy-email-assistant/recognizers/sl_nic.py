from __future__ import annotations

from presidio_analyzer import Pattern, PatternRecognizer


class SriLankanNICRecognizer(PatternRecognizer):
    """
    Recognizes Sri Lankan NIC numbers:
    - Old format: 9 digits + [VvXx] (e.g. 912345678V)
    - New format: 12 digits (e.g. 200012345678)

    Note: We intentionally do NOT match just 9 digits without the suffix letter.
    """

    def __init__(self) -> None:
        patterns = [
            Pattern(
                name="sl_nic_old",
                regex=r"\b\d{9}[VvXx]\b",
                score=0.85,
            ),
            Pattern(
                name="sl_nic_new",
                regex=r"\b\d{12}\b",
                score=0.6,
            ),
        ]
        super().__init__(
            supported_entity="SL_NIC",
            patterns=patterns,
            supported_language="en",
        )


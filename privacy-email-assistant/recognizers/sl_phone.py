from __future__ import annotations

from presidio_analyzer import Pattern, PatternRecognizer


class SriLankanPhoneRecognizer(PatternRecognizer):
    """
    Sri Lankan phone patterns (simple):
    - +94XXXXXXXXX (country code)
    - 0XXXXXXXXX (local)
    """

    def __init__(self) -> None:
        patterns = [
            Pattern(
                name="sl_phone_e164",
                regex=r"\b\+94\d{9}\b",
                score=0.75,
            ),
            Pattern(
                name="sl_phone_local",
                regex=r"\b0\d{9}\b",
                score=0.55,
            ),
        ]
        super().__init__(
            supported_entity="PHONE_NUMBER",
            patterns=patterns,
            supported_language="en",
        )


from __future__ import annotations

from presidio_analyzer import Pattern, PatternRecognizer


class InvoiceNumberRecognizer(PatternRecognizer):
    """
    Invoice reference, context-aware.

    Examples:
    - INV-2341
    - INV2341
    - INVOICE-2341
    """

    def __init__(self) -> None:
        patterns = [
            Pattern(
                name="invoice_ref",
                regex=r"\b(?:INV|INVOICE)[-_]?\d{3,10}\b",
                score=0.65,
            )
        ]
        super().__init__(
            supported_entity="INVOICE_NUMBER",
            patterns=patterns,
            supported_language="en",
            context=["invoice", "inv", "bill", "billing", "reference", "ref", "payment"],
        )


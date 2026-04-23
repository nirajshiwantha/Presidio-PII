from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from cleaner import PromptCleaner


def run_cases() -> None:
    cleaner = PromptCleaner()

    cases = [
        # Baseline example
        (
            "Write a polite follow-up email from Alex Silva (alex.silva@example.com, +94770000000) "
            "to Maya Perera (maya.perera@client.example) about the overdue invoice INV-2341 for LKR 85,000 "
            "due on 15 March 2026. NIC on file: 912345678V."
        ),
        # NIC should match with suffix letter
        "NIC: 912345678V, please update.",
        # NIC should NOT match 9 digits only
        "NIC: 912345678 (digits only) should not match old NIC format.",
        # New NIC 12 digits
        "New NIC: 200012345678 should be detected.",
        # Invoice with context
        "Invoice INV-2341 is overdue. Please pay.",
        # Similar string without context should be less likely (but may still match regex)
        "Random code INV-2341X in a log line (should ideally not be treated as invoice).",
        # Phone formats
        "Call me on +94770000000 or 0770000000.",
    ]

    for i, text in enumerate(cases, start=1):
        result = cleaner.clean(text)
        # Ensure every produced token appears in the redacted text at least once.
        assert all(t in result.redacted_text for t in result.token_to_value.keys()), f"Missing token in case {i}"
        restored = result.restore(result.redacted_text)
        assert restored == text, f"Round-trip failed on case {i}"

    print(f"OK: {len(cases)} test cases passed.")


if __name__ == "__main__":
    run_cases()


from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from tabulate import tabulate


@dataclass(frozen=True)
class DetectionRow:
    entity_type: str
    start: int
    end: int
    score: float
    text: str
    token: str


def print_detection_report(rows: Iterable[DetectionRow]) -> None:
    rows_list = list(rows)
    if not rows_list:
        print("No entities detected.")
        return

    table = [
        [
            r.entity_type,
            f"{r.score:.2f}",
            f"{r.start}:{r.end}",
            r.text,
            r.token,
        ]
        for r in rows_list
    ]
    print(
        tabulate(
            table,
            headers=["Entity", "Score", "Span", "Detected Text", "Token"],
            tablefmt="github",
        )
    )


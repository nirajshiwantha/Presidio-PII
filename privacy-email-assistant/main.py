from __future__ import annotations

import argparse
import sys

from cleaner import PromptCleaner
from llm import generate_email_draft
from report import print_detection_report


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Privacy-safe email assistant (Presidio)")
    p.add_argument("--text", required=True, help="Natural-language request")
    p.add_argument(
        "--use-llm",
        action="store_true",
        help="Call OpenAI/Anthropic if API keys are set (otherwise stub).",
    )
    p.add_argument(
        "--token-style",
        choices=["brackets", "angle"],
        default="brackets",
        help="Token delimiter style.",
    )
    return p.parse_args(argv)


def main(argv: list[str]) -> int:
    args = _parse_args(argv)

    cleaner = PromptCleaner(token_style=args.token_style)
    result = cleaner.clean(args.text)

    print("\n=== ORIGINAL INPUT ===\n")
    print(result.original_text)

    print("\n=== DETECTION REPORT (pre-LLM) ===\n")
    print_detection_report(result.detection_rows)

    print("\n=== REDACTED PROMPT (sent to LLM) ===\n")
    print(result.redacted_text)

    # Generate draft (remote if requested + keys exist, otherwise stub)
    llm_resp = generate_email_draft(
        result.redacted_text,
        provider=None if args.use_llm else "stub",
    )

    print(f"\n=== LLM OUTPUT (provider: {llm_resp.provider}) ===\n")
    print(llm_resp.text)

    restored = result.restore(llm_resp.text)

    print("\n=== RESTORED FINAL EMAIL ===\n")
    print(restored)

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))


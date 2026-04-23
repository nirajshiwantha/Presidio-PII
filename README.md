## Privacy-Safe Email Assistant (Presidio)

CLI tool that drafts professional emails using an LLM **without sending real PII** (names/emails/phones/NICs/invoice numbers) to the model.

### Setup

```bash
cd privacy-email-assistant
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Run (CLI)

```bash
python main.py --text "Write a polite follow-up email from Alex Silva (alex.silva@example.com, +94770000000) to Maya Perera (maya.perera@client.example) about the overdue invoice INV-2341 for LKR 85,000 due on 15 March 2026. NIC on file: 912345678V."
```

### LLM mode (optional)

Set one of:
- `OPENAI_API_KEY` (uses OpenAI)
- `ANTHROPIC_API_KEY` (uses Anthropic Claude)

Then:

```bash
python main.py --text "..." --use-llm
```

### What to look for

- **Milestone 1**: Printed prompt sent to LLM must not include real PII.
- **Milestone 2**: Tokens round-trip back into the final email.
- **Milestone 3**: NIC recognizer catches `912345678V` but not `912345678`.
- **Milestone 4**: Invoice recognizer catches `INV-2341` with context words.
- **Milestone 5**: Report table shows detected entities + confidence + token.

### Project structure

```
privacy-email-assistant/
├── cleaner.py          # PromptCleaner + custom recognizers registry
├── recognizers/
│   ├── sl_nic.py       # Sri Lankan NIC recognizer
│   ├── sl_phone.py     # Local phone format recognizer
│   └── invoice.py      # Invoice number recognizer (context-aware)
├── llm.py              # OpenAI/Anthropic wrapper + system prompt trick
├── report.py           # Detection report printer
├── main.py             # CLI entry point
└── tests/
    └── test_cases.py   # Tricky inputs to validate against
```

### Notes

- **Token safety**: the system prompt in `llm.py` instructs the model not to rewrite placeholders like `[[EMAIL_ADDRESS_2]]`.
- **Overlaps**: `cleaner.py` resolves overlapping detections (e.g. URL inside an email) before replacing spans, to avoid corrupted output.

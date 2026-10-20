# Amala 9 AM Office Work

Deterministic, zero-paid-API workflow for OpenClaw command cron.

It verifies a public business source, calls local Ollama (`qwen3:4b`, then
`gemma3:1b`), creates a Python enquiry-qualification prototype, runs automated
tests, prepares a draft-only outreach email, writes a dated report and prints a
compact delivery summary.

The script does not send outreach email, publish to GitHub, or enable paid APIs.

## Daily archive

Each successful scheduled run creates `runs/YYYY-MM-DD/` containing:

- the verified public-source evidence snapshot;
- model analysis and model/fallback status;
- a functional Python prototype and its tests;
- the draft-only outreach message; and
- the final daily report.

OpenClaw runs `amala_office.mjs` every day at 9:00 AM Asia/Kolkata. The
scheduler prints a concise completion report for delivery through the configured
messaging channel. The local models remain `qwen3:4b` with `gemma3:1b` fallback,
and no paid API is enabled.

After a successful run, the workflow commits the dated artifacts and pushes
them to the private `amala-9am-office-work` GitHub repository. A failed model,
test, commit, or push produces a failed scheduler run instead of a false success.

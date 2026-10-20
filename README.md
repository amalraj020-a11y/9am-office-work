# Amala — Autonomous 9 AM Office Workflow

Amala is Multimax's new intern and automated AI office employee. OpenClaw starts this workflow every day at **9:00 AM Asia/Kolkata**. It researches the configured business opportunity, uses local AI to prepare an automation plan, builds and tests a small Python prototype, saves a report, and publishes the successful run to this repository.

The workflow has a **₹0 paid-API budget**. It uses local Ollama models and does not activate paid AI services. Normal electricity, internet, and account-provider usage still apply.

## What happens at 9 AM

| Stage | What Amala does | Verified output |
| --- | --- | --- |
| 1. Research | Fetches the configured business's official public website and verifies its identity. | `official-site-evidence.txt` |
| 2. Identify opportunity | Treats the operational problem as a hypothesis, not a confirmed customer fact. | `analysis.json` |
| 3. Design solution | Defines the proposed automation's inputs, processing, outputs, and expected value. | Analysis and daily report |
| 4. Build prototype | Creates a small Python enquiry-qualification prototype using synthetic data only. | `prototype/src/qualify.py` |
| 5. Test | Runs the Python unit-test suite and stops the run if a test fails. | Test output in `report.md` |
| 6. Prepare outreach | Produces a personalized email draft for review. The scheduled workflow does not send it. | Draft inside `report.md` |
| 7. Record work | Writes dated evidence, analysis, source code, tests, and the final report. | `runs/YYYY-MM-DD/` |
| 8. Publish | Commits and pushes a successful run to `main`. A push failure makes the workflow fail instead of reporting false success. | Git commit and `run-log.jsonl` |
| 9. Report | Prints a compact result for delivery through OpenClaw's configured messaging channel. | Scheduler run output |

The office session is configured as a one-hour workflow window. The current implementation completes as soon as its controlled tasks finish; it does not artificially wait for the full hour.

## Current business case

The current script is configured for **MobileMistri** (`https://www.mobilemistri.com/`). It does not select a different company automatically each day.

The working hypothesis is that callback and booking enquiries may require manual sorting by repair type, city, urgency, and missing contact details. This must be validated with the business before any commercial implementation.

The prototype converts synthetic enquiry data into:

- enquiry intent;
- urgency;
- detected city;
- missing-information fields; and
- a lead-priority score.

No customer production data is used, and this repository is not a production deployment.

## Tools and models

| Tool | Purpose | Cost configuration |
| --- | --- | --- |
| OpenClaw gateway and scheduler | Runs the job and routes its completion report. | Existing local setup |
| Ollama `qwen3:4b` | Primary local model for the business analysis. | No paid API |
| Ollama `gemma3:1b` | Fallback if the primary model fails. | No paid API |
| Node.js | Executes `amala_office.mjs` and coordinates the workflow. | Local runtime |
| Python `unittest` | Builds and verifies the prototype. | Local runtime |
| Git | Versions every successful daily run. | Free/local |
| GitHub | Stores the public daily archive in this repository. | Free account features |
| WhatsApp through OpenClaw | Receives the configured completion report when the channel is connected. | No paid AI API enabled |

Gmail and Google Sheets were exercised during the controlled setup test. They are **not called by `amala_office.mjs` in every scheduled run**, so the daily report must not claim they were updated unless OpenClaw separately verifies those actions.

Groq is not required by this workflow and is not enabled as a paid fallback. The permitted model order is strictly `qwen3:4b`, then `gemma3:1b`.

## Repository structure

```text
9am-office-work/
├── amala_office.mjs       # Daily workflow orchestrator
├── run-log.jsonl          # PASS/FAIL execution records
├── prototype.gitignore    # Prototype ignore rules
└── runs/
    └── YYYY-MM-DD/
        ├── official-site-evidence.txt
        ├── analysis.json
        ├── report.md
        └── prototype/
            ├── src/qualify.py
            └── tests/test_qualify.py
```

## Success and failure rules

A run is successful only when:

1. the official website is fetched and its identity check passes;
2. one permitted Ollama model returns usable analysis;
3. all automated prototype tests pass;
4. the dated files and run log are written;
5. Git commits any new daily artifacts; and
6. GitHub accepts the push.

If research, both models, tests, commit, or push fails, the scheduler records a failure. Amala must report the real error and must not claim that unfinished integrations succeeded.

## Approval and business-safety rules

- Scheduled outreach is **draft-only**. Sending email requires authorization under the configured operating rules.
- A sent introductory email does not authorize a price, contract, production deployment, or customer-data access.
- The ₹0 budget controls Amala's operating spend; it does **not** promise free development to a customer.
- Prices, delivery dates, contractual commitments, and final proposals require approval.
- Production deployment requires agreed scope, access, security requirements, and commercial terms.
- Public evidence and synthetic demonstration data are used until appropriate customer permission exists.
- Existing Telegram allowlists, channel security, schedule, and model settings must remain intact.

## Daily output and review

Open the newest directory under `runs/` and read `report.md`. It contains the business source, evidence summary, problem hypothesis, proposed solution, model used, prototype location, actual test result, outreach draft, cost status, and next steps.

The latest controlled run is stored in `runs/2026-10-20/`. Its prototype completed **3/3 automated tests** and was pushed to GitHub. That result applies only to that recorded run; future runs must produce their own verified status.

## Schedule and repository

- Schedule: every day at **9:00 AM Asia/Kolkata (IST)**
- Primary model: **Ollama `qwen3:4b`**
- Fallback model: **Ollama `gemma3:1b`**
- Repository: `amalraj020-a11y/9am-office-work`
- Branch: `main`
- Visibility: public
- Paid AI/API budget: **₹0**

Successful daily artifacts are committed with a dated message and pushed to this repository. The workflow does not create duplicate schedules or repositories.

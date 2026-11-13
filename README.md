# Amala — Autonomous 9 AM and 9 PM Office Workflow

Amala is Multimax's automated AI office employee. AWS EventBridge starts the cloud workflow every day at **9:00 AM and 9:00 PM Asia/Kolkata**. A small AWS Lambda function dispatches this public repository's GitHub Actions workflow. The runner verifies OpenClaw, starts Ollama, researches a rotating real business from its official website, prepares an automation plan, builds and tests a Python prototype, saves a report, and publishes the successful run to this repository.

The workflow has a **₹0 paid-API budget**. AWS Lambda and EventBridge usage is kept inside their monthly free allowances, and the public repository uses free standard GitHub-hosted runners. Ollama runs on the temporary GitHub runner, so the office computer may be shut down. No paid AI API is enabled.

## What happens at 9 AM and 9 PM

| Stage | What Amala does | Verified output |
| --- | --- | --- |
| 1. Research | Selects a business from a rotating verified pool, fetches its official public website, and verifies its identity. | `official-site-evidence.txt` |
| 2. Identify opportunity | Treats the operational problem as a hypothesis, not a confirmed customer fact. | `analysis.json` |
| 3. Design solution | Defines the proposed automation's inputs, processing, outputs, and expected value. | Analysis and daily report |
| 4. Build prototype | Creates a small Python enquiry-qualification prototype using synthetic data only. | `prototype/src/qualify.py` |
| 5. Test | Runs the Python unit-test suite and stops the run if a test fails. | Test output in `report.md` |
| 6. Prepare outreach | Produces a personalized email draft for review. The scheduled workflow does not send it. | Draft inside `report.md` |
| 7. Record work | Writes dated evidence, analysis, source code, tests, and the final report. | `runs/YYYY-MM-DD-SLOT/` |
| 8. Publish | Commits and pushes a successful run to `main`. A push failure makes the workflow fail instead of reporting false success. | Git commit and `run-log.jsonl` |
| 9. Report | Prints a compact result in the GitHub Actions run and records the report in the repository. | Actions log and daily report |

The office session is configured as a one-hour workflow window. The current implementation completes as soon as its controlled tasks finish; it does not artificially wait for the full hour.

## Business selection

The script rotates through a curated pool of real service businesses with official public websites. If a selected website fails its identity check, the workflow tries the next candidate and records the failure. Operational problems remain hypotheses until a business confirms them.

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
| AWS EventBridge Scheduler | Triggers the 9 AM and 9 PM jobs in Asia/Kolkata. | Monthly free allowance |
| AWS Lambda | Dispatches the GitHub workflow. | Monthly free allowance |
| OpenClaw | Verified on each temporary runner as the configured agent layer. | Free runner |
| Ollama `qwen3:4b` | Primary model for business analysis. | Free runner; no paid API |
| Ollama `gemma3:1b` | Fallback if the primary model fails. | Free runner; no paid API |
| GitHub Actions | Provides temporary Linux compute while the office PC is off. | Free standard runner for this public repository |
| Node.js | Executes `amala_office.mjs` and coordinates the workflow. | Free runner |
| Python `unittest` | Builds and verifies the prototype. | Free runner |
| Git | Versions every successful run. | Free runner |
| GitHub | Stores reports, prototypes, evidence, and test results. | Public repository; free account features |

Gmail, Google Sheets, WhatsApp, and Telegram credentials are not stored in this public repository or temporary runner. Each cloud report states the actual delivery status and prepares outreach as a draft until a cloud-safe integration is configured.

Groq is not required by this workflow and is not enabled as a paid fallback. The permitted model order is strictly `qwen3:4b`, then `gemma3:1b`.

## Repository structure

```text
9am-office-work/
├── amala_office.mjs       # Daily workflow orchestrator
├── run-log.jsonl          # PASS/FAIL execution records
├── prototype.gitignore    # Prototype ignore rules
└── runs/
    └── YYYY-MM-DD-0900/ or YYYY-MM-DD-2100/
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

- Schedule: every day at **9:00 AM and 9:00 PM Asia/Kolkata (IST)**
- Primary model: **Ollama `qwen3:4b`**
- Fallback model: **Ollama `gemma3:1b`**
- Repository: `amalraj020-a11y/9am-office-work`
- Branch: `main`
- Visibility: public
- Paid AI/API budget: **₹0**

Successful artifacts are committed with a dated slot and pushed to this repository. A run skips an existing slot report, which prevents duplicate execution from creating duplicate work.

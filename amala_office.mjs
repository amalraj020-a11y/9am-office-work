import { access, appendFile, mkdir, writeFile } from "node:fs/promises";
import { constants as fsConstants } from "node:fs";
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PYTHON = process.env.PYTHON || (process.platform === "win32" ? "python" : "python3");
const GIT = process.env.GIT || "git";
const SLOT = (process.env.AMALA_SLOT || "manual").replace(/[^a-zA-Z0-9_-]/g, "-");

const BUSINESSES = [
  { name: "MobileMistri", url: "https://www.mobilemistri.com/", email: "info@mobilemistri.com", identity: ["mobilemistri", "mobile repair"], hypothesis: "Callback and booking enquiries may require manual sorting by repair type, city, urgency, and missing contact details." },
  { name: "Viva Laundry", url: "https://vivalaundry.in/", email: "hello@vivalaundry.in", identity: ["viva laundry", "laundry"], hypothesis: "Pickup requests may require manual routing by branch, service, area, preferred slot, and express-service need." },
  { name: "EasyLaundry", url: "https://easylaundry.in/", email: "support@easylaundry.in", identity: ["easy laundry", "laundry"], hypothesis: "Partner and customer enquiries may require manual classification by location, request type, urgency, and missing details." },
  { name: "MyKhana", url: "https://www.mykhana.in/", email: "sales@mykhana.in", identity: ["mykhana", "catering"], hypothesis: "Catering enquiries may require manual routing by event type, location, date, headcount, menu preference, and budget range." },
  { name: "Shuchi Laundry", url: "https://shuchilaundry.com/", email: "info@shuchilaundry.com", identity: ["shuchi", "laundry"], hypothesis: "Pickup and franchise enquiries may require manual separation, service-area validation, scheduling, and missing-detail follow-up." },
  { name: "GoCaters", url: "https://gocaters.in/", email: "admin@gocaters.in", identity: ["gocaters", "catering"], hypothesis: "Quote requests may require manual qualification by event date, location, guest count, menu, dietary needs, staffing, and equipment." },
  { name: "Doorstep Fix", url: "https://doorstepfix.com/", email: "mansoor@doorstepfix.com", identity: ["doorstep fix", "repair"], hypothesis: "Home-service requests may require manual triage by appliance or trade, location, urgency, warranty need, and preferred visit time." },
];

const PROTOTYPE = `"""Synthetic-data enquiry qualification prototype."""
from dataclasses import asdict, dataclass
import json
import re
import sys

@dataclass
class Result:
    intent: str
    urgency: str
    city: str | None
    missing_fields: list[str]
    score: int

def qualify(enquiry: dict) -> Result:
    text = str(enquiry.get("message", "")).lower()
    cities = ["delhi", "noida", "gurugram", "mumbai", "pune", "bengaluru", "bangalore", "chennai", "hyderabad"]
    city = next((c.title() for c in cities if re.search(rf"\\b{re.escape(c)}\\b", text)), None)
    urgent = any(word in text for word in ("urgent", "today", "asap", "immediately", "same day"))
    booking = any(word in text for word in ("book", "appointment", "pickup", "visit", "quote", "schedule"))
    service = any(word in text for word in ("repair", "laundry", "groom", "catering", "service", "clean"))
    intent = "booking" if booking else "service" if service else "general"
    missing = [key for key in ("name", "contact") if not enquiry.get(key)]
    if city is None:
        missing.append("city")
    score = 50 + (25 if urgent else 0) + (15 if intent != "general" else 0) - 10 * len(missing)
    return Result(intent, "high" if urgent else "normal", city, missing, max(0, min(100, score)))

if __name__ == "__main__":
    payload = json.loads(sys.stdin.read() or "{}")
    print(json.dumps(asdict(qualify(payload)), indent=2))
`;

const TESTS = `import unittest
from src.qualify import qualify

class QualificationTests(unittest.TestCase):
    def test_urgent_booking(self):
        result = qualify({"name":"Anu","contact":"9999999999","message":"Urgent pickup service in Noida today"})
        self.assertEqual(result.intent, "booking")
        self.assertEqual(result.urgency, "high")
        self.assertEqual(result.city, "Noida")
        self.assertEqual(result.missing_fields, [])

    def test_missing_fields(self):
        result = qualify({"message":"Please book an appointment"})
        self.assertEqual(result.intent, "booking")
        self.assertEqual(result.missing_fields, ["name", "contact", "city"])

    def test_general_enquiry(self):
        result = qualify({"name":"Raj","contact":"8888888888","message":"What services do you offer in Pune?"})
        self.assertEqual(result.intent, "service")
        self.assertEqual(result.city, "Pune")

if __name__ == "__main__":
    unittest.main()
`;

function cleanHtml(html) {
  return html.replace(/<script[\s\S]*?<\/script>/gi, " ").replace(/<style[\s\S]*?<\/style>/gi, " ").replace(/<[^>]+>/g, " ").replace(/&nbsp;|&#160;/g, " ").replace(/&amp;/g, "&").replace(/\s+/g, " ").trim();
}

function hash(text) {
  return [...text].reduce((value, char) => ((value * 31) + char.charCodeAt(0)) >>> 0, 2166136261);
}

async function selectBusiness(day) {
  const start = hash(`${day}-${SLOT}`) % BUSINESSES.length;
  const errors = [];
  for (let offset = 0; offset < BUSINESSES.length; offset += 1) {
    const business = BUSINESSES[(start + offset) % BUSINESSES.length];
    try {
      const page = await fetch(business.url, { headers: { "user-agent": "AmalaBusinessResearch/2.0 (+public-source-verification)" }, redirect: "follow", signal: AbortSignal.timeout(30_000) });
      if (!page.ok) throw new Error(`HTTP ${page.status}`);
      const evidence = cleanHtml(await page.text());
      const lower = evidence.toLowerCase();
      if (!business.identity.some((token) => lower.includes(token))) throw new Error("identity check failed");
      return { business, evidence, sourceFailures: errors };
    } catch (error) {
      errors.push(`${business.name}: ${error.message}`);
    }
  }
  throw new Error(`No official business source passed verification: ${errors.join("; ")}`);
}

function baselineAnalysis(business) {
  return {
    problem_hypothesis: `${business.hypothesis} This is a hypothesis to validate with the business.`,
    solution: "An AI-assisted enquiry qualification workflow that extracts the request type, location, urgency, and missing fields, then produces a structured lead and draft follow-up.",
    inputs: "Public website enquiry or booking text, customer name and contact details, requested service, location, and preferred date or slot.",
    processing: "Validate required fields, classify intent and urgency, extract service and location, detect missing information, and route the enquiry for follow-up.",
    outputs: "A structured lead record, priority score, missing-information checklist, routing suggestion, and draft response for review.",
    business_value: "Less manual triage, faster follow-up, more consistent records, and fewer incomplete bookings.",
  };
}

async function callOllama(model, business, evidence) {
  const prompt = `Return concise JSON with keys problem_hypothesis, solution, inputs, processing, outputs, business_value. Business: ${business.name}. Official website: ${business.url}. Public evidence: ${evidence.slice(0, 5000)}. Starting hypothesis: ${business.hypothesis} Label the operational problem as a hypothesis. Propose an enquiry or booking automation grounded in the evidence. Do not invent customer data, internal metrics, prices, or confirmed pain points.`;
  const response = await fetch("http://127.0.0.1:11434/api/generate", { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ model, prompt, stream: false, format: "json", think: false, options: { temperature: 0.1, num_predict: 600 } }), signal: AbortSignal.timeout(180_000) });
  if (!response.ok) throw new Error(`Ollama ${model} HTTP ${response.status}`);
  const result = await response.json();
  if (!result.response) throw new Error(`Ollama ${model} returned no response`);
  return JSON.parse(result.response);
}

async function exists(filePath) {
  try { await access(filePath, fsConstants.F_OK); return true; } catch { return false; }
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, { encoding: "utf8", ...options });
  if (result.error) throw result.error;
  return result;
}

async function main() {
  const day = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Kolkata", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
  const runId = `${day}-${SLOT}`;
  const runDir = path.join(HERE, "runs", runId);
  const reportPath = path.join(runDir, "report.md");
  if (await exists(reportPath)) { console.log(`Amala ${runId} already exists; skipping duplicate execution.`); return; }

  const prototypeDir = path.join(runDir, "prototype");
  await mkdir(path.join(prototypeDir, "src"), { recursive: true });
  await mkdir(path.join(prototypeDir, "tests"), { recursive: true });

  const { business, evidence, sourceFailures } = await selectBusiness(day);
  let analysis;
  let modelUsed;
  const modelErrors = [];
  for (const model of ["qwen3:4b", "gemma3:1b"]) {
    try {
      const candidate = await callOllama(model, business, evidence);
      const required = ["problem_hypothesis", "solution", "inputs", "processing", "outputs", "business_value"];
      analysis = required.every((key) => typeof candidate[key] === "string" && candidate[key].trim()) ? candidate : { ...baselineAnalysis(business), model_quality_note: `${model} omitted required fields; the evidence-based baseline was used.` };
      modelUsed = model;
      break;
    } catch (error) { modelErrors.push(`${model}: ${error.message}`); }
  }
  if (!analysis) throw new Error(`Both permitted Ollama models failed: ${modelErrors.join("; ")}`);

  await writeFile(path.join(prototypeDir, "src", "__init__.py"), "", "utf8");
  await writeFile(path.join(prototypeDir, "src", "qualify.py"), PROTOTYPE, "utf8");
  await writeFile(path.join(prototypeDir, "tests", "test_qualify.py"), TESTS, "utf8");
  const tests = run(PYTHON, ["-m", "unittest", "discover", "-s", "tests", "-v"], { cwd: prototypeDir, timeout: 120_000 });
  const testOutput = `${tests.stdout || ""}${tests.stderr || ""}`.trim();
  if (tests.status !== 0) throw new Error(`Prototype tests failed:\n${testOutput}`);

  const recipientLine = business.email ? `Public email: ${business.email}` : "Public email: not verified; no email may be sent";
  const draft = `Subject: Idea to streamline ${business.name} enquiries\n\nHello ${business.name} team,\n\nI reviewed the enquiry and service information on your public website. A possible opportunity—subject to your confirmation—is automatically sorting incoming requests by service, location, urgency, preferred time, and missing details. Multimax prepared a small prototype using synthetic data only. If useful, I can share a short demonstration.\n\nRegards,\nAmala\nMultimax`;
  const report = `# Amala Office Report — ${runId}\n\n- Business: ${business.name}\n- Official source: ${business.url}\n- ${recipientLine}\n- Evidence: official website fetched and identity-checked successfully\n- Hypothesis: ${analysis.problem_hypothesis}\n- Solution: ${analysis.solution}\n- Inputs: ${analysis.inputs}\n- Processing: ${analysis.processing}\n- Outputs: ${analysis.outputs}\n- Expected value: ${analysis.business_value}\n- Model: Ollama ${modelUsed}${modelErrors.length ? ` (earlier attempt: ${modelErrors.join("; ")})` : ""}\n- OpenClaw: checked by the GitHub workflow before execution\n- Prototype: runs/${runId}/prototype\n- Tests: PASS — 3 automated tests\n- Outreach: draft prepared; cloud Gmail credentials are not configured\n- Actual paid API cost: ₹0\n- Source fallback notes: ${sourceFailures.length ? sourceFailures.join("; ") : "none"}\n\n## Draft email\n\n${draft}\n\n## Test output\n\n\`\`\`\n${testOutput}\n\`\`\`\n`;
  await writeFile(path.join(runDir, "official-site-evidence.txt"), evidence.slice(0, 20_000), "utf8");
  await writeFile(path.join(runDir, "analysis.json"), JSON.stringify({ runId, business, modelUsed, modelErrors, sourceFailures, analysis }, null, 2), "utf8");
  await writeFile(reportPath, report, "utf8");
  await appendFile(path.join(HERE, "run-log.jsonl"), `${JSON.stringify({ runId, status: "PASS", business: business.name, modelUsed, tests: 3, report: `runs/${runId}/report.md` })}\n`, "utf8");

  const gitAdd = run(GIT, ["add", "--", `runs/${runId}`, "run-log.jsonl"], { cwd: HERE, timeout: 60_000 });
  if (gitAdd.status !== 0) throw new Error(`Git add failed: ${(gitAdd.stderr || gitAdd.stdout).trim()}`);
  const staged = run(GIT, ["diff", "--cached", "--quiet"], { cwd: HERE, timeout: 60_000 });
  if (staged.status === 1) {
    const commit = run(GIT, ["commit", "-m", `Add Amala office report ${runId}`], { cwd: HERE, timeout: 120_000 });
    if (commit.status !== 0) throw new Error(`Git commit failed: ${(commit.stderr || commit.stdout).trim()}`);
    const push = run(GIT, ["push", "origin", "main"], { cwd: HERE, timeout: 180_000 });
    if (push.status !== 0) throw new Error(`GitHub push failed: ${(push.stderr || push.stdout).trim()}`);
  } else if (staged.status !== 0) throw new Error(`Git staged-change check failed: ${(staged.stderr || staged.stdout).trim()}`);

  console.log(`🤖 Amala — ${SLOT} Office Workflow PASS\nBusiness: ${business.name}\nOfficial source: ${business.url}\nProblem: ${analysis.problem_hypothesis}\nSolution: ${analysis.solution}\nModel: Ollama ${modelUsed}\nPrototype tests: 3/3 passed\nOutreach: draft prepared\nGitHub: daily artifacts committed and pushed\nCost: ₹0\nReport: runs/${runId}/report.md`);
}

main().catch(async (error) => {
  await appendFile(path.join(HERE, "run-log.jsonl"), `${JSON.stringify({ at: new Date().toISOString(), slot: SLOT, status: "FAIL", error: error.message })}\n`, "utf8");
  console.error(`Amala office workflow failed: ${error.message}`);
  process.exitCode = 1;
});

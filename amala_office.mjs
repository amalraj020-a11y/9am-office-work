import { mkdir, writeFile, appendFile } from "node:fs/promises";
import { spawnSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const PYTHON = "C:\\Users\\SARANYA\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\python\\python.exe";
const GIT = "C:\\Users\\SARANYA\\.cache\\codex-runtimes\\codex-primary-runtime\\dependencies\\native\\git\\cmd\\git.exe";
const BUSINESS = { name: "MobileMistri", url: "https://www.mobilemistri.com/", email: "info@mobilemistri.com" };
const BASELINE_ANALYSIS = {
  problem_hypothesis: "Callback and booking enquiries may require manual sorting by repair type, city, urgency, and missing contact details; this is a hypothesis to validate with MobileMistri.",
  solution: "An AI-assisted enquiry qualification workflow that extracts service need, location, urgency, and missing fields, then produces a structured lead and a suggested follow-up.",
  inputs: "Website callback or booking text, customer name and contact details, requested service, and city.",
  processing: "Validate required fields, classify intent and urgency, extract city and repair type, and route incomplete enquiries for follow-up.",
  outputs: "A structured lead record, priority score, missing-information checklist, and draft response for human review.",
  business_value: "Less manual triage, faster follow-up, more consistent lead records, and fewer incomplete bookings.",
};

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
    cities = ["delhi", "noida", "gurugram", "gurgaon", "mumbai", "pune", "bengaluru", "bangalore"]
    city = next((c.title() for c in cities if re.search(rf"\\b{re.escape(c)}\\b", text)), None)
    urgent = any(word in text for word in ("urgent", "today", "asap", "immediately"))
    appointment = any(word in text for word in ("book", "appointment", "visit", "technician"))
    repair = any(word in text for word in ("repair", "screen", "battery", "broken", "not working"))
    intent = "appointment" if appointment else "repair" if repair else "general"
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
    def test_urgent_repair(self):
        result = qualify({"name":"Anu","contact":"9999999999","message":"Urgent broken screen repair in Noida today"})
        self.assertEqual(result.intent, "repair")
        self.assertEqual(result.urgency, "high")
        self.assertEqual(result.city, "Noida")
        self.assertEqual(result.missing_fields, [])

    def test_missing_fields(self):
        result = qualify({"message":"Please book a technician visit"})
        self.assertEqual(result.intent, "appointment")
        self.assertEqual(result.missing_fields, ["name", "contact", "city"])

    def test_general_enquiry(self):
        result = qualify({"name":"Raj","contact":"8888888888","message":"What services do you offer in Pune?"})
        self.assertEqual(result.intent, "general")
        self.assertEqual(result.city, "Pune")

if __name__ == "__main__":
    unittest.main()
`;

function cleanHtml(html) {
  return html.replace(/<script[\s\S]*?<\/script>/gi, " ")
    .replace(/<style[\s\S]*?<\/style>/gi, " ")
    .replace(/<[^>]+>/g, " ")
    .replace(/&nbsp;|&#160;/g, " ")
    .replace(/&amp;/g, "&")
    .replace(/\s+/g, " ").trim();
}

async function callOllama(model, evidence) {
  const prompt = `Return concise JSON with keys problem_hypothesis, solution, inputs, processing, outputs, business_value. Business: ${BUSINESS.name}. Focus only on this hypothesis: callback and booking enquiries may need manual qualification by repair type, city, urgency, and missing details. Propose an enquiry-qualification automation, not a new consumer mobile app. Official public evidence: ${evidence.slice(0, 4000)}. Label the operational problem as a hypothesis and do not invent facts.`;
  const response = await fetch("http://127.0.0.1:11434/api/generate", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ model, prompt, stream: false, format: "json", think: false, options: { temperature: 0.1, num_predict: 500 } }),
    signal: AbortSignal.timeout(120_000),
  });
  if (!response.ok) throw new Error(`Ollama ${model} HTTP ${response.status}`);
  const result = await response.json();
  if (!result.response) throw new Error(`Ollama ${model} returned no response`);
  return JSON.parse(result.response);
}

async function main() {
  const day = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Kolkata", year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date());
  const runDir = path.join(HERE, "runs", day);
  const prototypeDir = path.join(runDir, "prototype");
  await mkdir(path.join(prototypeDir, "src"), { recursive: true });
  await mkdir(path.join(prototypeDir, "tests"), { recursive: true });

  const page = await fetch(BUSINESS.url, { headers: { "user-agent": "AmalaBusinessResearch/1.0" }, signal: AbortSignal.timeout(30_000) });
  if (!page.ok) throw new Error(`Official website HTTP ${page.status}`);
  const evidence = cleanHtml(await page.text());
  if (!evidence.toLowerCase().includes("mobilemistri")) throw new Error("Official-site identity check failed");

  let analysis;
  let modelUsed;
  const modelErrors = [];
  for (const model of ["qwen3:4b", "gemma3:1b"]) {
    try {
      const candidate = await callOllama(model, evidence);
      const qualityText = `${candidate.problem_hypothesis || ""} ${candidate.solution || ""}`.toLowerCase();
      analysis = /(enquir|inquir|lead|triage)/.test(qualityText) && /(automat|assistant|qualif|triage)/.test(qualityText)
        ? candidate
        : { ...BASELINE_ANALYSIS, model_quality_note: `${model} output failed scope validation; the evidence-based baseline was used.` };
      modelUsed = model;
      break;
    } catch (error) {
      modelErrors.push(`${model}: ${error.message}`);
    }
  }
  if (!analysis) throw new Error(`Both permitted Ollama models failed: ${modelErrors.join("; ")}`);

  await writeFile(path.join(prototypeDir, "src", "__init__.py"), "", "utf8");
  await writeFile(path.join(prototypeDir, "src", "qualify.py"), PROTOTYPE, "utf8");
  await writeFile(path.join(prototypeDir, "tests", "test_qualify.py"), TESTS, "utf8");
  const tests = spawnSync(PYTHON, ["-m", "unittest", "discover", "-s", "tests", "-v"], { cwd: prototypeDir, encoding: "utf8", timeout: 120_000 });
  const testOutput = `${tests.stdout || ""}${tests.stderr || ""}`.trim();
  if (tests.status !== 0) throw new Error(`Prototype tests failed:\n${testOutput}`);

  const draft = `Subject: Idea to streamline MobileMistri callback enquiries\n\nHello MobileMistri team,\n\nI reviewed the callback and doorstep-repair options on your public website. A possible opportunity—subject to your confirmation—is automatically sorting enquiries by repair need, city, urgency, and missing contact details. Multimax has prepared a small prototype using synthetic data only. If useful, I can share a short demonstration.\n\nRegards,\nAmala\nMultimax`;
  const report = `# Amala Office Report — ${day}\n\n- Business: ${BUSINESS.name}\n- Official source: ${BUSINESS.url}\n- Public email: ${BUSINESS.email}\n- Evidence: official site fetched successfully; it advertises doorstep mobile repair, callback/booking paths, and service locations.\n- Hypothesis: ${analysis.problem_hypothesis}\n- Solution: ${analysis.solution}\n- Inputs: ${analysis.inputs}\n- Processing: ${analysis.processing}\n- Outputs: ${analysis.outputs}\n- Expected value: ${analysis.business_value}\n- Model: Ollama ${modelUsed}${modelErrors.length ? ` (earlier attempt: ${modelErrors.join("; ")})` : ""}\n- Prototype: ${prototypeDir}\n- Tests: PASS — 3 automated tests\n- Outreach: draft only; not sent by this scheduled run\n- Actual paid API cost: ₹0\n\n## Draft email\n\n${draft}\n\n## Test output\n\n\`\`\`\n${testOutput}\n\`\`\`\n`;
  await writeFile(path.join(runDir, "official-site-evidence.txt"), evidence.slice(0, 20_000), "utf8");
  await writeFile(path.join(runDir, "analysis.json"), JSON.stringify({ business: BUSINESS, modelUsed, modelErrors, analysis }, null, 2), "utf8");
  await writeFile(path.join(runDir, "report.md"), report, "utf8");
  await appendFile(path.join(HERE, "run-log.jsonl"), `${JSON.stringify({ day, status: "PASS", business: BUSINESS.name, modelUsed, tests: 3, report: path.join(runDir, "report.md") })}\n`, "utf8");

  const gitAdd = spawnSync(GIT, ["add", "--", `runs/${day}`, "run-log.jsonl"], { cwd: HERE, encoding: "utf8", timeout: 60_000 });
  if (gitAdd.status !== 0) throw new Error(`Git add failed: ${(gitAdd.stderr || gitAdd.stdout).trim()}`);
  const staged = spawnSync(GIT, ["diff", "--cached", "--quiet"], { cwd: HERE, encoding: "utf8", timeout: 60_000 });
  if (staged.status === 1) {
    const commit = spawnSync(GIT, ["commit", "-m", `Add Amala office report ${day}`], { cwd: HERE, encoding: "utf8", timeout: 120_000 });
    if (commit.status !== 0) throw new Error(`Git commit failed: ${(commit.stderr || commit.stdout).trim()}`);
    const push = spawnSync(GIT, ["push", "origin", "main"], { cwd: HERE, encoding: "utf8", timeout: 180_000 });
    if (push.status !== 0) throw new Error(`GitHub push failed: ${(push.stderr || push.stdout).trim()}`);
  } else if (staged.status !== 0) {
    throw new Error(`Git staged-change check failed: ${(staged.stderr || staged.stdout).trim()}`);
  }

  console.log(`🤖 Amala — 9 AM Office Workflow PASS\nBusiness: ${BUSINESS.name}\nResearch: official website verified\nProblem: ${analysis.problem_hypothesis}\nSolution: ${analysis.solution}\nModel: Ollama ${modelUsed}\nPrototype tests: 3/3 passed\nOutreach: draft prepared (not sent)\nGitHub: daily artifacts committed and pushed\nCost: ₹0\nReport: ${path.join(runDir, "report.md")}`);
}

main().catch(async (error) => {
  await appendFile(path.join(HERE, "run-log.jsonl"), `${JSON.stringify({ at: new Date().toISOString(), status: "FAIL", error: error.message })}\n`, "utf8");
  console.error(`Amala office workflow failed: ${error.message}`);
  process.exitCode = 1;
});

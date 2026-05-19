"""
Eval harness for DevAgent.

Runs each task twice (self-correction OFF then ON), saves results to
eval_results.json, classifies SC=ON failures via gpt-4o-mini, and saves
the analysis to failure_analysis.json.
"""

import json
import os
import sys
import time

from dotenv import load_dotenv
from openai import OpenAI

from agent import agent, reset_agent

load_dotenv()

TASK_FILE = "tasks.json"
RESULTS_FILE = "eval_results.json"
FAILURE_ANALYSIS_FILE = "failure_analysis.json"
LOGS_DIR = "logs"

VALID_CATEGORIES = {
    "hallucinated_critique",
    "confident_wrong_answer",
    "overcorrection",
    "correction_plateau",
}

eval_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ---------------------------------------------------------------------------
# Task running
# ---------------------------------------------------------------------------

def check_success(output: str, task: dict) -> bool:
    if not output:
        return False
    low = output.lower()
    return all(kw.lower() in low for kw in task.get("success_keywords", []))


def run_task(task: dict, self_correction: bool) -> dict:
    """Run a single task and return a result dict.

    Private fields prefixed with '_' carry data needed for failure
    classification but are stripped before writing eval_results.json.
    """
    reset_agent()
    stats: dict = {"total_tokens": 0, "retries": 0}
    start = time.time()

    try:
        output = agent(task["prompt"], self_correction=self_correction, _stats=stats)
    except Exception as exc:
        output = f"ERROR: {exc}"

    elapsed = round(time.time() - start, 2)
    success = check_success(output or "", task)
    agent_task_id = stats.get("task_id", "")

    return {
        "task_id": task["id"],
        "tier": task["tier"],
        "self_correction": self_correction,
        "success": success,
        "retries": stats.get("retries", 0),
        "total_tokens": stats.get("total_tokens", 0),
        "wall_time_seconds": elapsed,
        "output": (output or "")[:600],
        # private — used by classifier, stripped before saving
        "_output_full": output or "",
        "_log_file": os.path.join(LOGS_DIR, f"{agent_task_id}.json") if agent_task_id else "",
    }


# ---------------------------------------------------------------------------
# Failure classification
# ---------------------------------------------------------------------------

def _load_retry_log(log_file: str) -> list[dict]:
    if not log_file or not os.path.exists(log_file):
        return []
    try:
        with open(log_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _format_retry_log(log_entries: list[dict]) -> str:
    if not log_entries:
        return "  No run_code calls were recorded."
    lines = []
    for e in log_entries:
        stderr = (e.get("stderr") or "").strip()[:300]
        stderr_part = f", stderr={repr(stderr)}" if stderr else ""
        lines.append(f"  Attempt {e['attempt_number']}: success={e['success']}{stderr_part}")
    return "\n".join(lines)


_CLASSIFIER_SYSTEM = """\
You are a precise evaluator classifying why an AI coding agent failed a task.
Return only valid JSON — no markdown fences, no extra keys.\
"""

_CLASSIFIER_CATEGORIES = """\
- hallucinated_critique: The agent claimed a problem existed when none did, \
invented a nonexistent API or library, or refused to proceed citing a made-up constraint.
- confident_wrong_answer: Code ran without errors (exit code 0) but the output is \
factually wrong or does not satisfy the expected outcome.
- overcorrection: The agent fixed one error but introduced a different new error each \
retry — distinct tracebacks across attempts, no convergence.
- correction_plateau: The agent retried but reproduced the same or nearly identical \
error every attempt — no meaningful progress.\
"""


def classify_failure(task: dict, result: dict) -> dict:
    log_entries = _load_retry_log(result.get("_log_file", ""))
    log_text = _format_retry_log(log_entries)

    user_prompt = f"""\
Task prompt:
{task["prompt"]}

Expected outcome:
{task["expected_outcome"]}

Agent's final output:
{result["_output_full"][:1200]}

Retry log ({len(log_entries)} run_code attempt(s)):
{log_text}

Classify this failure into exactly one of these four categories:
{_CLASSIFIER_CATEGORIES}

Return ONLY a JSON object with this exact schema:
{{"category": "<one of the four categories>", "reasoning": "<one concise sentence citing the evidence above>"}}\
"""

    try:
        response = eval_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _CLASSIFIER_SYSTEM},
                {"role": "user",   "content": user_prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        parsed = json.loads(response.choices[0].message.content)
        category = parsed.get("category", "unknown")
        if category not in VALID_CATEGORIES:
            category = "unknown"
        reasoning = parsed.get("reasoning", "")
    except Exception as exc:
        category = "unknown"
        reasoning = f"Classifier error: {exc}"

    return {
        "task_id": task["id"],
        "tier": task["tier"],
        "retries": result.get("retries", 0),
        "category": category,
        "reasoning": reasoning,
        "agent_output_snippet": result["_output_full"][:300],
    }


# ---------------------------------------------------------------------------
# Summary printing
# ---------------------------------------------------------------------------

def _tier_stats(results: list[dict], tier: str, sc: bool) -> dict:
    subset = [r for r in results if r["tier"] == tier and r["self_correction"] == sc]
    if not subset:
        return {}
    n = len(subset)
    return {
        "n": n,
        "success_rate": sum(r["success"] for r in subset) / n,
        "avg_retries":  sum(r["retries"] for r in subset) / n,
        "avg_tokens":   sum(r["total_tokens"] for r in subset) / n,
        "avg_time":     sum(r["wall_time_seconds"] for r in subset) / n,
    }


def print_summary(results: list[dict]) -> None:
    tiers = ["easy", "medium", "hard"]
    col = 12
    header = (
        f"{'Tier':<8}"
        f"{'Success%':>{col}}"
        f"{'Avg Retries':>{col}}"
        f"{'Avg Tokens':>{col}}"
        f"{'Avg Time(s)':>{col}}"
    )

    print(f"\n{'=' * 72}")
    print(f"{'EVAL SUMMARY':^72}")
    print(f"{'=' * 72}")

    for sc, label in [(False, "Self-Correction OFF"), (True, "Self-Correction ON")]:
        print(f"\n  {label}")
        print(f"  {header}")
        print(f"  {'-' * (8 + col * 4)}")
        for tier in tiers:
            s = _tier_stats(results, tier, sc)
            if not s:
                continue
            print(
                f"  {tier:<8}"
                f"{s['success_rate'] * 100:>{col}.0f}%"
                f"{s['avg_retries']:>{col}.1f}"
                f"{s['avg_tokens']:>{col}.0f}"
                f"{s['avg_time']:>{col}.1f}s"
            )

    sign = lambda v: f"+{v:.1f}" if v >= 0 else f"{v:.1f}"
    print(f"\n  Overall improvement (SC ON vs OFF)")
    print(f"  {header}")
    print(f"  {'-' * (8 + col * 4)}")
    for tier in tiers:
        off = _tier_stats(results, tier, False)
        on  = _tier_stats(results, tier, True)
        if not off or not on:
            continue
        print(
            f"  {tier:<8}"
            f"{sign((on['success_rate'] - off['success_rate']) * 100) + '%':>{col}}"
            f"{sign(on['avg_retries']  - off['avg_retries']):>{col}}"
            f"{sign(on['avg_tokens']   - off['avg_tokens']):>{col}}"
            f"{sign(on['avg_time']     - off['avg_time']) + 's':>{col}}"
        )
    print()


def print_failure_distribution(analyses: list[dict]) -> None:
    print(f"\n{'=' * 72}")
    print(f"{'FAILURE MODE DISTRIBUTION  (self-correction ON)':^72}")
    print(f"{'=' * 72}")

    if not analyses:
        print("\n  No SC=ON failures to classify.\n")
        return

    total = len(analyses)
    ordered = [
        "hallucinated_critique",
        "confident_wrong_answer",
        "overcorrection",
        "correction_plateau",
        "unknown",
    ]

    print(f"\n  {'Category':<28} {'N':>3}  {'%':>5}  Tasks")
    print(f"  {'-' * 62}")
    for cat in ordered:
        items = [a for a in analyses if a["category"] == cat]
        if not items:
            continue
        pct = len(items) / total * 100
        ids = ", ".join(a["task_id"] for a in items)
        print(f"  {cat:<28} {len(items):>3}  {pct:>4.0f}%  {ids}")

    print(f"\n  Total classified: {total}")
    print(f"\n  {'Reasoning by task':}")
    print(f"  {'-' * 62}")
    for a in analyses:
        print(f"  [{a['task_id']}]  {a['category']}  (retries: {a['retries']})")
        print(f"    {a['reasoning']}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not os.path.exists(TASK_FILE):
        print(f"ERROR: {TASK_FILE} not found. Run from the DevAgent project root.")
        sys.exit(1)

    with open(TASK_FILE, "r", encoding="utf-8") as f:
        tasks: list[dict] = json.load(f)

    results: list[dict] = []
    # Keep (task, full_result) so private fields survive until classification
    task_run_pairs: list[tuple[dict, dict]] = []
    total = len(tasks) * 2
    idx = 0

    for task in tasks:
        for sc in [False, True]:
            idx += 1
            mode = "SC=ON " if sc else "SC=OFF"
            print(
                f"[{idx:>2}/{total}] {mode} | {task['tier']:<6} | {task['id']:<12} ...",
                end=" ",
                flush=True,
            )
            full_result = run_task(task, sc)
            task_run_pairs.append((task, full_result))

            public_result = {k: v for k, v in full_result.items() if not k.startswith("_")}
            results.append(public_result)

            status = "PASS" if full_result["success"] else "FAIL"
            print(
                f"{status}  ({full_result['wall_time_seconds']}s,"
                f" {full_result['total_tokens']} tok,"
                f" {full_result['retries']} retries)"
            )

    with open(RESULTS_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {RESULTS_FILE}")

    # Classify every SC=ON failure
    sc_failures = [
        (task, fr)
        for task, fr in task_run_pairs
        if fr["self_correction"] and not fr["success"]
    ]

    analyses: list[dict] = []
    if sc_failures:
        print(f"\nClassifying {len(sc_failures)} SC=ON failure(s)...")
        for task, fr in sc_failures:
            print(f"  {task['id']} ...", end=" ", flush=True)
            analysis = classify_failure(task, fr)
            analyses.append(analysis)
            print(analysis["category"])

    with open(FAILURE_ANALYSIS_FILE, "w", encoding="utf-8") as f:
        json.dump(analyses, f, indent=2)
    print(f"Failure analysis saved to {FAILURE_ANALYSIS_FILE}")

    print_summary(results)
    print_failure_distribution(analyses)


if __name__ == "__main__":
    main()

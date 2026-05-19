---
title: DevAgent
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 5.23.0
app_file: app.py
pinned: false
---

# DevAgent 🤖

An autonomous AI coding agent that reads files, writes and runs code, and opens pull requests on GitHub — all from a single natural-language chat interface.

Built as the capstone project for the **IIT Jammu Winter School 2025 AI (LLMs, GenAI & Agentic AI) Internship Program**.

## What it does

- **Reads files** from your local filesystem and from any public GitHub repository
- **Writes and runs Python code** in a sandboxed subprocess with timeout and error capture
- **Self-corrects** automatically when code execution fails — reads the traceback and retries up to 3 times
- **Opens pull requests** on GitHub autonomously with proposed code changes
- **Remembers the conversation** across turns for multi-step dialogues

## Tech Stack

- **Python 3.11**
- **OpenAI API** (gpt-4o-mini) — native function calling
- **PyGithub** — GitHub REST API
- **Gradio 5.23** — web-based chat interface
- **uv** — fast dependency management

## How to run

1. Clone the repo
```bash
   git clone https://github.com/ibo-agentic/DevAgent.git
   cd DevAgent
```

2. Install dependencies with uv
```bash
   uv sync
```

3. Add your API keys to a `.env` file
```
   OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
   GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxx
```

4. Run the agent
```bash
   uv run app.py        # web UI at http://127.0.0.1:7860
   # or
   uv run agent.py      # CLI
```

## Example interactions

```
You:        "what files are in my project?"
DevAgent:   [calls list_files tool]
DevAgent:   "Your project contains: agent.py, tools.py, code_tools.py..."

You:        "write a function that adds two numbers and run it for 3+5"
DevAgent:   [writes code, saves to file, runs it in subprocess]
DevAgent:   "Done. Output: 8"

You:        "read the README of ibo-agentic/DevAgent and summarize it"
DevAgent:   [calls read_github_file]
DevAgent:   "The README describes an autonomous AI coding agent that..."

You:        "open a PR to improve the README in my repo"
DevAgent:   [reads repo → drafts improvements → creates branch → opens PR]
DevAgent:   "PR created: https://github.com/ibo-agentic/DevAgent/pull/4"
```

## Evaluation

DevAgent was evaluated on a fixed benchmark of **30 coding tasks** across 3 difficulty tiers (easy, medium, hard). Each task was run **twice** — once with self-correction OFF, once with self-correction ON — for a total of 60 runs.

### Results

| Tier | Self-Correction OFF | Self-Correction ON | Avg. Tokens (SC ON) |
|------|--------------------:|-------------------:|--------------------:|
| Easy | 100% (5/5) | 100% (5/5) | 2,141 |
| Medium | 40% (2/5) | 40% (2/5) | 2,666 |
| Hard | 100% (5/5) | 100% (5/5) | 43,781 |

### Key finding

**Self-correction did not improve success rate on any tier.** It only increased token cost. The reason: all 3 unresolved failures fell into categories that simple retry-on-error cannot fix:

- **Confident wrong answer (67%)** — code ran successfully but produced wrong output. No error triggered a retry.
- **Overcorrection (33%)** — fixed one bug, introduced another.

This is the central finding of the project. It suggests that the next layer of improvement in coding agents is not "more retries" but rather **self-verification** — the agent needs to check whether its own output is actually correct, not just whether the code ran without crashing.

Full evaluation methodology, failure taxonomy, and analysis are in the project report.

## Project structure

```
DevAgent/
├── agent.py              # Core ReAct loop, OpenAI client, system prompt
├── app.py                # Gradio web UI
├── tools.py              # Tool schema definitions and dispatcher
├── code_tools.py         # read_file, write_file, run_python
├── github_tools.py       # PyGithub integration
├── eval_harness.py       # 30-task evaluation harness
├── tasks.json            # Evaluation task definitions
├── eval_results.json     # Captured evaluation data
├── failure_analysis.json # Classified failures
├── logs/                 # Per-run JSON logs
├── data/                 # Sample files for medium tasks
├── pyproject.toml        # Project config
├── uv.lock               # Dependency lock
└── README.md             # This file
```

## Tools exposed to the LLM

| Tool | Purpose |
|------|---------|
| `list_files` | List files in a local directory |
| `read_file` | Read contents of a local file |
| `write_file` | Write a string to a local file |
| `run_python` | Execute a Python snippet in a subprocess |
| `read_github_file` | Fetch a file from a GitHub repo |
| `list_github_files` | List files in a GitHub repo |
| `open_pull_request` | Create a branch, commit, and open a PR |

## Built by

**Bashanta Bikash Chakma** — [@ibo-agentic](https://github.com/ibo-agentic)

B.Tech CSE, Guru Nanak Dev University, Amritsar
IIT Jammu Winter School 2025 — AI (LLMs, GenAI & Agentic AI) Internship Program
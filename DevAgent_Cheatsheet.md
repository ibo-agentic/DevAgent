# DevAgent — Complete Cheatsheet 🤖
## Everything we learned — Python, Git, OpenAI, Agents, Evaluation

---

## 1. Python Basics (Quick Recall)

### Variables & Types
```python
name = "Ibo"           # string (text)
age = 20               # integer (number)
price = 9.99           # float (decimal)
is_ready = True        # boolean (true/false)
```

### Functions
```python
# Define a function
def add(a, b):
    return a + b

# Call a function
result = add(3, 5)     # result = 8
```

### Lists
```python
files = ["main.py", "tools.py", "agent.py"]
files.append("new.py")     # add to list
files[0]                   # get first item → "main.py"
```

### Dictionaries
```python
message = {
    "role": "user",
    "content": "hello"
}
message["role"]            # → "user"
```

### If / Else
```python
if user_input == "exit":
    print("Goodbye!")
else:
    print("Continuing...")
```

### While Loop
```python
while True:
    user_input = input("You: ")
    if user_input == "exit":
        break              # stops the loop
```

### Try / Except (Error Handling)
```python
try:
    with open("file.txt", "r") as f:
        return f.read()
except Exception as e:
    return f"Error: {e}"   # handles error gracefully
```

### Imports
```python
import os                          # whole library
from openai import OpenAI          # specific class from library
from dotenv import load_dotenv     # specific function
```

---

## 2. Python File Operations

### Read a file
```python
with open("main.py", "r") as f:
    content = f.read()
```

### Write a file
```python
with open("output.py", "w") as f:
    f.write("print('hello')")
```

### List files in folder
```python
import os
files = os.listdir(".")    # "." means current folder
```

### Run a Python file from code (safe subprocess)
```python
import subprocess
result = subprocess.run(
    ["python", "add.py"],
    capture_output=True,
    text=True,
    timeout=30                  # prevents runaway code
)
print(result.stdout)            # what the file printed
print(result.stderr)            # any errors
print(result.returncode)        # 0 = success, anything else = failed
```

---

## 3. Environment Variables (.env)

### Why .env?
Never hardcode API keys in code. Put them in `.env` file.

### .env file
```
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxx
```

### Read in Python
```python
from dotenv import load_dotenv
import os

load_dotenv()                              # loads .env file
key = os.getenv("OPENAI_API_KEY")          # reads the value
```

### .gitignore — keep .env safe!
Always add `.env` to `.gitignore` so it never goes to GitHub:
```
.env
.venv
__pycache__
logs/
```

---

## 4. UV Package Manager

### Why UV?
Faster than pip. Modern way to manage Python projects. Produces a reproducible lockfile.

### Common commands
```bash
uv init                    # create new project
uv venv                    # create virtual environment
.venv\Scripts\activate     # activate environment (Windows)
uv add openai              # install a library
uv add gradio              # install gradio
uv run main.py             # run a Python file
uv sync                    # install all packages from pyproject.toml
```

---

## 5. LLM API — OpenAI

### Basic call
```python
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Python?"}
    ]
)

reply = response.choices[0].message.content
print(reply)
```

### Why we picked OpenAI
- Mature, well-documented function calling
- Reliable structured outputs
- Stable API surface
- Strong on coding tasks
- `gpt-4o-mini` is cheap enough for full evaluation runs

### Message roles
| Role | What it does |
|------|-------------|
| `system` | Instructions for the AI |
| `user` | What the user said |
| `assistant` | What the AI replied |
| `tool` | Result from a tool call |

### Conversation memory
```python
conversation_history = [
    {"role": "system", "content": "You are DevAgent."}
]

def chat(user_message):
    conversation_history.append({"role": "user", "content": user_message})
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation_history
    )
    
    ai_reply = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": ai_reply})
    return ai_reply
```

---

## 6. Tool Use (Function Calling)

### What is tool use?
LLM decides WHEN to use a tool and WHICH tool to use.

### Define tools
```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the file"
                    }
                },
                "required": ["filepath"]
            }
        }
    }
]
```

### Call API with tools
```python
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=messages,
    tools=tools,
    tool_choice="auto"     # LLM decides when to use tools
)
```

### Handle tool calls
```python
message = response.choices[0].message

if message.tool_calls:
    for tool_call in message.tool_calls:
        tool_name = tool_call.function.name
        tool_input = json.loads(tool_call.function.arguments)
        tool_result = run_tool(tool_name, tool_input)
        
        messages.append(message)
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": str(tool_result)
        })
```

---

## 7. The ReAct Agent Loop

### What is ReAct?
ReAct = **Reason + Act**. The agent reasons about what to do, takes an action with a tool, observes the result, and reasons again.

### The loop in plain English
```
1. User provides instruction
2. Add user message to conversation history
3. Call LLM with history + tool schemas
4. If LLM returns a tool call:
   → Execute the tool
   → Add tool result to conversation
   → Go back to step 3
5. If LLM returns plain text:
   → Show it to user
   → Wait for next instruction
```

### Why this loop works
The model is not "running" code — it is *requesting* code be run. The application code does the actual execution. This separation is what makes the agent safe and inspectable.

---

## 8. Self-Correction Loop

### What is self-correction?
When the agent's code fails, the agent reads the error, figures out what went wrong, and tries again.

### How it's implemented
Self-correction is NOT a separate critic model. It is just the same model, with the right system prompt, looking at its own tool result.

### System prompt clause
```
When you call run_python and the tool result contains a non-zero exit code 
or a traceback, do not give up. Read the error carefully, diagnose the 
cause, and call run_python again with corrected code. You have up to 3 
attempts. After 3 failed attempts, summarize what went wrong and stop.
```

### Retry cap
```python
MAX_RETRIES = 3      # stops infinite loops
```

### Key insight
Self-correction only fixes **loud errors** (syntax errors, runtime exceptions). It cannot fix:
- Confident wrong answers (code runs but output is wrong)
- Correction plateaus (same error repeats)
- Overcorrection (fixes one bug, breaks another)

---

## 9. GitHub Integration (PyGithub)

### Connect to GitHub
```python
from github import Github
import os

g = Github(os.getenv("GITHUB_TOKEN"))
```

### Read repo structure
```python
def get_repo_structure(repo_name):
    repo = g.get_repo(repo_name)        # e.g. "ibo-agentic/DevAgent"
    contents = repo.get_contents("")
    files = []
    
    while contents:
        file = contents.pop(0)
        if file.type == "dir":
            contents.extend(repo.get_contents(file.path))
        else:
            files.append(file.path)
    
    return "\n".join(files)
```

### Read file content
```python
def get_file_content(repo_name, file_path):
    repo = g.get_repo(repo_name)
    file = repo.get_contents(file_path)
    return file.decoded_content.decode("utf-8")
```

### Create a Pull Request
```python
def create_pull_request(repo_name, title, body, filename, content, branch_name):
    repo = g.get_repo(repo_name)
    main_branch = repo.get_branch("main")
    
    # Create new branch
    repo.create_git_ref(
        ref=f"refs/heads/{branch_name}",
        sha=main_branch.commit.sha
    )
    
    # Update file on new branch
    file = repo.get_contents(filename)
    repo.update_file(
        path=filename,
        message=f"DevAgent: {title}",
        content=content,
        sha=file.sha,
        branch=branch_name
    )
    
    # Open PR
    pr = repo.create_pull(
        title=title,
        body=body,
        head=branch_name,
        base="main"
    )
    return f"PR created: {pr.html_url}"
```

### Rate limits
- Unauthenticated: 60 requests/hour (will hit limit fast)
- Authenticated with token: 5000 requests/hour
- **Always use a token** for any real testing

---

## 10. Evaluation Harness

### Why evaluate?
A demo is not a system. A system needs measured success rates, not vibes.

### Task structure
```json
{
  "id": "medium_01",
  "tier": "medium",
  "prompt": "Read data/sample.csv, compute total revenue, write to out.json",
  "expected_outcome": "Output JSON contains revenue = 1332.0"
}
```

### Three difficulty tiers
| Tier | Description | Example |
|------|-------------|---------|
| Easy | Single function, no dependencies | "Write Fibonacci function and run for n=10" |
| Medium | File I/O, multi-step | "Read CSV, compute sum, write to JSON" |
| Hard | GitHub operations | "Read repo README and summarize" |

### Run each task twice
- Once with self-correction **OFF** (single attempt)
- Once with self-correction **ON** (up to 3 attempts)
- Total = 60 runs for 30 tasks

### What to measure
```python
{
    "task_id": "medium_01",
    "sc_enabled": True,
    "success": False,
    "retries": 2,
    "tokens_used": 4520,
    "wall_clock_seconds": 12.38,
    "final_output": "..."
}
```

---

## 11. Failure Mode Taxonomy

### Four failure classes
| Class | Description | Self-correction can fix? |
|-------|-------------|--------------------------|
| **Hallucinated critique** | Agent claims a problem where none exists, invents fake APIs | ❌ No |
| **Confident wrong answer** | Code runs successfully but output is incorrect | ❌ No |
| **Overcorrection** | Fixes one bug, introduces another | ❌ No |
| **Correction plateau** | Same error repeats every retry | ❌ No |

### Classifying failures with a second LLM call
```python
classification_prompt = f"""
Classify this agent failure into one category:
- hallucinated_critique
- confident_wrong_answer  
- overcorrection
- correction_plateau

Task: {task_prompt}
Expected: {expected_outcome}
Agent output: {agent_output}
Retry log: {retry_log}

Return JSON: {{"category": "...", "reasoning": "..."}}
"""
```

### Real DevAgent findings
On 30 tasks, with self-correction ON:
- Easy: 100% success (no failures)
- Medium: 40% success (3 failures)
- Hard: 100% success
- **Self-correction did NOT improve any tier's success rate**
- Failures: 67% confident wrong answer, 33% overcorrection
- Token cost on hard tier doubled (20,679 → 43,781)

---

## 12. Gradio (Web UI)

### Basic chat interface
```python
import gradio as gr

def chat(message, history):
    reply = agent(message)
    return reply

demo = gr.ChatInterface(
    fn=chat,
    title="DevAgent 🤖",
    description="Your AI coding agent",
)

demo.launch()
```

### Run locally
```bash
uv run app.py
# Opens at http://127.0.0.1:7860
```

---

## 13. Git — Version Control

### What is Git?
Git saves your code history. Like "undo" for your entire project.

### The 3 commands you use every time
```bash
git add .                           # select all changed files
git commit -m "what you changed"   # save the changes
git push origin main                # upload to GitHub
```

### First time setup for a project
```bash
git init                            # start git in project folder
git add .                           # add all files
git commit -m "Initial commit"     # first save
git branch -M main                  # name the branch "main"
git remote add origin https://github.com/USERNAME/REPO.git
git push -u origin main             # push to GitHub
```

### Common git commands
```bash
git status                          # see what changed
git log                             # see history of commits
git pull origin main                # download latest from GitHub
git push origin main                # upload to GitHub
```

### Fix merge conflict
```bash
git checkout --ours README.md       # keep your version
git add README.md
git commit -m "Resolve conflict"
git push
```

---

## 14. Project File Structure

```
DevAgent/
│
├── agent.py              ← Core ReAct loop, OpenAI client, system prompt
├── app.py                ← Gradio web UI
├── tools.py              ← Tool schema definitions and dispatcher
├── code_tools.py         ← read_file, write_file, run_python (with subprocess)
├── github_tools.py       ← PyGithub: read repos, create PRs
├── eval_harness.py       ← Runs 30 tasks twice, classifies failures
├── tasks.json            ← The 30 evaluation tasks
├── eval_results.json     ← Saved evaluation data
├── failure_analysis.json ← Classified failures with reasoning
├── logs/                 ← Per-run JSON logs
├── data/                 ← Sample CSVs/JSONs for medium tasks
│
├── .env                  ← API keys (NEVER push to GitHub!)
├── .gitignore            ← tells git what to ignore
├── requirements.txt      ← pip-compatible fallback
├── pyproject.toml        ← UV project config
├── uv.lock               ← Deterministic dependency lock
└── README.md             ← Project description
```

---

## 15. DevAgent Build Phases

| Phase | What we built | Key file |
|-------|---------------|----------|
| 1 | Basic OpenAI call | agent.py (early) |
| 2 | Conversation memory | agent.py |
| 3 | Local file tools | tools.py, code_tools.py |
| 4 | ReAct loop with tool dispatch | agent.py |
| 5 | GitHub reading | github_tools.py |
| 6 | Pull request creation | github_tools.py |
| 7 | Code execution with subprocess | code_tools.py |
| 8 | **Self-correction loop** | agent.py (system prompt + retry) |
| 9 | **Evaluation harness** | eval_harness.py |
| 10 | **Failure mode classifier** | eval_harness.py |
| 11 | Gradio web UI | app.py |

---

## 16. Full Agent Loop (Visual)

```
User types message
        ↓
LLM reads message + tool definitions
        ↓
Does LLM want to use a tool?
    YES → run the tool → send result back to LLM
                                  ↓
                          If run_python failed:
                              retries < 3?
                                  YES → try again with fix
                                  NO  → give up, summarize
                                  ↓
                          LLM gives final answer
    NO  → LLM just answers directly
        ↓
Print reply to user
        ↓
Loop back to start
```

---

## 17. Common Errors & Fixes

| Error | What it means | Fix |
|-------|--------------|-----|
| `ModuleNotFoundError` | Library not installed | `uv add library_name` |
| `SyntaxError` | Code has a typo | Check indentation and syntax |
| `IndentationError` | Wrong spaces/tabs | Use consistent 4 spaces |
| `KeyError` | Dictionary key doesn't exist | Check spelling of key |
| `OPENAI_API_KEY not found` | .env not loaded | Add `load_dotenv()` at top |
| `403: rate limit exceeded` | GitHub unauthenticated limit | Add `GITHUB_TOKEN` to .env |
| `rejected (fetch first)` | Git conflict | `git pull` then push |
| Subprocess timeout | Code takes too long | Increase timeout or fix logic |

---

## 18. Important Concepts

### What is an LLM?
Large Language Model — an AI trained on text that can understand and generate human language. Examples: GPT-4, Claude, LLaMA.

### What is an Agent?
An LLM + Tools + a Loop. The LLM can take actions, not just talk.

### What is ReAct?
A pattern where the agent alternates between **Reasoning** (thinking about what to do) and **Acting** (using a tool). The reasoning happens inside the LLM call; the acting happens when the application code executes a requested tool.

### What is Function Calling?
A feature of modern LLM APIs where you give the model a list of available tools (with names, descriptions, and JSON schemas). The model can choose to return a structured tool request instead of plain text.

### What is Self-Correction?
A loop where, when an action fails, the same model reads the error and tries again. It is not a separate AI — it is the same model, seeing more context.

### What is RAG?
Retrieval Augmented Generation — feeding external data (like files) to the LLM so it can answer questions about it.

### What is a Virtual Environment?
An isolated Python installation for each project. Keeps libraries separate so they don't conflict.

### What is an API?
Application Programming Interface — a way for programs to talk to each other. We use OpenAI's API to talk to GPT-4o-mini.

---

## 19. What I Learned (Reflection)

**Building an agent is easy. Building one that fails honestly is hard.**

The hardest part of this project was not building DevAgent — it was admitting that self-correction did not help. The evaluation showed that adding retries did not improve success rate on any tier. It only increased token cost.

This was the most valuable finding. It teaches that:
- Demos lie. Evaluations don't.
- Loud errors are easy to fix. Silent wrong answers are not.
- Adding more retries is not enough. The agent needs to *verify* its own output.

The next step for this project would be to add a **self-verification layer** — a step where the agent compares its output against an expected outcome or runs a unit test on its own code. That is a much harder problem and is the basis for the research direction this work seeds.

---

*Built by Ibo — @ibo-agentic*
*DevAgent project — IIT Jammu Winter School 2025*
*Updated for the final report submission, May 2026*
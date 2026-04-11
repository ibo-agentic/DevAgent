# DevAgent — Complete Cheatsheet 🤖
## Everything we learned — Python, Git, Hugging Face, LLMs

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
from groq import Groq              # specific class from library
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

### Run a Python file from code
```python
import subprocess
result = subprocess.run(
    ["python", "add.py"],
    capture_output=True,
    text=True,
    timeout=10
)
print(result.stdout)       # what the file printed
print(result.stderr)       # any errors
```

---

## 3. Environment Variables (.env)

### Why .env?
Never hardcode API keys in code. Put them in `.env` file.

### .env file
```
GROQ_API_KEY=gsk_xxxxxxxxxxxx
GITHUB_TOKEN=ghp_xxxxxxxxxxxx
```

### Read in Python
```python
from dotenv import load_dotenv
import os

load_dotenv()                              # loads .env file
key = os.getenv("GROQ_API_KEY")           # reads the value
```

### .gitignore — keep .env safe!
Always add `.env` to `.gitignore` so it never goes to GitHub:
```
.env
.venv
__pycache__
```

---

## 4. UV Package Manager

### Why UV?
Faster than pip. Modern way to manage Python projects.

### Common commands
```bash
uv init                    # create new project
uv venv                    # create virtual environment
.venv\Scripts\activate     # activate environment (Windows)
uv add groq                # install a library
uv add gradio              # install gradio
uv run main.py             # run a Python file
uv sync                    # install all packages from pyproject.toml
```

---

## 5. LLM API — Groq

### Basic call
```python
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Python?"}
    ]
)

reply = response.choices[0].message.content
print(reply)
```

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
        model="llama-3.3-70b-versatile",
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
    model="llama-3.3-70b-versatile",
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

## 7. GitHub Integration (PyGithub)

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

---

## 8. Gradio (Web UI)

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

## 9. Git — Version Control

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

### Two remotes (GitHub + Hugging Face)
```bash
# Push to GitHub (portfolio)
git push origin main

# Push to Hugging Face (live app)
git push huggingface main
```

### Fix merge conflict
```bash
git checkout --ours README.md       # keep your version
git add README.md
git commit -m "Resolve conflict"
git push
```

---

## 10. Hugging Face Spaces (Deployment)

### What is it?
Free cloud hosting for AI apps. Anyone can use your app from a browser.

### README.md metadata (required!)
```
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
```

### requirements.txt (what to install)
```
groq
gradio==5.23.0
python-dotenv
PyGithub
audioop-lts
```

### Secrets (API keys on Hugging Face)
Go to Space Settings → Variables and secrets → Add secret
- Name: `GROQ_API_KEY`  Value: your key
- Name: `GITHUB_TOKEN`  Value: your token

### Deploy steps
```bash
# 1. Add Hugging Face remote
git remote add huggingface https://huggingface.co/spaces/USERNAME/SPACENAME

# 2. Push code
git push huggingface main

# 3. If rejected, pull first
git pull huggingface main --allow-unrelated-histories
git push huggingface main
```

### Your live app
```
https://huggingface.co/spaces/ibohanma/DevAgent
```

---

## 11. Project File Structure

```
DevAgent/
│
├── main.py           ← Phase 1: Basic LLM call
├── llm_test.py       ← Phase 2: Conversation memory
├── tools.py          ← Phase 3: Local file tools
│                          read_file(), list_files()
├── agent.py          ← Phase 4: Full agent with all tools
├── github_tools.py   ← Phase 5-6: GitHub integration
│                          get_repo_structure(), get_file_content()
│                          create_pull_request()
├── code_tools.py     ← Phase 7: Write and run code
│                          write_file(), run_code()
├── app.py            ← Web UI (Gradio)
│
├── .env              ← API keys (NEVER push to GitHub!)
├── .gitignore        ← tells git what to ignore
├── requirements.txt  ← libraries for Hugging Face
├── pyproject.toml    ← UV project config
└── README.md         ← project description
```

---

## 12. Full Agent Loop (How it works)

```
User types message
        ↓
LLM reads message + tool definitions
        ↓
Does LLM want to use a tool?
    YES → run the tool → send result back to LLM → LLM gives final answer
    NO  → LLM just answers directly
        ↓
Print reply to user
        ↓
Loop back to start
```

---

## 13. DevAgent Phases Summary

| Phase | File | What it does |
|-------|------|-------------|
| 1 | main.py | Basic LLM call |
| 2 | llm_test.py | Conversation memory |
| 3 | tools.py | Read files, list folders |
| 4 | agent.py | Agent loop with tools |
| 5-6 | github_tools.py | Read GitHub repos |
| 7 | code_tools.py | Write & run code |
| 8 | agent.py + github_tools.py | Open Pull Requests |
| Deploy | app.py | Gradio web UI on Hugging Face |

---

## 14. Common Errors & Fixes

| Error | What it means | Fix |
|-------|--------------|-----|
| `ModuleNotFoundError` | Library not installed | `uv add library_name` |
| `SyntaxError` | Code has a typo | Check indentation and syntax |
| `IndentationError` | Wrong spaces/tabs | Use consistent 4 spaces |
| `KeyError` | Dictionary key doesn't exist | Check spelling of key |
| `API key not found` | .env not loaded | Add `load_dotenv()` at top |
| `tool_use_failed` | Groq model failed | Add `tool_choice="auto"` |
| `rejected (fetch first)` | Git conflict | `git pull` then push |

---

## 15. Important Concepts

### What is an LLM?
Large Language Model — an AI trained on text that can understand and generate human language. Examples: GPT-4, Claude, LLaMA.

### What is an Agent?
An LLM + Tools + a Loop. The LLM can take actions, not just talk.

### What is RAG?
Retrieval Augmented Generation — feeding external data (like files) to the LLM so it can answer questions about it.

### What is a Virtual Environment?
An isolated Python installation for each project. Keeps libraries separate so they don't conflict.

### What is an API?
Application Programming Interface — a way for programs to talk to each other. We use Groq's API to talk to LLaMA.

---

*Built by Ibo — @ibo-agentic*
*DevAgent project — April 2026*

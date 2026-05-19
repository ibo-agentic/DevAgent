import os
import json
import uuid
import datetime
import base64
from openai import OpenAI
from dotenv import load_dotenv
from tools import read_file, list_files
from github_tools import get_repo_structure, get_file_content, create_pull_request
from code_tools import write_file, run_code

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MAX_RETRIES = 3
MAX_TURNS = 10
LOGS_DIR = "logs"

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
                        "description": "The path to the file"
                    }
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List all files in a folder. Use '.' for current folder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder_path": {
                        "type": "string",
                        "description": "The folder path to list"
                    }
                },
                "required": ["folder_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_repo_structure",
            "description": "List all files in a GitHub repository",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "GitHub repo in format 'username/reponame'"
                    }
                },
                "required": ["repo_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_file_content",
            "description": "Read a specific file from a GitHub repository",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "GitHub repo in format 'username/reponame'"
                    },
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file inside the repo"
                    }
                },
                "required": ["repo_name", "file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write code to a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Name of the file to create"
                    },
                    "content": {
                        "type": "string",
                        "description": "The code content to write"
                    }
                },
                "required": ["filepath", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_code",
            "description": "Run a Python file and return the output",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Path to the Python file to run"
                    }
                },
                "required": ["filepath"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_pull_request",
            "description": "Create a pull request on GitHub with file changes",
            "parameters": {
                "type": "object",
                "properties": {
                    "repo_name": {"type": "string", "description": "GitHub repo username/reponame"},
                    "title": {"type": "string", "description": "PR title"},
                    "body": {"type": "string", "description": "PR description"},
                    "filename": {"type": "string", "description": "File to change"},
                    "content": {"type": "string", "description": "New file content"},
                    "branch_name": {"type": "string", "description": "New branch name"}
                },
                "required": ["repo_name", "title", "body", "filename", "content", "branch_name"]
            }
        }
    }
]

def run_tool(tool_name, tool_input):
    if tool_name == "read_file":
        return read_file(tool_input["filepath"])
    elif tool_name == "list_files":
        return list_files(tool_input["folder_path"])
    elif tool_name == "get_repo_structure":
        return get_repo_structure(tool_input["repo_name"])
    elif tool_name == "get_file_content":
        return get_file_content(tool_input["repo_name"], tool_input["file_path"])
    elif tool_name == "write_file":
        return write_file(tool_input["filepath"], tool_input["content"])
    elif tool_name == "run_code":
        raw = run_code(tool_input["filepath"])
        if raw["success"]:
            return f"Output:\n{raw['stdout']}"
        return f"Error (exit code {raw['returncode']}):\n{raw['stderr']}"
    elif tool_name == "create_pull_request":
        return create_pull_request(
            tool_input["repo_name"],
            tool_input["title"],
            tool_input["body"],
            tool_input["filename"],
            tool_input["content"],
            tool_input["branch_name"],
        )
    else:
        return f"Unknown tool: {tool_name}"

_SYSTEM_MESSAGE = {"role": "system", "content": """You are DevAgent, a helpful coding assistant. Use tools when needed.

For local files: use list_files with '.' when user says 'my files' or 'list files'.
For GitHub files: use get_file_content with repo_name and file_path.
For GitHub repo listing: use get_repo_structure with repo_name.

If user gives you a filename and asks to create it, just create it immediately. Do not ask for confirmation.
If user gives NO filename, then ask once for the name only.
If repo name is missing for GitHub actions, ask once for it only.
Remember the last mentioned repo and reuse it automatically.
Do not ask multiple questions. Just do the task.

When the user uploads an image, analyze it carefully and describe what you see.
If it contains code, extract and explain it.
If it contains a diagram or UI, describe it in detail.

When the user uploads a PDF, read and analyze its contents thoroughly.
Summarize, answer questions, or extract information as requested.

When run_code returns a non-zero exit code or a traceback in stderr:
- Read the error message carefully and identify the root cause.
- Fix the bug by rewriting the file with write_file.
- Run it again with run_code.
- You have up to 3 run_code attempts per task. After 3 failures, stop retrying and explain clearly what went wrong and why the code could not be fixed.
"""}

messages = [_SYSTEM_MESSAGE]

def reset_agent():
    """Reset conversation history to system prompt only. Call before each eval task."""
    global messages
    messages = [_SYSTEM_MESSAGE]

def get_trimmed_messages():
    if len(messages) <= 11:
        return messages
    return [messages[0]] + messages[-10:]

def sanitize_messages(msgs):
    """Ensure all message content is a string or None."""
    sanitized = []
    for msg in msgs:
        m = dict(msg)
        if isinstance(m.get("content"), list):
            texts = [
                block.get("text", "")
                for block in m["content"]
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            m["content"] = " ".join(texts) if texts else None
        sanitized.append(m)
    return sanitized

def _log_run_attempt(task_id, attempt_number, filepath, stderr, success):
    os.makedirs(LOGS_DIR, exist_ok=True)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()
    except Exception:
        code = f"<could not read {filepath}>"

    entry = {
        "task_id": task_id,
        "attempt_number": attempt_number,
        "code_run": code,
        "stderr": stderr,
        "success": success,
        "timestamp": datetime.datetime.now().isoformat(),
    }

    log_path = os.path.join(LOGS_DIR, f"{task_id}.json")
    existing = []
    if os.path.exists(log_path):
        try:
            with open(log_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except Exception:
            pass
    existing.append(entry)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)

def _add_tokens(_stats, response):
    if _stats is not None and response.usage:
        _stats["total_tokens"] = _stats.get("total_tokens", 0) + response.usage.total_tokens

def agent(user_message, image_path=None, file_path=None, file_type=None,
          self_correction=True, _stats=None):
    task_id = uuid.uuid4().hex[:8]
    run_code_retries = 0
    if _stats is not None:
        _stats["task_id"] = task_id

    # Handle PDF upload
    if file_path and file_type == "pdf":
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join(page.extract_text() or "" for page in pdf.pages)
            user_message = f"{user_message or 'Summarize this PDF.'}\n\nPDF Content:\n{text}"
        except ImportError:
            return "pdfplumber is not installed. Run: uv add pdfplumber"
        except Exception as e:
            return f"Failed to read PDF: {e}"

    # Handle image upload
    actual_image = image_path or (file_path if file_type != "pdf" else None)

    if actual_image:
        ext = actual_image.lower().split(".")[-1]
        mime_map = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp",
        }
        mime_type = mime_map.get(ext, "image/jpeg")

        with open(actual_image, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        content = [
            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{image_data}"}},
            {"type": "text", "text": user_message or "What do you see in this image?"},
        ]
        messages.append({"role": "user", "content": content})
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=sanitize_messages(get_trimmed_messages()),
        )
        _add_tokens(_stats, response)
        reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        return reply

    # Normal text message — multi-turn agentic loop
    messages.append({"role": "user", "content": user_message})

    for _ in range(MAX_TURNS):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=sanitize_messages(get_trimmed_messages()),
            tools=tools,
        )
        _add_tokens(_stats, response)
        message = response.choices[0].message

        if not message.tool_calls:
            reply = message.content or ""
            messages.append({"role": "assistant", "content": reply})
            return reply

        messages.append({
            "role": "assistant",
            "content": message.content or None,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in message.tool_calls
            ],
        })

        retry_cap_hit = False

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_input = json.loads(tool_call.function.arguments)

            if tool_name == "run_code":
                raw = run_code(tool_input["filepath"])
                success = raw["success"]

                _log_run_attempt(
                    task_id=task_id,
                    attempt_number=run_code_retries + 1,
                    filepath=tool_input["filepath"],
                    stderr=raw["stderr"],
                    success=success,
                )

                if not success:
                    run_code_retries += 1
                    if not self_correction or run_code_retries >= MAX_RETRIES:
                        retry_cap_hit = True

                if _stats is not None:
                    _stats["retries"] = run_code_retries

                if success:
                    tool_result = f"Output:\n{raw['stdout']}"
                else:
                    tool_result = f"Error (exit code {raw['returncode']}):\n{raw['stderr']}"
            else:
                tool_result = str(run_tool(tool_name, tool_input))

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": tool_result,
            })

        if retry_cap_hit:
            messages.append({
                "role": "user",
                "content": (
                    f"You have reached the maximum of {MAX_RETRIES} run_code retries. "
                    "Stop retrying. Summarize what went wrong and why the code could not run successfully."
                ),
            })
            cap_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=sanitize_messages(get_trimmed_messages()),
            )
            _add_tokens(_stats, cap_response)
            summary = cap_response.choices[0].message.content or ""
            messages.append({"role": "assistant", "content": summary})
            return summary

    return "Agent reached the maximum number of turns without completing the task."


if __name__ == "__main__":
    print("DevAgent is ready! Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        reply = agent(user_input)
        print(f"DevAgent: {reply}\n")

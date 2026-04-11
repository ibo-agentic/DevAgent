import os
import json
import base64
from groq import Groq
from dotenv import load_dotenv
from tools import read_file, list_files
from github_tools import get_repo_structure, get_file_content, create_pull_request
from code_tools import write_file, run_code

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

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
        return run_code(tool_input["filepath"])
    elif tool_name == "create_pull_request":
        return create_pull_request(
            tool_input["repo_name"],
            tool_input["title"],
            tool_input["body"],
            tool_input["filename"],
            tool_input["content"],
            tool_input["branch_name"]
        )
    else:
        return f"Unknown tool: {tool_name}"

messages = [
    {"role": "system", "content": """You are DevAgent, a helpful coding assistant. Use tools when needed.

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
"""}
]

def get_trimmed_messages():
    # Always keep system prompt + last 10 messages
    if len(messages) <= 11:
        return messages
    return [messages[0]] + messages[-10:]

def sanitize_messages(msgs):
    """Ensure all message content is a string or None — Groq requires this."""
    sanitized = []
    for msg in msgs:
        m = dict(msg)
        if isinstance(m.get("content"), list):
            # Extract text from content list if possible
            texts = [
                block.get("text", "")
                for block in m["content"]
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            m["content"] = " ".join(texts) if texts else None
        sanitized.append(m)
    return sanitized

def agent(user_message, image_path=None, file_path=None, file_type=None):

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
            "webp": "image/webp"
        }
        mime_type = mime_map.get(ext, "image/jpeg")

        with open(actual_image, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")

        content = [
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{image_data}"}
            },
            {
                "type": "text",
                "text": user_message or "What do you see in this image?"
            }
        ]
        messages.append({"role": "user", "content": content})
        response = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=sanitize_messages(get_trimmed_messages()),
        )
        reply = response.choices[0].message.content
        messages.append({"role": "assistant", "content": reply})
        return reply

    # Normal text message
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=sanitize_messages(get_trimmed_messages()),
        tools=tools
    )

    message = response.choices[0].message

    if message.tool_calls:
        # ✅ FIX: append assistant message as a plain dict with string content
        messages.append({
            "role": "assistant",
            "content": message.content or None,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in message.tool_calls
            ]
        })

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name
            tool_input = json.loads(tool_call.function.arguments)
            tool_result = run_tool(tool_name, tool_input)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(tool_result)
            })

        final_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=sanitize_messages(get_trimmed_messages()),
            tools=tools
        )

        final_message = final_response.choices[0].message
        messages.append({"role": "assistant", "content": final_message.content or ""})

        if final_message.content:
            return final_message.content
        else:
            return str(tool_result)

    messages.append({"role": "assistant", "content": message.content or ""})
    return message.content


if __name__ == "__main__":
    print("DevAgent is ready! Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ")

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        reply = agent(user_input)
        print(f"DevAgent: {reply}\n")
import os
import json
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

def agent(user_message):
    messages = [
        {"role": "system", "content": "You are DevAgent, a helpful coding assistant. Use tools when needed."},
        {"role": "user", "content": user_message}
    ]

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        tools=tools
    )

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

        final_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=tools
        )

        final_message = final_response.choices[0].message

        if final_message.content:
            return final_message.content
        else:
            return tool_result

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
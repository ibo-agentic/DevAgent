---
title: DevAgent
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 4.19.2
app_file: app.py
pinned: false
---



# DevAgent 🤖

An autonomous AI coding agent that can read, write, and push code to GitHub.

## What it does
- Reads files from your computer and GitHub repos
- Writes and runs Python code automatically
- Opens Pull Requests on GitHub autonomously
- Answers coding questions with conversation memory

## Tech Stack
- Python
- Groq API (LLaMA 3)
- PyGithub
- UV package manager

## How to run
1. Clone the repo
2. Add your API keys to `.env`
3. Run `uv run agent.py`


## Example
You: "what files are in my project?"
DevAgent: *automatically calls list_files tool*
DevAgent: "Your project contains: agent.py, tools.py..."

You: "write a function that adds two numbers and run it"
DevAgent: *writes code, saves to file, runs it*
DevAgent: "Done! Output: 8"

You: "open a PR to improve the README in my repo"
DevAgent: *reads repo, improves file, opens PR*
DevAgent: "PR created! https://github.com/..."

## Built by
Ibo — [@ibo-agentic](https://github.com/ibo-agentic)
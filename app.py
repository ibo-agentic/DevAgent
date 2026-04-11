import gradio as gr
from agent import agent

def chat(message, history):
    try:
        reply = agent(message)
        if reply:
            return reply
        else:
            return "Sorry I had trouble with that. Try asking differently!"
    except Exception as e:
        return f"Error: {str(e)}"

demo = gr.ChatInterface(
    fn=chat,
    title="DevAgent 🤖",
    description="Your autonomous AI coding agent — reads files, writes code, opens Pull Requests on GitHub automatically.",
    examples=[
        "What files are in my project?",
        "What is a Python decorator?",
        "What files are in ibo-agentic/ai-startup-generator repo?",
    ],
    chatbot=gr.Chatbot(
        height=500,
        placeholder="Ask DevAgent anything about code...",
        show_label=False,
    ),
    textbox=gr.Textbox(
        placeholder="Type your message here...",
        container=False,
    ),
)

demo.launch()
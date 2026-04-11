import gradio as gr
from llm_test import chat as agent_chat

def chat(message, history):
    try:
        reply = agent_chat(message)
        if reply:
            return reply
        else:
            return "Sorry I had trouble with that!"
    except Exception as e:
        return f"Error: {str(e)}"

demo = gr.ChatInterface(
    fn=chat,
    title="DevAgent 🤖",
    description="Your autonomous AI coding agent!",
    examples=[
        "What is a Python decorator?",
        "Explain how APIs work",
        "Write a function that reverses a string",
    ],
)

demo.launch()
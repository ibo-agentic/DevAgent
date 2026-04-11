import gradio as gr
from agent import agent

def chat(message, history):
    files = message.get("files", [])
    text = message.get("text", "") or ""

    if files:
        file_path = files[0]
        ext = file_path.lower().split(".")[-1]
        if ext == "pdf":
            reply = agent(text or "Summarize this PDF.", file_path=file_path, file_type="pdf")
        else:
            reply = agent(text or "What do you see in this image?", image_path=file_path)
        display_msg = text or f"📎 {ext.upper()} uploaded"
    else:
        reply = agent(text)
        display_msg = text

    history.append({"role": "user", "content": display_msg})
    history.append({"role": "assistant", "content": reply})
    return history, gr.MultimodalTextbox(value=None)

with gr.Blocks(title="DevAgent 🤖") as demo:

    gr.Markdown("""
# 🤖 DevAgent
**AI-powered coding assistant** — read files, explore GitHub repos, write code, and analyze images.
""")

    chatbot = gr.Chatbot(height=500, show_label=False, type="messages")

    msg = gr.MultimodalTextbox(
        placeholder="Message DevAgent... or attach a file 📎",
        show_label=False,
        file_types=[".jpg", ".jpeg", ".png", ".webp", ".pdf"],
        submit_btn=True,
    )

    clear = gr.ClearButton([msg, chatbot], value="🗑️ Clear")

    gr.Examples(
        examples=["list my files", "what files are in ibo-agentic/ai-startup-generator repo?", "tell me about README.md in ibo-agentic/ai-startup-generator", "create a hello world python file"],
        inputs=msg,
        label="💡 Try these"
    )

    msg.submit(chat, [msg, chatbot], [chatbot, msg])

demo.launch()
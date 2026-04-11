import gradio as gr
from agent import agent

def chat(message, history, uploaded_file):
    if uploaded_file:
        ext = uploaded_file.lower().split(".")[-1]
        if ext == "pdf":
            reply = agent(message or "Summarize this PDF.", file_path=uploaded_file, file_type="pdf")
        else:
            reply = agent(message or "What do you see in this image?", image_path=uploaded_file)
        display_msg = message or f"📎 {ext.upper()} uploaded"
    else:
        reply = agent(message)
        display_msg = message

    history.append({"role": "user", "content": display_msg})
    history.append({"role": "assistant", "content": reply})
    return "", history, None

with gr.Blocks(title="DevAgent 🤖") as demo:

    gr.Markdown("""
# 🤖 DevAgent
**AI-powered coding assistant** — read files, explore GitHub repos, write code, and analyze images.
""")

    chatbot = gr.Chatbot(height=500, show_label=False)

    with gr.Row():
        file_upload = gr.File(
            label="📎 Upload File (jpg, png, webp, pdf...)",
            file_types=[".jpg", ".jpeg", ".png", ".webp", ".pdf"],
            scale=1,
            height=100,
        )

    with gr.Row():
        msg = gr.Textbox(
            placeholder="Message DevAgent... or upload an image above",
            show_label=False,
            scale=5,
            lines=1
        )
        send = gr.Button("Send ↑", variant="primary", scale=1)

    clear = gr.ClearButton([msg, chatbot, file_upload], value="🗑️ Clear")

    gr.Examples(
        examples=[
            "list my files",
            "what files are in ibo-agentic/ai-startup-generator repo?",
            "tell me about README.md in ibo-agentic/ai-startup-generator",
            "create a hello world python file",
        ],
        inputs=msg,
        label="💡 Try these"
    )

    msg.submit(chat, [msg, chatbot, file_upload], [msg, chatbot, file_upload])
    send.click(chat, [msg, chatbot, file_upload], [msg, chatbot, file_upload])

demo.launch()
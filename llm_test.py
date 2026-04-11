import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

#THIS IS OUR CONVERSATIONAL HISTORY

conversation_history = [
    {
        "role": "system",
        "content": "You are a helpful coding assistant called DevAgent."
    }
]

#this function sends the full conversation to LLM everytime
def chat(user_message):
    conversation_history.append({
        "role": "user",
        "content": user_message
    })
    
    #send the entire history to LLM
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages = conversation_history
    )
    
    #ai reply
    ai_reply = response.choices[0].message.content
    
    #add the ai reply history too
    conversation_history.append({
        "role": "assistant",
        "content": ai_reply
    })
    #return the reply
    return ai_reply

if __name__ == "__main__":
    print("DevAgent is ready! Type 'exit' to quit.\n")
    
    while True:
        #get input from the user
        user_input = input("You: ")
        
        #if user types exit, stop the loop
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        #send the llm and print the reply
        
        reply = chat(user_input)
        print(f"DevAgent: {reply}\n")
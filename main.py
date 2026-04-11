# #we are importing the libaries we need
# #os= tool that lets python talk to your system
# we used it for here to read our secret value (API KEY)

import os


#groq = a class, use it to connect to AI
from groq import Groq #this gives you access to Groq AI


#it helps to read .env file
from dotenv import load_dotenv

#load .env file so python can read ur API
load_dotenv()



#this creates a Groq client - opening a connection to the llm
# Get API key
# Give it to Groq
# Store connection in client
client = Groq(api_key=os.getenv("GROQ_API_KEY"))



#this function talks to the LLM
def chat(user_message):
    response = client.chat.completions.create(
        model = "llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful coding assistant."
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
    )
    
    return response.choices[0].message.content



#this runs when we execute the files

if __name__ == "__main__":
    reply = chat("What is a Python function? Explain in 2 lines.")
    print(reply)
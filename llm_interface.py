import streamlit as st
from groq import Groq

def get_groq_client():
    api_key = st.secrets["GROQ_API_KEY"]
    return Groq(api_key=api_key)

def ask_roo(prompt, signals=None):
    client = get_groq_client()

    # Optionally include signals in the prompt
    if signals:
        signal_text = "\n".join(signals)
        prompt = f"{prompt}\n\nRelevant signals:\n{signal_text}"

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are Roo, a helpful assistant who answers clearly and concisely.",
            },
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="mixtral-8x7b-32768"
    )

    return chat_completion.choices[0].message.content

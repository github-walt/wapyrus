import streamlit as st
from groq import Groq

def get_groq_client():
    api_key = st.secrets["GROQ_API_KEY"]
    return Groq(api_key=api_key)

def ask_roo(prompt, signals=None):
    client = get_groq_client()

    # Safely format signals
    if signals and isinstance(signals, list):
        try:
            signal_text = "\n".join(str(s) for s in signals)
            prompt = f"{prompt}\n\nRelevant signals:\n{signal_text}"
        except Exception as e:
            prompt = f"{prompt}\n\n(Note: Signals could not be formatted)"

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are Roo, a helpful assistant who answers clearly and concisely.",
                },
                {
                    "role": "user",
                    "content": str(prompt),
                }
            ],
            model="llama-3.3-70b-versatile"
        )
        return chat_completion.choices[0].message.content

    except Exception as e:
        return f"❌ Error from Groq API: {str(e)}"



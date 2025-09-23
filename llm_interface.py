import streamlit as st
from groq import Groq

def get_groq_client():
    api_key = st.secrets["GROQ_API_KEY"]
    return Groq(api_key=api_key)

def ask_roo(prompt, signals=None, max_signals=50):
    client = get_groq_client()

    # Format signals into readable context
    signal_text = ""
    if signals and isinstance(signals, list):
        trimmed_signals = signals[:max_signals]
        signal_text = "\n".join([
            f"- {s.get('title', 'Unknown')} by {s.get('sponsor', 'Unknown')} ({s.get('status', 'Unknown')})"
            for s in trimmed_signals if s.get("title") and s.get("sponsor")
        ])
        prompt = f"{prompt}\n\nHere are some recent MedTech signals:\n{signal_text}"

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are Roo, a helpful assistant who answers questions using the provided MedTech signal data. Be specific and cite examples from the list when relevant.",
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.1-8b-instant"
        )
        return chat_completion.choices[0].message.content

    except Exception as e:
        return f"❌ Roo hit a limit: {str(e)}"




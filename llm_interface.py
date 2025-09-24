import streamlit as st
from groq import Groq
import os
from dotenv import load_dotenv

def get_groq_client():
    load_dotenv()  # Load from .env file
    api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment or Streamlit secrets")
    return Groq(api_key=api_key)

def ask_roo(prompt, signals=None, max_signals=50):
    try:
        client = get_groq_client()
        
        # Better signal formatting with fallbacks
        signal_text = ""
        if signals and isinstance(signals, list):
            trimmed_signals = signals[:max_signals]
            signal_entries = []
            for s in trimmed_signals:
                title = s.get('title', 'Unknown Study')
                sponsor = s.get('sponsor', 'Unknown Sponsor')
                status = s.get('status', 'Status Unknown')
                signal_entries.append(f"- {title} by {sponsor} ({status})")
            
            signal_text = "\n".join(signal_entries)
            prompt = f"{prompt}\n\nRelevant MedTech trials:\n{signal_text}"

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are Roo, a helpful MedTech analyst. Use the provided clinical trial data to answer questions accurately. Be specific and cite relevant trials when possible.",
                },
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama-3.1-8b-instant",
            timeout=30  # Add timeout
        )
        return chat_completion.choices[0].message.content

    except Exception as e:
        return f"❌ Sorry, I encountered an error: {str(e)}"



